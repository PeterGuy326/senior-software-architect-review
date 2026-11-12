const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
let sent=[],chunks=[],committed=false,purpose='essay';
const config={transport:'cloud',cloudEnv:'test-env',cloudService:'test-service'};
const wx={getStorageSync:()=> 'synthetic-session',cloud:{init(){},callContainer(o){
  sent.push(o);let code=200,result={};
  if(o.path.endsWith('/uploads'))result={upload_id:'a'.repeat(32),chunk_chars:64000};
  else if(o.path.endsWith('/chunks')){chunks.push(o.data);result={ok:true};}
  else if(o.method==='POST' && (o.path.endsWith('/reviews') || o.path.endsWith('/voice'))) {
    assert.equal(o.data.upload_id,'a'.repeat(32));assert.ok(!o.data.file_base64 && !o.data.audio_base64);
    committed=true;code=202;result={status:'pending'};
  }else if(!committed){code=404;result={detail:'not found'};}
  else result=purpose==='essay'?{status:'complete',response:{kind:'review_report'}}:{status:'complete',text:'已转写'};
  o.success({statusCode:code,data:result});
}}};
const box={exports:{}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../miniprogram/services/api.js'),'utf8'),{
  module:box,require:()=>config,wx,setTimeout:callback=>callback()});
(async()=>{
  const data='A'.repeat(128000);
  const result=await box.exports.review('goal',{request_id:'review1234',kind:'essay',filename:'paper.docx',file_base64:data});
  assert.equal(result.kind,'review_report');assert.equal(chunks.map(c=>c.data).join(''),data);
  assert.equal(chunks.length,2);assert.ok(sent.every(o=>Buffer.byteLength(JSON.stringify(o.data))<70000));
  sent=[];chunks=[];committed=false;purpose='voice';
  assert.equal(await box.exports.transcribe('goal',{request_id:'voice1234',format:'mp3',audio_base64:data}),'已转写');
  assert.equal(chunks.length,2);assert.ok(sent.every(o=>Buffer.byteLength(JSON.stringify(o.data))<70000));
  console.log('Chunk uploads: large document and voice stay below small WeChat envelopes; bytes are unchanged and final calls contain only owned upload IDs.');
})().catch(e=>{console.error(e);process.exitCode=1;});
