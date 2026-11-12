const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
let definition, fail=true, calls=[];
const api={goal:async()=> 'goal',request:async(path,method,data)=>{
  calls.push({path,method,data});
  if (method!=='POST') return {items:[{request_id:'history1',user:'之前的问题',response:{text:'之前的回复',sources:[],actions:[]}}]};
  if(fail){fail=false;throw Error('network interrupted');}
  return {text:'真实回复',sources:[{id:'one',title:'公开笔记'}],actions:[{type:'practice',label:'开始练一道'}]};
}};
api.chat=async(goal,data)=>api.request(`/v1/goals/${goal}/chat`,'POST',data);
vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'../miniprogram/pages/chat/index.js'),'utf8'),{
  require:()=>api,Page:p=>definition=p,wx:{}});
const page={...definition,data:JSON.parse(JSON.stringify(definition.data)),setData(x){Object.assign(this.data,x);}};
(async()=>{
  await page.loadConversation();
  assert.equal(page.data.messages.length,2);
  assert.equal(page.data.showWelcome,false);
  page.home();assert.equal(page.data.showWelcome,true);
  assert.equal(page.data.messages.length,2); // Returning home never deletes history.
  page.resumeChat();assert.equal(page.data.showWelcome,false);
  page.data.input='今天很累，怎么学？';
  await page.send();
  assert.equal(page.data.messages.length,3);
  assert.ok(page.data.chatFailed);
  const pending=page.pendingChat;
  page.data.input='不应该替换原消息';
  await page.send();
  assert.equal(calls.length,2);
  await page.deliverChat();
  assert.deepEqual(calls[1].data,calls[2].data);
  assert.equal(calls[2].data.request_id,pending.request_id);
  assert.equal(page.data.messages.length,4);
  assert.equal(page.data.messages[3].text,'真实回复');
  assert.equal(page.pendingChat,null);
  page.toggleSources({currentTarget:{dataset:{index:3}}});
  assert.equal(page.data.messages[3].sourcesOpen,true);
  console.log('Chat page: owned history, free text, preserved retry and no keyword routing passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
