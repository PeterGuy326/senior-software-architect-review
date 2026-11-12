const config = require('../config');
let loginPending;
let cloudReady = false;
function initCloud() {
  if (config.transport !== 'cloud' || cloudReady) return;
  if (!config.cloudEnv || !config.cloudService) throw new Error('尚未配置云环境和服务名称。');
  if (!wx.cloud || !wx.cloud.callContainer) throw new Error('请升级微信后再试。');
  wx.cloud.init({env:config.cloudEnv});
  cloudReady = true;
}
async function request(path, method = 'GET', data = {}, authenticated = true) {
  // A retry after a 401 must first obtain a fresh real WeChat session.
  if (authenticated) await login();
  if (config.transport !== 'cloud' && !config.baseURL) return Promise.reject(new Error('尚未配置开发环境地址，请先部署后端。'));
  return new Promise((resolve, reject) => {
    const options = {method, data, timeout:15000,
      header: { 'content-type': 'application/json',
        ...(authenticated ? {Authorization: 'Bearer ' + (wx.getStorageSync('session') || '')} : {}) },
      success(res) {
        if (res.statusCode === 401) { wx.removeStorageSync('session'); wx.removeStorageSync('goal'); }
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data);
        else {const error=new Error(res.data && typeof res.data.detail === 'string' ? res.data.detail : '暂时无法完成，请重试。');error.statusCode=res.statusCode;reject(error);}
      },
      fail() { reject(new Error('连接暂时中断，你的内容还在，请重试。')); }
    };
    if (config.transport === 'cloud') {
      initCloud();
      // The Mini Program must first be associated with this CloudBase environment.
      // The backend still verifies wx.login codes; client headers are not identities.
      wx.cloud.callContainer({...options, config:{env:config.cloudEnv}, path,
        header:{...options.header,'X-WX-SERVICE':config.cloudService}});
    } else {
      wx.request({...options,url:config.baseURL.replace(/\/$/, '') + path});
    }
  });
}
async function login() {
  if (wx.getStorageSync('session')) return;
  if (loginPending) return loginPending;
  loginPending = (async () => {
    let result;
    if (config.localDebug) {
      if (!/^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/.test(config.baseURL)) throw new Error('本地调试只能连接本机 API');
      result = await request('/v1/auth/local', 'POST', {}, false);
    } else {
      const auth = await new Promise((resolve, reject) => wx.login({success:resolve, fail:reject}));
      if (!auth.code) throw new Error('微信登录未完成，请重试。');
      result = await request('/v1/auth/wechat', 'POST', {code:auth.code}, false);
    }
    wx.setStorageSync('session', result.token);
  })();
  try { await loginPending; } finally { loginPending = null; }
}
async function goal() {
  await login();
  const cached = wx.getStorageSync('goal');
  if (cached) return cached;
  const exams = await request('/v1/exams', 'GET', {}, false);
  const pack = exams.find(x => x.id === 'ruankao.senior.system_architect');
  if (!pack) throw new Error('架构师题库尚未发布。');
  const result = await request('/v1/goals', 'POST', {
    exam_id:pack.id, release_id:pack.release_id, daily_minutes:15
  });
  wx.setStorageSync('goal', result.goal_id);
  return result.goal_id;
}
async function chat(goalId, body) {
  const base = `/v1/goals/${goalId}/chat`;
  let result, initialError;
  try { result = await request(base+'?async_mode=true','POST',body); }
  catch(e) { initialError = e; }
  if (result && result.text) return result;
  // Long model calls run behind a database lease; each WeChat call stays short.
  // A lost POST response is recovered by its same request ID, without a second generation.
  for (let step=0;step<45;step++) {
    await new Promise(resolve=>setTimeout(resolve,1500));
    let state;
    try { state = await request(base+'/'+body.request_id); }
    catch(e) { if (initialError) throw initialError; throw e; }
    if (state.status==='complete') return state.response;
    if (state.status==='failed') throw new Error('这次回复没有完成，请重试，原消息会保留。');
  }
  throw new Error('私教还在整理回复，请稍后重试这句话。');
}
async function transcribe(goalId,body) {
  const base=`/v1/goals/${goalId}/voice`;
  let result,initialError;
  let pending=false;
  if(body.audio_base64.length>60000) {
    try {result=await request(base+'/'+body.request_id);pending=result.status==='pending';}
    catch(e){if(e.statusCode!==404)throw e;}
    if(result && result.status==='complete')return result.text;
    if(result && result.status==='expired')throw new Error('这段转写已过期，请重新录制。');
  }
  if(!pending) {
    try {const prepared=await uploadMedia(goalId,body,'voice','audio_base64');result=await request(base,'POST',prepared);} catch(e) {initialError=e;}
  }
  if(result && result.status==='complete') return result.text;
  for(let step=0;step<40;step++) {
    await new Promise(resolve=>setTimeout(resolve,1500));
    let state;
    try {state=await request(base+'/'+body.request_id);} catch(e) {throw initialError || e;}
    if(state.status==='complete') return state.text;
    if(state.status==='expired') throw new Error('这段转写已过期，请重新录制。');
    if(state.status==='failed') throw new Error('暂时没转出来，录音还在，可以重试。');
  }
  throw new Error('转写还在进行，请稍后重试这段录音。');
}
async function review(goalId,body,resume=false,alive=()=>true) {
  const base=`/v1/goals/${goalId}/reviews`;
  const id=typeof body==='string'?body:body.request_id;
  let result,initialError;
  if(!resume) {
    try {
      let pending=false,retry=false;
      if(typeof body==='object' && body.file_base64 && body.file_base64.length>60000) {
        try {result=await request(base+'/'+id);pending=result.status==='pending';retry=result.status==='failed';}
        catch(e){if(e.statusCode!==404)throw e;}
        if(result && result.status==='complete')return result.response;
      }
      if(!pending) {
        const retryStored=typeof body==='string' || retry;
        const prepared=retryStored?{}:await uploadMedia(goalId,body,'essay','file_base64');
        result=await request(retryStored?base+'/'+id+'/retry':base,'POST',prepared);
      }
    }
    catch(e) {if([413,422,409,429].includes(e.statusCode))throw e;initialError=e;}
  }
  if(result && result.status==='complete')return result.response;
  for(let step=0;step<100;step++) {
    await new Promise(resolve=>setTimeout(resolve,1500));
    if(!alive())throw new Error('已退出页面，批改完成后可在聊天记录中查看。');
    let state;
    try {state=await request(base+'/'+id);}catch(e){throw initialError || e;}
    if(state.status==='complete')return state.response;
    if(state.status==='failed')throw new Error('这次批改未完成，原内容已保留，可以重试。');
  }
  throw new Error('批改还在进行，稍后点重试即可继续查看，不会重复记分。');
}
const reviewPending=id=>request(`/v1/goals/${id}/reviews/pending`);
async function uploadMedia(goalId,body,purpose,field) {
  const encoded=body[field];
  if(!encoded || encoded.length<=60000)return body;
  const size=encoded.length*3/4-(encoded.endsWith('==')?2:encoded.endsWith('=')?1:0);
  const base=`/v1/goals/${goalId}/uploads`;
  const file=await request(base,'POST',{request_id:body.request_id,purpose,byte_size:size,
    filename:purpose==='voice'?'recording.'+body.format:body.filename});
  for(let offset=0,index=0;offset<encoded.length;offset+=file.chunk_chars,index++) {
    await request(base+'/'+file.upload_id+'/chunks','POST',{index,data:encoded.slice(offset,offset+file.chunk_chars)});
  }
  const result={...body,upload_id:file.upload_id};delete result[field];return result;
}
module.exports = {request, goal, initCloud, chat, transcribe,review,reviewPending};
