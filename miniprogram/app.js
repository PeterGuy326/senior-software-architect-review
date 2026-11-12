App({
  globalData: { theme: 'system' },
  onLaunch() { this.globalData.theme = wx.getStorageSync('appearance') || 'system'; }
});
