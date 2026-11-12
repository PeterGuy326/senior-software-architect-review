// Owns only the current page's recorder. Audio is uploaded only after a normal stop.
function removeFile(path) {
  if (path) wx.getFileSystemManager().unlink({filePath:path,fail(){}});
}
function createRecorder(hooks) {
  const manager=wx.getRecorderManager();
  let discarded=false,disposed=false,active=false,timer;
  function clear() { if(timer) clearInterval(timer);timer=null;active=false; }
  manager.onStart(()=>{
    if(disposed || discarded) {manager.stop();return;}
    active=true;let seconds=0;hooks.state('recording',seconds);
    timer=setInterval(()=>hooks.state('recording',++seconds),1000);
  });
  manager.onStop(result=>{
    clear();
    if(discarded || disposed) {removeFile(result.tempFilePath);if(!disposed) hooks.state('idle',0);return;}
    if(result.duration<500 || !result.tempFilePath) {removeFile(result.tempFilePath);hooks.error('说话时间太短了，请再录一次。');return;}
    hooks.file(result.tempFilePath);
  });
  manager.onError(()=>{clear();if(!disposed && !discarded) hooks.error('录音没有成功，请检查麦克风权限后再试。');});
  if(manager.onInterruptionBegin) manager.onInterruptionBegin(()=>{
    discarded=true;manager.stop();clear();if(!disposed) hooks.error('录音被中断了，这段不会发送，请重新录制。');
  });
  return {
    start() {discarded=false;manager.start({duration:60000,sampleRate:16000,numberOfChannels:1,encodeBitRate:48000,format:'mp3'});},
    stop() {manager.stop();},
    cancel() {discarded=true;if(active) manager.stop();clear();if(!disposed) hooks.state('idle',0);},
    dispose() {disposed=true;discarded=true;if(active) manager.stop();clear();}
  };
}
function permission() {
  return new Promise((resolve,reject)=>{
    const authorize=()=>wx.authorize({scope:'scope.record',success:resolve,
      fail:()=>reject(new Error('麦克风未授权，可以继续打字，或到小程序设置中开启。'))});
    if(wx.requirePrivacyAuthorize) wx.requirePrivacyAuthorize({success:authorize,
      fail:()=>reject(new Error('隐私授权未完成，可以先打字输入。'))});
    else authorize();
  });
}
function readAudio(path) {
  return new Promise((resolve,reject)=>wx.getFileSystemManager().getFileInfo({filePath:path,
    success(info) {
      if(info.size>512*1024) {reject(new Error('录音有点大，请分成两段说。'));return;}
      wx.getFileSystemManager().readFile({filePath:path,encoding:'base64',success:r=>resolve(r.data),
        fail:()=>reject(new Error('这段录音已失效，请重新录制。'))});
    },fail:()=>reject(new Error('找不到这段录音，请重新录制。'))}));
}
module.exports={createRecorder,permission,readAudio,removeFile};
