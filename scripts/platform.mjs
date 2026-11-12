import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(import.meta.url);
process.chdir(root);
if (fs.existsSync('.env')) {
  for (const line of fs.readFileSync('.env','utf8').split(/\r?\n/)) {
    const m = line.match(/^([A-Z_][A-Z0-9_]*)=(.*)$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^(['"])(.*)\1$/, '$2');
  }
}
function missing(keys) { return keys.filter(k => !process.env[k]); }
function need(keys) { const m = missing(keys); if (m.length) throw new Error('缺少配置：' + m.join(', ') + '。参见 .env.example'); }
function miniKeys() { return ['WECHAT_APP_ID','MINIPROGRAM_PRIVATE_KEY_PATH',
  ...((process.env.MINI_TRANSPORT || 'cloud') === 'cloud' ? ['TCB_ENV_ID','TCB_SERVICE_NAME'] : ['API_BASE_URL'])]; }
function configureMini() {
  need(miniKeys().filter(k=>k!=='MINIPROGRAM_PRIVATE_KEY_PATH'));
  if (!/^wx[a-z0-9]{16}$/i.test(process.env.WECHAT_APP_ID)) throw new Error('AppID 格式无效');
  const transport = process.env.MINI_TRANSPORT || 'cloud';
  if (!['cloud','https'].includes(transport)) throw new Error('MINI_TRANSPORT 只允许 cloud 或 https');
  if (transport === 'https' && !/^https:\/\//.test(process.env.API_BASE_URL)) throw new Error('手机体验版必须使用 HTTPS 后端');
  fs.writeFileSync('miniprogram/config.local.js', 'module.exports = ' + JSON.stringify({transport,
    cloudEnv:process.env.TCB_ENV_ID,cloudService:process.env.TCB_SERVICE_NAME,
    baseURL:transport === 'https' ? process.env.API_BASE_URL : '',localDebug:false}) + ';\n');
  const project = JSON.parse(fs.readFileSync('miniprogram/project.config.json'));
  project.appid = process.env.WECHAT_APP_ID;
  fs.writeFileSync('miniprogram/project.config.json',JSON.stringify(project,null,2)+'\n');
}
function run(command, args, env = process.env) {
  const r = spawnSync(command, args, {cwd:root,env,encoding:'utf8',maxBuffer:20*1024*1024,shell:false});
  for (const output of [r.stdout,r.stderr]) if (output) {
    const safe = ['WECHAT_APP_SECRET','DATABASE_URL','CLOUDBASE_SERVER_KEY','MODEL_API_KEY','ASR_API_KEY'].reduce((s,k) => process.env[k] ? s.replaceAll(process.env[k],'[REDACTED]') : s, output);
    process.stdout.write(safe);
  }
  if (r.error) throw r.error;
  if (r.status !== 0) throw new Error(`${command} 执行失败，退出码 ${r.status}`);
}
const action = process.argv[2] || 'check';
try {
  if (action === 'check') {
    for (const p of ['miniprogram/app.json','miniprogram/project.config.json','exam_packs/ruankao-system-architect/manifest.json']) JSON.parse(fs.readFileSync(p));
    console.log('CLI: CloudBase ' + require('@cloudbase/cli/package.json').version + '; miniprogram-ci ' + require('miniprogram-ci/package.json').version);
    console.log('后端云部署配置：' + (missing(process.env.STORAGE_TRANSPORT === 'cloudbase_rpc' ? ['TCB_ENV_ID','CLOUDBASE_SERVER_KEY','CONTENT_RELEASE_ID'] : ['TCB_ENV_ID','DATABASE_URL','WECHAT_APP_ID','WECHAT_APP_SECRET']).join(', ') || '齐全'));
    console.log('微信登录配置：' + (missing(['WECHAT_APP_ID','WECHAT_APP_SECRET']).join(', ') || '齐全'));
    console.log('微信 CI 配置：' + (missing(miniKeys()).join(', ') || '齐全'));
    run('uv', ['run','python','-c','from apps.api.content import compile_pack; r,p=compile_pack(); print("内容校验通过:",r,len(p["items"]),"题；未导入私人记录")']);
  } else if (action === 'deploy') {
    const managed = process.env.STORAGE_TRANSPORT === 'cloudbase_rpc';
    need(managed ? ['TCB_ENV_ID','CLOUDBASE_SERVER_KEY','CONTENT_RELEASE_ID'] : ['TCB_ENV_ID','DATABASE_URL','WECHAT_APP_ID','WECHAT_APP_SECRET','CONTENT_RELEASE_ID']);
    if (!managed && !process.env.DATABASE_URL.startsWith('postgresql')) throw new Error('云端只允许持久化 PostgreSQL，不能部署本地 SQLite');
    const env = Object.fromEntries(['DATABASE_URL','WECHAT_APP_ID','WECHAT_APP_SECRET','CONTENT_RELEASE_ID','TCB_ENV_ID','CLOUDBASE_SERVER_KEY','STORAGE_TRANSPORT','MODEL_PROVIDER','MODEL_BASE_URL','MODEL_NAME','MODEL_API_KEY','MODEL_FREE_ONLY','ASR_API_KEY','KNOWLEDGE_RELEASE_ID'].filter(k=>process.env[k]).map(k => [k,process.env[k]]));
    env.APP_ENV = 'development'; env.TZ = 'Asia/Shanghai';
    // Cloud CLI may upload sources BEFORE Docker applies .dockerignore.
    // Stage an explicit allowlist so neither learner files nor secrets reach it.
    const stage = path.join(root,'.study/platform/deploy-' + Date.now());
    stageDeployment(stage);
    // No shell, no credentials printed by this script. tcb credentials stay in its own login store.
    run('node', ['node_modules/@cloudbase/cli/bin/cloudbase','cloudrun','deploy',
      '--env-id',process.env.TCB_ENV_ID,'--service-name',process.env.TCB_SERVICE_NAME || 'wuji-coach-dev',
      '--source',stage,'--port','8080','--min-num','0','--max-num','1',
      '--open-access-types','PUBLIC,MINIAPP','--env-params',JSON.stringify(env),'--wait','--force','--yes']);
  } else if (action === 'stage') {
    const stage = path.join(root,'.study/platform/deploy-' + Date.now());
    stageDeployment(stage);
    console.log('已生成仅含白名单源码的部署包：' + path.relative(root,stage));
  } else if (action === 'configure-mini') {
    configureMini();
    console.log('已配置真实 AppID 和公开连接参数；未写入任何服务端密钥。');
  } else if (action === 'preview' || action === 'upload') {
    need(miniKeys());
    const keyPath = path.resolve(process.env.MINIPROGRAM_PRIVATE_KEY_PATH);
    if (!fs.existsSync(keyPath)) throw new Error('未找到本机代码上传密钥文件');
    if (keyPath.startsWith(root + path.sep)) throw new Error('上传密钥必须放在仓库之外');
    configureMini();
    const ci = require('miniprogram-ci');
    const project = new ci.Project({appid:process.env.WECHAT_APP_ID,type:'miniProgram',projectPath:path.join(root,'miniprogram'),privateKeyPath:keyPath,
      ignores:['config.local.example.js','project.private.config.json']});
    const options = {project,desc:'架构师选择题与真实进度闭环',setting:{es6:true,minify:true},onProgressUpdate:()=>{}};
    if (action === 'preview') {
      fs.mkdirSync('.study/platform', {recursive:true});
      await ci.preview({...options,qrcodeFormat:'image',qrcodeOutputDest:path.join(root,'.study/platform/preview.jpg')});
      console.log('预览二维码：.study/platform/preview.jpg（仅开发/体验权限用户可用）');
    } else {
      await ci.upload({...options,version:process.env.RELEASE_VERSION || '0.1.0'});
      console.log('代码已上传为开发版本。设为体验版、添加体验者需在微信后台完成。');
    }
  } else throw new Error('未知操作：' + action);
} catch (e) {
  // Never echo SDK exceptions which may include signed URLs or secrets.
  const safe = String(e.message || '执行失败');
  const redacted = ['WECHAT_APP_SECRET','DATABASE_URL','CLOUDBASE_SERVER_KEY','MODEL_API_KEY'].reduce((s,k) => process.env[k] ? s.replaceAll(process.env[k],'[REDACTED]') : s, safe);
  console.error(redacted.slice(0,1000));process.exitCode=1;
}
function stageDeployment(stage) {
  fs.mkdirSync(stage,{recursive:true});
  const exact = ['Dockerfile','.dockerignore','pyproject.toml','uv.lock',
    'scripts/tutor.py','scripts/grade.py','scripts/sanitize_bank.py',
    'tutor/curriculum.json','tutor/mock_paper.py'];
  for (const source of exact) {
    const target = path.join(stage,source);fs.mkdirSync(path.dirname(target),{recursive:true});
    fs.copyFileSync(source,target);
  }
  for (const directory of ['apps','exam_packs','exam-bank']) {
    fs.cpSync(directory,path.join(stage,directory),{recursive:true,
      filter:source=>fs.statSync(source).isDirectory() ? path.basename(source)!=='__pycache__' : /\.(py|json|md)$/.test(source)});
  }
}
