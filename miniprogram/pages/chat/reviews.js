const api=require('../../services/api');
const documents=require('../../services/documents');
const requestId=()=>Date.now().toString(36)+'_'+Math.random().toString(36).slice(2,12);
module.exports={
  practiceAction(e) {
    const type=e.currentTarget.dataset.type;
    if(type==='case')return this.startCase();
    if(type==='essay')return this.chooseEssay();
    return this.startOne();
  },
  async startCase() {
    if(this.data.busy || this.data.voiceActive || this.pendingChat)return;
    if(this.pendingReview){this.showDialog('先完成上次批改','可以重试上次批改，或先将它放下，再开始新的练习。');return;}
    this.closeSheet();if(this.data.replyMode==='chat')this.chatDraft=this.data.input;
    this.exitReply();this.setData({busy:true,error:'',screen:'home',showWelcome:false});
    try {
      const id=await api.goal(),result=await api.request(`/v1/goals/${id}/case`,'POST');
      const key='case_'+result.case.issue_id;
      let messages=this.data.messages;
      if(!messages.some(m=>m.id==='a'+key))messages=messages.concat({id:'u'+key,role:'user',text:'练一道案例'},
        {id:'a'+key,role:'assistant',...result});
      this.caseStarted=Date.now();
      this.setData({messages,scrollTarget:'a'+key,caseTask:result.case,replyMode:'case',voiceStatus:'idle',
        input:this.caseDraft && this.caseDraft.issue===result.case.issue_id?this.caseDraft.text:''});
    }catch(e){this.setData({error:e.message});}finally{this.setData({busy:false});}
  },
  async caseReply(e) {
    const item=this.data.messages[e.currentTarget.dataset.index];
    if(!item || !item.case || this.data.busy || this.data.voiceActive)return;
    if(item.case.completed)return this.startCase();
    if(this.pendingReview){this.showDialog('已有一份批改待完成','请先重试或放下上次批改。');return;}
    if(this.data.replyMode==='chat')this.chatDraft=this.data.input;
    this.caseStarted=Date.now();
    this.setData({caseTask:item.case,replyMode:'case',essayFile:null,
      input:this.caseDraft && this.caseDraft.issue===item.case.issue_id?this.caseDraft.text:''});
    return this.toggleVoice();
  },
  async chooseEssay() {
    if(this.data.busy || this.data.voiceActive || this.pendingChat)return;
    if(this.pendingReview){this.showDialog('先完成上次批改','可以先重试或放下上次批改，再上传另一篇文稿。');return;}
    this.closeSheet();this.setData({privacyPurpose:'essay'});
    try {
      if(wx.requirePrivacyAuthorize)await new Promise((resolve,reject)=>wx.requirePrivacyAuthorize({success:resolve,
        fail:()=>reject(new Error('隐私授权未完成，文件尚未上传。'))}));
      const file=await documents.choose();
      if(!file || this.reviewClosed)return;
      if(this.data.replyMode==='chat')this.chatDraft=this.data.input;
      else if(this.data.replyMode==='case' && this.data.caseTask)this.caseDraft={issue:this.data.caseTask.issue_id,text:this.data.input};
      if(this.pendingVoice)this.cancelVoice();
      this.setData({screen:'home',showWelcome:false,replyMode:'essay',essayFile:file,essayTopic:null,caseTask:null,input:'',error:'',voiceStatus:'idle'});
    }catch(e){this.setData({error:e.message});}
  },
  async openEssayTopics() {
    if(this.data.busy || this.data.voiceActive || this.pendingReview)return;
    try {
      const id=await api.goal(),result=await api.request(`/v1/goals/${id}/essay-topics`);
      this.setData({essayTopics:result.topics || []});
      this.openSheet('essayTopics','选择论文仿真题');
    }catch(e){this.setData({error:e.message});}
  },
  pickEssayTopic(e) {
    const topic=this.data.essayTopics.find(t=>t.id===e.currentTarget.dataset.id);
    if(!topic)return;
    this.closeSheet();this.setData({essayTopic:topic,input:''});
  },
  clearEssayTopic() {this.setData({essayTopic:null});},
  exitReply() {
    if(this.data.voiceActive)return;
    if(this.data.replyMode==='case' && this.data.caseTask)this.caseDraft={issue:this.data.caseTask.issue_id,text:this.data.input};
    if(this.pendingVoice)this.cancelVoice();
    if(this.data.replyMode!=='chat')this.setData({replyMode:'chat',caseTask:null,essayFile:null,essayTopic:null,input:this.chatDraft || '',voiceStatus:'idle'});
  },
  async submitReview() {
    if(this.data.busy || this.data.voiceActive || this.pendingReview || this.reviewPreparing)return;
    const kind=this.data.replyMode,answer=this.data.input.trim(),file=this.data.essayFile;
    if(kind==='case' && (!this.data.caseTask || !answer))return;
    if(kind==='essay' && !file)return;
    this.reviewPreparing=true;
    try {
      if(!wx.getStorageSync('reviewConsentSiliconFlowV1')) {
        const accepted=await new Promise(resolve=>wx.showModal({title:'提交作答与文稿批改',
          content:'作答或文稿文字将发送至硅基流动进行评阅，并保存到你的学习记录；原始文件不保存。建议先隐去真实姓名、单位和敏感项目细节。',
          confirmText:'同意并提交',success:r=>resolve(r.confirm),fail:()=>resolve(false)}));
        if(!accepted)return;
        wx.setStorageSync('reviewConsentSiliconFlowV1',true);
      }
      this.setData({busy:true,error:''});
      const body={request_id:requestId(),kind};
      if(kind==='case')Object.assign(body,{issue_id:this.data.caseTask.issue_id,answer,
        duration_seconds:Math.min(10800,Math.max(0,Math.floor((Date.now()-(this.caseStarted || Date.now()))/1000)))});
      else if(this.data.essayTopic)Object.assign(body,{filename:file.name,file_base64:await documents.read(file),topic_ref:this.data.essayTopic.id,prompt:''});
      else Object.assign(body,{filename:file.name,file_base64:await documents.read(file),prompt:answer});
      if(this.reviewClosed)return;
      this.reviewDraft={kind,answer,file,caseTask:this.data.caseTask,essayTopic:this.data.essayTopic};this.pendingReview=body;
      const message=kind==='case'?answer:'上传论文：'+file.name+(this.data.essayTopic?' · '+this.data.essayTopic.title:'');
      const messages=this.data.messages.concat({id:'ureview_'+body.request_id,role:'user',text:message});
      this.setData({messages,scrollTarget:'ureview_'+body.request_id,input:'',replyMode:'chat',caseTask:null,essayFile:null,essayTopic:null,
        reviewPending:true,reviewFailed:false,busy:false,voiceStatus:'idle',voiceError:''});
      await this.deliverReview();
    }catch(e){if(!this.reviewClosed)this.setData({error:e.message,busy:false});}
    finally{this.reviewPreparing=false;}
  },
  async deliverReview(resume=false) {
    if(!this.pendingReview || this.data.busy)return;
    this.setData({busy:true,reviewPending:true,reviewFailed:false,error:''});
    const pending=this.pendingReview,id=typeof pending==='string'?pending:pending.request_id;
    try {
      const goal=await api.goal(),result=await api.review(goal,pending,resume,()=>!this.reviewClosed);
      if(this.reviewClosed)return;
      this.finishReview(id,result);
    }catch(e){
      if(this.reviewClosed)return;
      if([413,422].includes(e.statusCode) && this.reviewDraft) {
        const draft=this.reviewDraft;this.pendingReview=null;this.reviewDraft=null;
        this.setData({messages:this.data.messages.filter(m=>m.id!=='ureview_'+id),replyMode:draft.kind,
          caseTask:draft.caseTask,essayFile:draft.file,essayTopic:draft.essayTopic || null,input:draft.answer,reviewPending:false,reviewFailed:false,error:e.message});
      }else this.setData({reviewPending:false,reviewFailed:true,error:e.message});
    }finally{if(!this.reviewClosed)this.setData({busy:false});}
  },
  finishReview(id,result) {
    const key='areview_'+id;
    let messages=this.data.messages.map(m=>m.case && m.case.issue_id===result.case_issue_id?{...m,case:{...m.case,completed:true}}:m);
    if(!messages.some(m=>m.id===key))messages=messages.concat({id:key,role:'assistant',...result});
    this.pendingReview=null;this.reviewDraft=null;this.caseDraft=null;
    this.setData({messages,scrollTarget:key,reviewPending:false,reviewFailed:false,replyMode:'chat',caseTask:null,essayFile:null,essayTopic:null,error:''});
  },
  retryReview(){return this.deliverReview(false);},
  async dismissReview() {
    if(!this.pendingReview || this.data.busy)return;
    const id=typeof this.pendingReview==='string'?this.pendingReview:this.pendingReview.request_id;
    this.setData({busy:true});
    try {
      const goal=await api.goal(),result=await api.request(`/v1/goals/${goal}/reviews/${id}/dismiss`,'POST');
      if(result.status==='complete')this.finishReview(id,result.response);
      else {this.pendingReview=null;this.reviewDraft=null;this.setData({reviewFailed:false,reviewPending:false,error:'',
        messages:this.data.messages.filter(m=>m.id!=='ureview_'+id)});}
    }catch(e){
      if(e.statusCode===404){this.pendingReview=null;this.reviewDraft=null;this.setData({reviewFailed:false,reviewPending:false,error:'',
        messages:this.data.messages.filter(m=>m.id!=='ureview_'+id)});}
      else this.setData({error:e.message});
    }finally{this.setData({busy:false});}
    if(!this.pendingReview)await this.loadConversation();
  },
  async restoreReview(goal) {
    if(!api.reviewPending || this.pendingReview || this.reviewClosed)return;
    try {
      const {job}=await api.reviewPending(goal);
      if(!job || this.reviewClosed)return;
      this.pendingReview=job.request_id;
      if(job.status==='pending')await this.deliverReview(true);
      else this.setData({reviewFailed:true,error:'上次批改未完成，原内容还在，可以重试或先放下。'});
    }catch(e){if(!this.reviewClosed)this.setData({error:e.message});}
  },
  toggleReview(e) {
    const index=e.currentTarget.dataset.index;
    this.setData({messages:this.data.messages.map((m,i)=>i===index?{...m,reviewOpen:!m.reviewOpen}:m)});
  }
};
