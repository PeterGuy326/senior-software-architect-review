const api = require('../../services/api');
const voice = require('../../services/voice');
const reviewActions = require('./reviews');
Page({
  ...reviewActions,
  data: { screen:'home', theme:'light', navTop:24, navHeight:44, viewportHeight:640, input:'', busy:false,
    question:null, report:null, selected:'', issueId:'', error:'', uncertain:false, answerLocked:false,
    letters:['A','B','C','D'], count:0, justOne:false, appearance:'system', messages:[], scrollTarget:'', chatFailed:false,
    voiceStatus:'idle',voiceActive:false,voiceSeconds:0,voiceError:'',voiceCanRetry:false,privacyOpen:false,privacyName:'小程序隐私保护指引',
    showWelcome:true, sheet:'', sheetTitle:'', dialogOpen:false, dialogTitle:'', dialogContent:'', progressData:null,
    appearances:[{value:'system',label:'跟随系统',icon:'desktop'},{value:'light',label:'浅色',icon:'sunny'},{value:'dark',label:'深色',icon:'moon'}],
    subjects:[{key:'comprehensive',name:'综合知识'},{key:'case',name:'案例分析'},{key:'essay',name:'论文'}],
    replyMode:'chat',caseTask:null,essayFile:null,essayTopic:null,essayTopics:[],reviewPending:false,reviewFailed:false,privacyPurpose:'voice' },
  onLoad() {
    const info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    const capsule = wx.getMenuButtonBoundingClientRect();
    this.systemTheme = wx.getAppBaseInfo ? wx.getAppBaseInfo().theme : info.theme;
    this.setData({navTop:capsule.top, navHeight:capsule.height + 12, viewportHeight:info.windowHeight,
      appearance:wx.getStorageSync('appearance') || 'system'});
    this.applyTheme();
    this.themeListener = res => { this.systemTheme = res.theme; this.applyTheme(); };
    wx.onThemeChange(this.themeListener);
    this.voiceAlive=true;
    this.reviewClosed=false;
    if(wx.getPrivacySetting) wx.getPrivacySetting({success:r=>this.setData({privacyName:r.privacyContractName || '小程序隐私保护指引'})});
    if(wx.onNeedPrivacyAuthorization) {
      this.privacyListener=resolve=>{this.privacyResolve=resolve;this.setData({privacyOpen:true});};
      wx.onNeedPrivacyAuthorization(this.privacyListener);
    }
    this.loadConversation();
  },
  onShow() {this.voiceHidden=false;},
  onHide() {this.voiceHidden=true;if(this.recorder && this.data.voiceStatus==='recording') this.recorder.cancel();},
  onUnload() {
    this.voiceAlive=false;
    this.reviewClosed=true;
    if(this.recorder) this.recorder.dispose();
    if(this.pendingVoice) voice.removeFile(this.pendingVoice.path);
    if(this.privacyResolve) this.privacyResolve({event:'disagree'});
    if(wx.offNeedPrivacyAuthorization && this.privacyListener) wx.offNeedPrivacyAuthorization(this.privacyListener);
    if (wx.offThemeChange) wx.offThemeChange(this.themeListener);
  },
  onResize(event) { if (event.size && event.size.windowHeight) this.setData({viewportHeight:event.size.windowHeight}); },
  applyTheme() {
    const theme = this.data.appearance === 'system' ? (this.systemTheme || 'light') : this.data.appearance;
    this.setData({theme});
    wx.setNavigationBarColor({frontColor:theme === 'dark' ? '#ffffff' : '#000000',
      backgroundColor:theme === 'dark' ? '#151b18' : '#fafbf8'});
  },
  home() { if (!this.data.busy && !this.data.voiceActive) {if(this.exitReply)this.exitReply();this.setData({screen:'home',showWelcome:true,error:'',report:null,justOne:false});} },
  resumeChat() {this.setData({showWelcome:false,sheet:''});},
  startOne() {if(this.data.busy || this.data.voiceActive)return;this.setData({justOne:true,sheet:''});return this.start();},
  async start() {
    if (this.data.busy || this.data.voiceActive) return;
    if(this.exitReply)this.exitReply();
    this.setData({busy:true,error:''});
    try {
      const id = await api.goal();
      const result = await api.request(`/v1/goals/${id}/next`, 'POST');
      this.pendingAnswer = null;
      this.setData({screen:'quiz',question:result.question,issueId:result.issue_id,
        report:null,selected:'',uncertain:false,answerLocked:false});
    } catch(e) { this.setData({error:e.message}); }
    finally { this.setData({busy:false}); }
  },
  choose(e) {
    if (this.data.busy || this.data.report || this.pendingAnswer) return;
    const selected = e.detail && e.detail.value !== undefined ? e.detail.value : e.currentTarget.dataset.label;
    if (!this.data.question || !this.data.question.options.some(x=>x.label===selected)) return;
    this.setData({selected});
    if (wx.vibrateShort) wx.vibrateShort({type:'light',fail() {}});
  },
  async submitAnswer() {
    if (!this.data.selected || this.data.busy || this.data.report) return;
    this.setData({busy:true,error:'',answerLocked:true});
    // Preserve the exact request across retries, even if a response was lost.
    if (!this.pendingAnswer) this.pendingAnswer = {
      selected:this.data.selected, confidence:this.data.uncertain ? 'guess' : 'sure'
    };
    try {
      const report = await api.request(`/v1/issues/${this.data.issueId}/answer`, 'POST', this.pendingAnswer);
      this.pendingAnswer = null;
      this.setData({report:{...report,explanation:String(report.explanation || '').replace(/\*\*|`/g,'')},
        count:this.data.count + 1});
    } catch(e) { this.setData({error:e.message}); }
    finally { this.setData({busy:false}); }
  },
  retry() { if (this.pendingAnswer) this.submitAnswer(); else this.start(); },
  toggleUnsure() { if (!this.data.busy && !this.data.report && !this.pendingAnswer) this.setData({uncertain:!this.data.uncertain}); },
  primaryAction() { if (this.data.report) return this.next(); return this.submitAnswer(); },
  async next() {
    if (!this.data.report) return;
    if (this.data.justOne) { this.finish(); return; }
    await this.start();
  },
  finish() {
    this.home();this.showDialog('今天练到这里也很好','进度已保存，下次从一道题接着来。');
  },
  async progress() {
    try {
      const id = await api.goal();
      const s = await api.request(`/v1/goals/${id}/status`);
      const counts=await api.request(`/v1/goals/${id}/reviews/summary`);
      this.setData({progressData:{...s,total_count:s.answered_count+counts.case_count+counts.essay_count,
        counts:{comprehensive:s.answered_count,case:counts.case_count,essay:counts.essay_count}}});this.openSheet('progress','学习进展');
    } catch(e) { this.setData({error:e.message}); }
  },
  menu() {
    if(!this.data.voiceActive)this.openSheet('menu','我的私教');
  },
  openSheet(sheet,sheetTitle) {this.setData({sheet,sheetTitle});},
  closeSheet() {this.setData({sheet:''});},
  sheetChange(e) {if(!e.detail.visible)this.closeSheet();},
  appearance() {this.openSheet('appearance','外观');},
  selectAppearance(e) {
    const value=e.currentTarget.dataset.value;
    if(!['system','light','dark'].includes(value))return;
    this.setData({appearance:value});wx.setStorageSync('appearance',value);this.applyTheme();
  },
  goals() {this.openSheet('goals','学习目标');},
  showDialog(dialogTitle,dialogContent) {this.setData({dialogOpen:true,dialogTitle,dialogContent});},
  closeDialog() {this.setData({dialogOpen:false});},
  toggleSources(e) {
    const index=e.currentTarget.dataset.index;
    const messages=this.data.messages.map((m,i)=>i===index?{...m,sourcesOpen:!m.sourcesOpen}:m);
    this.setData({messages});
  },
  pendingFeature(e) {
    return e.currentTarget.dataset.kind==='case'?this.startCase():this.chooseEssay();
  },
  type(e) { this.setData({input:e.detail.value,voiceStatus:this.data.voiceStatus==='ready' ? 'idle' : this.data.voiceStatus,
    ...(this.data.replyMode==='essay' && this.data.essayTopic && e.detail.value ? {essayTopic:null} : {})}); },
  async loadConversation() {
    if (this.data.busy || this.pendingChat || this.data.voiceActive) return;
    this.setData({busy:true,error:''});
    let goalId;
    try {
      const id = await api.goal();goalId=id;
      const result = await api.request(`/v1/goals/${id}/chat`);
      const messages = [];
      for (const turn of result.items || []) {
        messages.push({id:'u'+turn.request_id,role:'user',text:turn.user});
        messages.push({id:'a'+turn.request_id,role:'assistant',...turn.response,text:String(turn.response.text || '').replace(/\*\*|`/g,'')});
      }
      const done=new Set(messages.filter(m=>m.case_issue_id).map(m=>m.case_issue_id));
      this.setData({messages:messages.map(m=>m.case && done.has(m.case.issue_id)?{...m,case:{...m.case,completed:true}}:m),
        showWelcome:!messages.length,scrollTarget:messages.length ? messages[messages.length-1].id : ''});
    } catch(e) { this.setData({error:e.message}); }
    finally { this.setData({busy:false}); }
    if(goalId && this.restoreReview)this.restoreReview(goalId);
  },
  async send() {
    if (this.data.busy || this.pendingChat || this.data.voiceActive) return;
    if(this.data.replyMode!=='chat')return this.submitReview();
    const text = this.data.input.trim(); if (!text) return;
    if (text.length > 2000) { this.setData({error:'这次先说短一点，最多 2000 字。'}); return; }
    const requestId = Date.now().toString(36)+'_'+Math.random().toString(36).slice(2,12);
    this.pendingChat = {request_id:requestId,message:text};
    const messages = this.data.messages.concat({id:'u'+requestId,role:'user',text});
    this.setData({input:'',messages,showWelcome:false,scrollTarget:'u'+requestId,voiceStatus:'idle'});
    await this.deliverChat();
  },
  async deliverChat() {
    if (this.data.busy || !this.pendingChat) return;
    this.setData({busy:true,error:'',chatFailed:false});
    const pending = this.pendingChat;
    try {
      const id = await api.goal();
      const result = await api.chat(id,pending);
      const messages = this.data.messages.concat({id:'a'+pending.request_id,role:'assistant',...result,text:String(result.text || '').replace(/\*\*|`/g,'')});
      this.pendingChat = null;
      this.setData({messages,scrollTarget:'a'+pending.request_id});
    } catch(e) { this.setData({error:e.message,chatFailed:true}); }
    finally { this.setData({busy:false}); }
  },
  async toggleVoice() {
    if(this.data.voiceStatus==='recording') {this.setData({voiceStatus:'transcribing'});this.recorder.stop();return;}
    if(this.data.busy || this.data.voiceActive || this.pendingChat) return;
    this.setData({privacyPurpose:'voice'});
    if(this.pendingVoice) {voice.removeFile(this.pendingVoice.path);this.pendingVoice=null;}
    this.setData({voiceActive:true,voiceStatus:'authorizing',voiceError:'',voiceCanRetry:false});
    try {
      if(!wx.getStorageSync('voiceConsentSiliconFlowV1')) {
        const accepted=await new Promise(resolve=>wx.showModal({title:'语音转文字',
          content:'录音将经云端发送至硅基流动进行文字转写，本小程序不保存原始音频。最长60秒，转写后由你确认再发送。',
          confirmText:'继续',success:r=>resolve(r.confirm),fail:()=>resolve(false)}));
        if(!accepted) {this.setData({voiceActive:false,voiceStatus:'idle'});return;}
        wx.setStorageSync('voiceConsentSiliconFlowV1',true);
      }
      await voice.permission();
      if(!this.voiceAlive || this.voiceHidden) {this.setData({voiceActive:false,voiceStatus:'idle'});return;}
      if(!this.recorder) this.recorder=voice.createRecorder({
        state:(stage,seconds)=>{if(this.voiceAlive)this.setData({voiceStatus:stage,voiceSeconds:seconds,voiceActive:stage==='recording'});},
        error:message=>{if(this.voiceAlive)this.setData({voiceStatus:'failed',voiceActive:false,voiceError:message});},
        file:path=>{
          this.pendingVoice={path,request_id:Date.now().toString(36)+'_'+Math.random().toString(36).slice(2,12),draft:this.data.input};
          return this.retryVoice();
        }
      });
      this.recorder.start();
    } catch(e) {this.setData({voiceActive:false,voiceStatus:'failed',voiceError:e.message});}
  },
  async retryVoice() {
    if(!this.pendingVoice || this.data.voiceStatus==='uploading') return;
    this.setData({voiceStatus:'uploading',voiceActive:true,voiceError:''});
    const pending=this.pendingVoice;
    pending.draft=this.data.input;
    try {
      const id=await api.goal();
      const audio=await voice.readAudio(pending.path);
      const text=await api.transcribe(id,{request_id:pending.request_id,audio_base64:audio,format:'mp3'});
      if(!this.voiceAlive) return;
      const draft=(pending.draft ? pending.draft+'\n' : '')+text;
      const limit=this.data.replyMode==='case'?6000:this.data.replyMode==='essay'?600:2000;
      if(draft.length>limit) throw new Error('输入框内容较长，请先整理原文字，再重试这段录音。');
      this.setData({input:draft,voiceStatus:'ready',voiceActive:false});
      voice.removeFile(pending.path);this.pendingVoice=null;
    } catch(e) {if(this.voiceAlive)this.setData({voiceStatus:'failed',voiceActive:false,voiceError:e.message,voiceCanRetry:true});}
  },
  cancelVoice() {
    if(this.recorder) this.recorder.cancel();
    if(this.pendingVoice) voice.removeFile(this.pendingVoice.path);
    this.pendingVoice=null;this.setData({voiceActive:false,voiceStatus:'idle',voiceError:'',voiceCanRetry:false});
  },
  voiceSettings() {wx.openSetting({});},
  openPrivacy() {if(wx.openPrivacyContract) wx.openPrivacyContract({fail:()=>wx.showToast({title:'暂时打不开，请稍后再试',icon:'none'})});},
  agreePrivacy() {if(this.privacyResolve)this.privacyResolve({buttonId:'voice-privacy-agree',event:'agree'});this.privacyResolve=null;this.setData({privacyOpen:false});},
  rejectPrivacy() {if(this.privacyResolve)this.privacyResolve({event:'disagree'});this.privacyResolve=null;this.setData({privacyOpen:false});},
  help() {this.closeSheet();this.showDialog('关于无极架构笔记','从每天一个小任务开始。选择题选好后确认；案例支持分段语音转写，确认文字后评分；论文选择 DOCX、文字版 PDF 或 TXT，可先选一道仿真题再批改。AI 估分仅供练习参考，批改和学习记录保存在当前账号。');}
});
