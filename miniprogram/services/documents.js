const LIMIT=2*1024*1024;
function choose() {
  return new Promise((resolve,reject)=>wx.chooseMessageFile({count:1,type:'file',extension:['docx','pdf','txt'],
    success(result) {
      const file=result.tempFiles && result.tempFiles[0];
      if(!file) {resolve(null);return;}
      if(!/\.(docx|pdf|txt)$/i.test(file.name || '') || file.size>LIMIT) {
        reject(new Error('请选择 2 MB 以内的 DOCX、文字版 PDF 或 TXT。'));return;
      }
      resolve({name:file.name,path:file.path,size:file.size});
    },fail(error) {if(/cancel/i.test(error.errMsg || ''))resolve(null);else reject(new Error('未能选择文件，请稍后再试。'));}
  }));
}
function read(file) {
  return new Promise((resolve,reject)=>wx.getFileSystemManager().getFileInfo({filePath:file.path,success(info) {
    if(info.size>LIMIT) {reject(new Error('请选择 2 MB 以内的论文文件。'));return;}
    wx.getFileSystemManager().readFile({filePath:file.path,encoding:'base64',success:r=>resolve(r.data),
      fail:()=>reject(new Error('文件已失效，请重新选择。'))});
  },fail:()=>reject(new Error('文件已失效，请重新选择。'))}));
}
module.exports={choose,read};
