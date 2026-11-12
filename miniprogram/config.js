// Public client configuration only. NEVER place AppSecret or model keys here.
let local = {};
try { local = require('./config.local.js'); } catch (_) {}
module.exports = { transport:'cloud', cloudEnv:'wuji-coach-dev-d4gtwqert85ce3eae',
  cloudService:'wuji-coach-dev', baseURL:'', localDebug:false, ...local };
