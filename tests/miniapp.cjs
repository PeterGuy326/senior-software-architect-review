// Exercise native page event handlers without fabricating a WeChat preview.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
let definition, failFirst = true, requests = [];
const sampleQuestion = {issue_id:'issue-1',question:{stem:'测试题',options:[{label:'A',text:'选项 A'},{label:'B',text:'选项 B'}]}};
const api = {goal:async()=> 'goal-1',request:async(url,method,data)=>{
  requests.push({url,method,data});
  if(url.endsWith('/next')) return sampleQuestion;
  if(failFirst) {failFirst=false;throw Error('network interrupted');}
  return {correct:true,message:'完成',explanation:'说明'};
}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../miniprogram/pages/chat/index.js'),'utf8'),{
  require:n=>n.includes('services')?api:{},
  Page:p=>definition=p,wx:{setStorageSync(){},setNavigationBarColor(){}}
});
const page = {...definition,data:JSON.parse(JSON.stringify(definition.data)),setData(x){Object.assign(this.data,x);}};
(async()=>{
  await page.start();
  assert.equal(page.data.screen,'quiz');
  await page.choose({currentTarget:{dataset:{label:'A'}}});
  assert.equal(page.data.selected,'A');assert.equal(requests.length,1);
  await page.choose({currentTarget:{dataset:{label:'B'}}});
  assert.equal(page.data.selected,'B');assert.equal(requests.length,1);
  // TDesign radio-group reports detail.value rather than a button dataset.
  page.choose({detail:{value:'A'}});assert.equal(page.data.selected,'A');
  page.choose({detail:{value:'B'}});assert.equal(requests.length,1);
  page.toggleUnsure();
  assert.equal(page.data.uncertain,true);
  await page.primaryAction();
  assert.ok(page.data.error);assert.equal(page.data.answerLocked,true);
  await page.choose({currentTarget:{dataset:{label:'A'}}});
  page.toggleUnsure();
  assert.equal(page.data.selected,'B');assert.equal(page.data.uncertain,true);
  await page.primaryAction();
  assert.deepEqual(requests[1].data,requests[2].data);
  assert.equal(requests[1].data.selected,'B');assert.equal(requests[1].data.confidence,'guess');
  assert.equal(page.data.count,1);
  await page.choose({currentTarget:{dataset:{label:'A'}}});
  assert.equal(page.data.selected,'B');
  await page.primaryAction();
  assert.equal(page.data.selected,'');assert.equal(page.data.answerLocked,false);
  page.data.appearance='dark';page.applyTheme();assert.equal(page.data.theme,'dark');
  page.data.appearance='light';page.applyTheme();assert.equal(page.data.theme,'light');
  page.data.appearance='system';page.systemTheme='dark';page.applyTheme();assert.equal(page.data.theme,'dark');
  page.selectAppearance({currentTarget:{dataset:{value:'light'}}});assert.equal(page.data.theme,'light');
  page.menu();assert.equal(page.data.sheet,'menu');
  page.appearance();assert.equal(page.data.sheet,'appearance');
  page.sheetChange({detail:{visible:false}});assert.equal(page.data.sheet,'');
  console.log('Mini Program page: change selection before confirmation, retry without rewriting, next question and themes passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
