const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname,'../miniprogram/services/api.js'),'utf8');
function setup(config) {
  const calls=[], storage={session:'test-session',goal:'test-goal'};
  const module={exports:{}};
  let response={statusCode:200,data:{ok:true}}, initialized=0;
  function send(options) {calls.push(options);options.success(response);}
  vm.runInNewContext(source,{module,require:()=>config,wx:{
    getStorageSync:k=>storage[k],setStorageSync:(k,v)=>storage[k]=v,removeStorageSync:k=>delete storage[k],
    login:o=>o.success({code:'real-temporary-code'}),request:send,
    cloud:{init:()=>initialized++,callContainer:send}
  },setTimeout:callback=>callback()});
  return {api:module.exports,calls,storage,get initialized(){return initialized;},respond:r=>response=r};
}
(async()=>{
  const cloud=setup({transport:'cloud',cloudEnv:'test-env',cloudService:'test-service'});
  await cloud.api.request('/v1/goals/g/next','POST');
  await cloud.api.request('/v1/exams','GET',{},false);
  assert.equal(cloud.initialized,1);
  assert.equal(cloud.calls[0].path,'/v1/goals/g/next');
  assert.equal(cloud.calls[0].config.env,'test-env');
  assert.equal(cloud.calls[0].header['X-WX-SERVICE'],'test-service');
  assert.equal(cloud.calls[0].header.Authorization,'Bearer test-session');
  assert.equal(cloud.calls[1].header.Authorization,undefined);
  cloud.respond({statusCode:401,data:{detail:'请重新登录'}});
  await assert.rejects(cloud.api.request('/v1/goals/g/status'),/请重新登录/);
  assert.equal(cloud.storage.session,undefined);
  assert.equal(cloud.storage.goal,undefined);
  cloud.respond({statusCode:200,data:{token:'new-session',ok:true}});
  await cloud.api.request('/v1/issues/same-issue/answer','POST',{selected:'B'});
  assert.equal(cloud.calls[3].path,'/v1/auth/wechat');
  assert.equal(cloud.calls[3].data.code,'real-temporary-code');
  assert.equal(cloud.calls[4].path,'/v1/issues/same-issue/answer');
  assert.equal(cloud.calls[4].header.Authorization,'Bearer new-session');
  cloud.respond({statusCode:503,data:null});
  await assert.rejects(cloud.api.request('/healthz'),/暂时无法完成/);
  const https=setup({transport:'https',baseURL:'https://example.com/'});
  await https.api.request('/healthz','GET',{},false);
  assert.equal(https.calls[0].url,'https://example.com/healthz');
  assert.equal(https.initialized,0);
  const polling=setup({transport:'cloud',cloudEnv:'test-env',cloudService:'test-service'});
  polling.respond({statusCode:202,data:{status:'pending'}});
  const pendingReply=polling.api.chat('test-goal',{request_id:'request123',message:'测试'});
  // Let the POST finish, then return the persisted result to the poll.
  await Promise.resolve(); await Promise.resolve();
  polling.respond({statusCode:200,data:{status:'complete',response:{text:'云端回复'}}});
  assert.equal((await pendingReply).text,'云端回复');
  assert.equal(polling.calls[0].path,'/v1/goals/test-goal/chat?async_mode=true');
  assert.ok(polling.calls.some(c=>c.path.endsWith('/chat/request123')));
  assert.ok(polling.calls.every(c=>c.timeout<=15000));
  console.log('Mini Program transport: cloud routing, auth expiry and HTTPS fallback passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
