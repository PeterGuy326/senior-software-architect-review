# 无极私教小程序界面

原生微信小程序，统一使用腾讯 [TDesign MiniProgram](https://github.com/Tencent/tdesign-miniprogram)，固定版本 `1.17.0`（MIT）。不引入 WebView 或另一套组件库。

## 视觉和交互

- 品牌保留无限环，简化装饰、加粗线条，保证小尺寸可辨识；源文件在 `assets/brand/wuji-avatar.svg`。
- 墨绿为主色，浅色用暖白背景，深色用深绿灰背景。组件颜色由 CSS 变量统一控制，外观可跟随系统或手动切换。
- 首页聚焦“先练一道”和对话输入；历史对话可继续，返回首页不删除记录。
- 图标统一采用 TDesign Icon。按钮、单选、输入框、标签、进度、底部弹层、提示对话框、列表和加载态使用 TDesign 原生组件。
- 单选题确认前可改选，点击“确认答案”才提交；网络失败保持原选择和幂等请求，避免重复记分。
- 语音仍为录音→文字草稿→修改→手动发送。微信隐私授权同意按钮保留原生 `open-type`，首次语音数据处理确认和系统授权使用微信原生提示。
- 进展只展示后端返回的练习数量与学科诊断状态。案例评分、论文批改和其他考试明确标为准备中或规划中。

## 构建

```sh
cd miniprogram
npm ci --ignore-scripts
cd ..
npm run mini:build-ui
npm run test:mini
```

根目录需要先 `npm ci --ignore-scripts` 安装已有 `miniprogram-ci` 工具。Windows UNC 工作区建议在 WSL 内执行上述命令。

`scripts/build_mini_ui.mjs` 调用微信官方 `packNpmManually`，按页面声明递归保留所需组件及公共依赖。生成目录 `miniprogram/miniprogram_npm` 不提交 Git，上传或在开发者工具编译前必须构建。页面使用绝对构建路径，Windows 开发预览目录无需再复制 `node_modules`。

图标字体来自 TDesign 官方 `https://tdesign.gtimg.com/icon/0.4.5/fonts/t.woff`，源文件保存在 `miniprogram/assets/tdesign-icons.woff`。构建时将它嵌入生成的图标 WXSS，消除运行时 CDN 依赖；原始 WOFF 不上传，版权见 `miniprogram/assets/TDESIGN-LICENSE.txt`。升级组件库时应核对图标字体版本和许可。

上传验证需覆盖：浅色和深色首页、历史对话及笔记折叠、选择题改选与确认、底部弹层关闭、真实进度、语音草稿编辑及取消。不要用真实用户账号提交测试答案。
