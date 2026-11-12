const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
let calls=[],selectedFile={name:'paper.docx',path:'temp-file',size:100},reads=0,consent=true,fail=false;
const task={issue_id:'a'.repeat(32),title:'短案例',prompt:'请说明方案',kind:'case'};
const api={goal:async()=> 'goal',request:async(url,method,data)=>{
  calls.push({url,method,data});if(url.endsWith('/case'))return {text:task.prompt,kind:'case_task',case:task};
  if(url.endsWith('/dismiss'))return {status:'abandoned'};return {};
},review:async(goal,body)=>{calls.push({review:body});if(fail)throw Error('network interrupted');return {
  kind:'review_report',review_kind:typeof body==='string'?'essay':body.kind,
  case_issue_id:typeof body==='object'?body.issue_id:null,text:'评分完成',report:{final_score:15,max_score:25,points:[]}};}};
const wx={getStorageSync:()=>consent,setStorageSync(){},showModal:o=>o.success({confirm:consent})};
const moduleBox={exports:{}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../miniprogram/pages/chat/reviews.js'),'utf8'),{
  module:moduleBox,require:n=>n.endsWith('/documents')?{choose:async()=>selectedFile,read:async()=>{reads++;return 'synthetic-file-base64';}}:api,wx});
let definition;
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../miniprogram/pages/chat/index.js'),'utf8'),{
  require:n=>n==='./reviews'?moduleBox.exports:api,Page:p=>definition=p,wx});
const make=()=>({...definition,data:JSON.parse(JSON.stringify(definition.data)),setData(x){Object.assign(this.data,x);}});
(async()=>{
  let page=make();await page.startCase();
  assert.equal(page.data.replyMode,'case');assert.equal(page.data.messages.at(-1).kind,'case_task');
  assert.equal(calls.filter(c=>c.review).length,0);
  page.data.input='先定义业务边界，再解释可靠投递与补偿。';fail=true;await page.send();
  assert.equal(page.data.reviewFailed,true);const pending=page.pendingReview;
  fail=false;await page.retryReview();assert.equal(page.pendingReview,null);
  const submitted=calls.filter(c=>c.review);assert.deepEqual(submitted[0].review,submitted[1].review);
  assert.equal(page.data.messages.at(-1).kind,'review_report');
  assert.equal(page.data.messages.find(m=>m.case).case.completed,true);
  page=make();await page.chooseEssay();assert.equal(page.data.replyMode,'essay');assert.equal(reads,0);
  consent=false;await page.send();assert.equal(reads,0);assert.ok(page.data.essayFile);
  consent=true;await page.send();assert.equal(reads,1);
  assert.equal(page.data.messages.at(-1).kind,'review_report');assert.equal(page.pendingReview,null);
  assert.ok(calls.find(c=>c.review && c.review.kind==='essay').review.file_base64);
  page=make();selectedFile=null;await page.chooseEssay();assert.equal(page.data.replyMode,'chat');
  page.data.input='原聊天草稿';selectedFile={name:'paper.docx',path:'temp-file',size:100};await page.chooseEssay();page.exitReply();
  assert.equal(page.data.input,'原聊天草稿');assert.equal(page.data.essayFile,null);
  console.log('Subjective UI: voice-answer submission boundary, fixed retry, document consent, no upload before confirm, cancellation and report rendering state passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
