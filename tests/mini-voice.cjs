const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
let callbacks={},deleted=[],uploaded=[];
const manager={onStart:f=>callbacks.start=f,onStop:f=>callbacks.stop=f,onError:f=>callbacks.error=f,
  onInterruptionBegin:f=>callbacks.interrupt=f,start:options=>manager.options=options,stop:()=>manager.stopped=true};
const recorderModule={exports:{}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../miniprogram/services/voice.js'),'utf8'),{
  module:recorderModule,wx:{getRecorderManager:()=>manager,getFileSystemManager:()=>({unlink:o=>deleted.push(o.filePath)})},
  setInterval:()=>1,clearInterval(){}});
const events=[];
const recorder=recorderModule.exports.createRecorder({state:(...x)=>events.push(x),file:p=>uploaded.push(p),error:e=>events.push(e)});
recorder.start();callbacks.start();recorder.cancel();callbacks.stop({tempFilePath:'cancelled',duration:1000});
assert.equal(uploaded.length,0);assert.ok(deleted.includes('cancelled'));
recorder.start();callbacks.start();recorder.stop();callbacks.stop({tempFilePath:'accepted',duration:1000});
assert.deepEqual(uploaded,['accepted']);assert.equal(manager.options.duration,60000);assert.equal(manager.options.format,'mp3');
recorder.dispose();callbacks.stop({tempFilePath:'late',duration:1000});assert.equal(uploaded.length,1);assert.ok(deleted.includes('late'));

let pageDefinition,fail=true,transcripts=[],chatCalls=0,voiceHooks;
const api={goal:async()=> 'goal',transcribe:async(id,body)=>{transcripts.push(body);if(fail){fail=false;throw Error('network interrupted');}return '今天只练一道题';},chat:async()=>{chatCalls++;return {text:'reply'};}};
const voice={removeFile:p=>deleted.push(p),readAudio:async()=> 'same-audio-base64',permission:async()=>{},createRecorder:h=>{voiceHooks=h;return {start(){h.state('recording',0);},stop(){},cancel(){h.state('idle',0);},dispose(){}};}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../miniprogram/pages/chat/index.js'),'utf8'),{
  require:n=>n.endsWith('/voice')?voice:api,Page:p=>pageDefinition=p,wx:{getStorageSync:()=>true,setStorageSync(){}}});
const page={...pageDefinition,data:JSON.parse(JSON.stringify(pageDefinition.data)),voiceAlive:true,setData:x=>Object.assign(page.data,x)};
(async()=>{
  page.data.input='已有草稿';
  await page.toggleVoice();assert.equal(page.data.voiceStatus,'recording');
  await voiceHooks.file('temp-audio');
  assert.equal(page.data.voiceStatus,'failed');assert.ok(page.pendingVoice);assert.equal(chatCalls,0);
  await page.retryVoice();
  assert.equal(page.data.input,'已有草稿\n今天只练一道题');assert.equal(page.data.voiceStatus,'ready');assert.equal(chatCalls,0);
  assert.equal(transcripts[0].request_id,transcripts[1].request_id);assert.equal(transcripts[0].audio_base64,transcripts[1].audio_base64);
  assert.equal(page.pendingVoice,null);assert.ok(deleted.includes('temp-audio'));
  await page.toggleVoice();page.onHide();assert.equal(page.data.voiceStatus,'idle');
  console.log('Voice input: cancellation, recording limits, no auto-send, editable draft and same-audio retry passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
