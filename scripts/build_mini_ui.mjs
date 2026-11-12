// Reproducible npm build. Keep TDesign's icons available without a CDN request.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import ci from 'miniprogram-ci';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const mini=path.join(root,'miniprogram');
const result=await ci.packNpmManually({packageJsonPath:path.join(mini,'package.json'),miniprogramNpmDistDir:mini});
if(result.warnList.length) throw new Error(JSON.stringify(result.warnList));
const iconFile=path.join(mini,'miniprogram_npm/tdesign-miniprogram/icon/icon.wxss');
const library=path.dirname(path.dirname(iconFile));
const page=JSON.parse(fs.readFileSync(path.join(mini,'pages/chat/index.json')));
const keep=new Set(['common','mixins','locale','miniprogram_npm']);
function visit(component) {
  const folder=component.split('/')[0];
  if(keep.has(folder))return;
  keep.add(folder);
  const config=JSON.parse(fs.readFileSync(path.join(library,component+'.json')));
  for(const dependency of Object.values(config.usingComponents || {})) {
    visit(path.posix.normalize(path.posix.join(path.posix.dirname(component),dependency)));
  }
}
for(const component of Object.values(page.usingComponents)) visit(component.replace(/^\/?(?:miniprogram_npm\/)?tdesign-miniprogram\//,''));
// Only delete build output within this exact, generated npm package directory.
if(!library.endsWith(path.join('miniprogram_npm','tdesign-miniprogram')))throw new Error('Unexpected build directory');
for(const entry of fs.readdirSync(library,{withFileTypes:true})) {
  if(entry.isDirectory() && !keep.has(entry.name))fs.rmSync(path.join(library,entry.name),{recursive:true});
}
const font=fs.readFileSync(path.join(mini,'assets/tdesign-icons.woff')).toString('base64');
const css=fs.readFileSync(iconFile,'utf8');
if(!css.includes('@font-face')) throw new Error('TDesign icon font format changed; inspect before building.');
fs.writeFileSync(iconFile,css.replace(/@font-face\{[^}]+\}/,'@font-face{font-family:t;src:url("data:font/woff;base64,'+font+'") format("woff");font-weight:400;font-style:normal;}'));
console.log('TDesign npm components built on demand; official icon font embedded for offline rendering.');
