# 无极私教：小程序首期开发

首期以系统架构设计师打样，已实现原生小程序源码与选择题 API。
云数据库、CLI 授权和开发 API 部署已完成，真实 AppID、微信登录配置和开发者工具登录已就绪。已在模拟器通过真实微信登录、云调用出题、提交判分和进度保存验收；测试作答已清理。已生成真实手机预览二维码，并通过已登录的开发者工具将 0.1.0 开发版本上传到微信平台。用户已确认设为体验版，并反馈手机登录、刷题解析、退出重进后的进度和深浅色切换全部正常；后台体验版状态与手机验收均按用户反馈记录。微信提审与正式发布尚未完成。
当前原生小程序体验版为 0.3.0，已通过微信开发者工具上传。选择题支持确认前改选；真实对话使用硅基流动免费 `Qwen/Qwen3-8B`，云托管版本为 `wuji-coach-dev-008`，`MODEL_FREE_ONLY=true`。聊天持久化、幂等重试及不改写学习成绩均已通过真实线上 API 验证。用户已确认此前手机端能回复、重进后聊天记录仍在，也已确认 0.3.0 手机语音转写、草稿编辑后发送和取消录音全部正常。正式提审与发布尚未完成。
普通对话语音输入已完成真机验收。案例评分、论文上传评分、通知和支付暂未实现，不生成虚假评分或通知回执。

## 环境与工具

工程位于 WSL Ubuntu，项目命令请在 WSL 中运行。

- Node.js 22 与 npm；项目锁定 CloudBase CLI 3.8.11、miniprogram-ci 2.1.31。
- Python >= 3.10，由 `uv sync --frozen` 安装锁定依赖。
- TCCLI 已通过 `uv tool install tccli` 安装在 WSL 用户工具目录。
- Windows 微信开发者工具用于模拟器、扫码与真实项目调试。

```bash
npm ci
uv sync --frozen
npm run check
npm test
npm run test:mini
npm run api:dev
```

API 默认只监听 `127.0.0.1:8421`。`GET /healthz` 检查状态，`/docs` 仅在本地开放。
本地 SQLite 保存到 `.study/cloud-dev/app.db`，与既有 CLI 私人档案分开。
不会读取、迁移或改写已有 `.study/profile.json`、`state.json`、`attempts.jsonl`。

本地测试身份只允许 `APP_ENV=local` 且请求来自本机。云端不提供假微信登录。
`DATABASE_URL` 如另行指定本地 SQLite 文件，也须使用根目录 `.study/` 下的路径。

## 内容与教学引擎

- `exam_packs/ruankao-system-architect/manifest.json` 是首个考试包入口。
- `apps/api/content.py` 通过现有 sanitizer 导入有可靠考点映射的 70 道自编题。
- 英语共享材料暂未接入小程序渲染，因此暂不发布那 5 题。
- 来源仅为 `exam-bank/`；不会扫描 `.study/`、抓取语料或导入第三方真题。
- 发布标识是内容与课程配置的摘要；学习目标固定引用不可变发布版本。
- 题目 ID 是基于既有来源别名的 UUID；文件移位或题号重排前，必须维护别名迁移映射。
- 上线商业使用前，维护者仍须完成所选内容的权属和教学质量审核。

`scripts/tutor.py` 新增纯函数 `recommend_payload()`，CLI 和云端共用排序逻辑。
云端以 `legacy_architect_v1` 为第一种适配器，复用原有掌握度及学习事件计算。
目前三科枚举、75 分制等仍在旧适配器中；新增其他考试应新增适配器，不能冒用架构师规则。
`scripts/grade.py` 的主观题核心算分函数保留，尚未接入云端评分接口。

## 对话与知识存储

云端 PostgreSQL 的 `coach` schema 新增 `knowledge_releases`、`knowledge_chunks` 和 `chat_turns`。知识按独立摘要版本发布，既有题库版本和用户学习目标不变。首批仅索引 `cheatsheets/*.md`、`knowledge-index/*.md` 中的公开笔记（50 文件、510 片段），不读取 `.study/`。这是中文双字及英文词项检索；当前不依赖向量服务，不代表完整教材知识库。

服务端把用户这次消息、最近最多 6 轮已完成对话、必要的学习进度摘要和命中的公开笔记片段发送至硅基流动。微信身份、应用会话、AppSecret、API Key 和逐题原始记录不会加入模型上下文。模型仅能读取当前账号学习摘要、检索笔记、提供开始练习按钮；没有成绩修改、任意 SQL、文件、代码或通知工具。模型解释仍需教学质量验收。

`POST /v1/goals/{id}/chat` 接受 `request_id` 和 `message`，`GET` 同路径恢复最近 10 轮聊天。服务端从会话绑定目标归属，数据库租约避免并发重复生成；同一消息的已完成请求返回原回复。每账号滚动 24 小时最多 50 个新请求，每请求最多 3 次生成尝试，失败可保留原消息重试。聊天不记录作答事件或提升掌握度。

小程序调用 `POST .../chat?async_mode=true`，立即返回待完成状态，再以 `GET .../chat/{request_id}` 取得结果；单次微信调用保持 15 秒以内。模型最多进行一轮工具调用和一轮最终回复，每次上游等待 25 秒。后台生成使用当前进程任务和数据库 120 秒租约，尚不是独立持久任务队列；进程退出后客户端用同一消息 ID 重试，过期租约可重新取得。商业规模部署前需接入独立任务队列和全局用量告警。

模型配置只保存在忽略的 `.env` / `.study/platform/model-input.env` 和云托管环境变量。运行 `npm run model:credentials` 导入，再运行 `npm run knowledge:publish`、`npm run deploy:dev`。运行 `uv run python -m scripts.verify_agent_cloud --deployed` 可用随机测试账号验证真实模型、云端聊天与恢复，然后只清理本次测试账号的数据。

### 免费 GLM 候选接入（未选为默认）

已增加智谱官方接口适配：`MODEL_PROVIDER=bigmodel`、`MODEL_BASE_URL=https://open.bigmodel.cn/api/paas/v4`、`MODEL_NAME=glm-4.7-flash`，使用 `thinking.type=disabled`；该提供商目前拒绝其他型号，避免误用付费的 FlashX。私密候选文件为 `.study/platform/glm-input.env`，候选测试不会修改当前 `.env` 或用户学习记录。

在本人完成智谱登录并将 API Key 填到候选文件后，先执行：

```bash
uv run python -m scripts.evaluate_model --source .study/platform/glm-input.env --label glm
```

该脚本与基准使用相同的 8 个公开合成场景，报告写入 `.study/platform/model-evaluation-glm.json`。人工核对知识解释、未测量状态、练习按钮及拒绝修改成绩等结果，通过后才执行以下激活和部署命令：

```bash
npm run model:credentials -- --source .study/platform/glm-input.env
npm run deploy:dev
uv run python -m scripts.verify_agent_cloud --deployed
```

已取得用户在本机填写的独立 Key，完成 GLM 真实调用。初测暴露了开始练习后模型自行编题并加粗答案的问题，因此引擎已改为：收到有效 `start_practice` 工具调用后直接返回固定按钮文案，不再让模型生成第二段题目内容。此规则对两个提供商均生效。

GLM 免费池在多轮测试中频繁返回 HTTP 429 / `1305`（官方定义为模型当前访问量过大）。增加针对 `1302` / `1305` 的最多两次短暂退避重试后，最新 8 场景仍只完成 5 个，另 3 个持续返回 `1305`；该轮未满足切换条件，因此当时保留了 DeepSeek。基准 8 场景完成 7 个，1 个在 25 秒超时，中位耗时约 10.2 秒。以上完成数只描述当轮请求成功，不代表知识准确率或长期可用率。完整合成记录保存在 `.study/platform/model-evaluation-*.json`。

练习入口防泄题修复已部署到 `006`；91 项本地测试通过，线上知识问答、练习按钮、聊天恢复、幂等重试和不改写成绩已通过合成账号验证，测试账号已精确清理。`/healthz` 现在返回公开的 `agent_provider` / `agent_model` 字段，便于核对实际激活的提供商与型号，不返回任何密钥。

### 后续免费模型筛选

通过当前官方价格页展开条目核对，硅基流动 `Qwen/Qwen3-8B`、`Qwen/Qwen2.5-7B-Instruct` 和 `Qwen/Qwen3.5-4B` 均标注输入、输出免费。实测 `Qwen3.5-4B` 对当前工具调用请求返回 HTTP 400，未选用；Qwen2.5-7B 虽然请求成功，但在初测中绕过练习按钮自行出题，未选用。Qwen3-8B 连续 24 轮请求全部完成，中位耗时约 2.05 秒，最慢约 3.57 秒，且三个“开始练习”场景都返回了有效工具操作。

人工检查发现 Qwen3-8B 仍可能在未提交题目的聊天中透露答案，因此已增加所有模型共用的程序保护：存在未完成练习且用户询问当前题答案，或明确说尚未提交时，先返回确认答案提示与继续练习按钮，不调用模型、不检索答案。聊天上下文最多取最近 6 轮，并增加历史文本 6000 UTF-8 字节预算，以适配轻量模型。进一步强化了不向用户暴露工具名和尊重每日学习时长的提示。

切换配置为 `.study/platform/free-qwen3-input.env`，设置 `MODEL_FREE_ONLY=true`，已激活并部署到 `007`。该模式只允许当前核实并通过评测的免费型号，拒绝付费型号和 Pro 别名，没有自动付费兜底。94 项本地测试通过；独立候选进程连接真实数据库及部署后的真实 API 均通过知识问答、练习操作、聊天保存、幂等和不改写成绩验证，合成测试账号已清理。微信模拟器已收到新模型对 ATAM / SAAM 区别的真实回复。免费标价及平台限额可能调整；上述连续测试是小规模内测证据，不是平台可用性承诺。切换部署及线上验收状态以 `.study/platform/environment.json` 为准。

### 语音转文字

语音输入当前采用固定的硅基流动免费 `XingChenAGI/XingChenASR-V3.2-Ultra`（0.5.0；0.3.0 使用 SenseVoiceSmall），不使用付费语音兜底。当前聊天也是硅基流动，因此共用服务端 Key；若以后聊天换提供商，应另行通过服务端 `ASR_API_KEY` 配置硅基流动密钥，不会把其他提供商 Key 发给硅基流动。

首页输入框左侧点击麦克风开始，再次点击或点「说完了，转文字」结束，最多 60 秒。首次说明音频目的及接收方，再申请微信隐私与麦克风授权。可取消；进入后台时取消正在录制的音频。转写后放入可编辑草稿，用户确认后才发送聊天；不会自动计分或改变掌握度。失败可使用原音频和原请求 ID 重试。

客户端录制单声道 16kHz / 48kbps MP3，通过已认证云托管通道以有大小上限的 Base64 上传。服务端使用固定模型、固定地址，以 multipart 转发音频；验证实际文件格式、0.5–61 秒时长及 512KiB 大小，不接受用户提供的 URL 或模型 ID。音频只在处理内存中存在，不写文件、数据库或对象存储。语音提供商的数据处理另以其服务条款为准。

`coach.voice_jobs` 是第 11 张业务表，只保存归属、请求 ID、音频哈希、状态和短期转写文本。`POST /v1/goals/{id}/voice` 创建任务，`GET /v1/goals/{id}/voice/{request_id}` 轮询。任务复用、归属校验与最多 3 次生成尝试由固定 `coach_voice_rpc` 执行，仅 service_role 可调用。结果 30 分钟后不可读取；后续请求触发清空过期文本，25 小时后清理旧任务。原始音频从不写入任务表，未确认的转写也不写入聊天记录。

`008` 云端已部署，99 项本地测试和真实云端合成中文音频转写、重试复用、不自动发聊天、不改写成绩检查通过。另用离线合成的 MP3 验证了与手机相同格式的解析和真实转写。合成测试没有使用麦克风；其后用户独立在手机确认录音授权、转写为草稿、编辑后手动发送、取消录音全部正常，真机验收来源为用户反馈。微信后台隐私保护指引应包含收集录音的目的及委托硅基流动处理的说明；因后台访问限制，平台配置由管理员本人处理。当前基础库不再接受 `app.json.permission.scope.record` / `__usePrivacyCheck__`，已按实际编译提示移除，运行时通过官方隐私与录音授权 API 处理。

## API 闭环

| 接口 | 用途 |
|---|---|
| `POST /v1/auth/wechat` | 服务端用临时 code 向微信换取身份，再签发应用会话 |
| `POST /v1/auth/local` | 仅本地隔离调试身份；非 local 环境始终拒绝 |
| `GET /v1/exams` | 可用考试及发布版本，不含答案 |
| `POST /v1/goals` | 创建或幂等获取学习目标 |
| `POST /v1/goals/{id}/next` | 取得未完成题目，或按推荐选择下一题 |
| `POST /v1/issues/{id}/answer` | 服务端判分并原子保存事件与状态 |
| `GET /v1/goals/{id}/status` | 当前用户目标的真实进度 |

发题接口采用允许字段清单，答案和解析仅在作答后返回。客户端不能指定分数或用户身份。
同一发题记录重复提交相同答案返回同一结果，冲突提交拒绝。
SQLite 用写事务串行化；PostgreSQL 用用户/目标行锁保护并发写入。
原始学习事件保存于 `learning_attempts`，状态与事件在一个事务中提交。
短练习不生成完整模考分数，不会把一次答对标为稳定掌握。

## 云端部署

1. 腾讯云账号实名，开通 CloudBase PostgreSQL 环境和云托管。
2. 由账号本人确认腾讯云首次服务角色授权。
3. `npm run cloud:login`，在网页完成 CLI 设备授权；`npm run cloud:status` 验证。
4. 从 `.env.example` 复制为 `.env`，在本机填入配置，不要把密钥发到聊天或提交仓库。
5. 获取 `npm run check` 输出的发布 ID，填入 `CONTENT_RELEASE_ID`。
6. 当前免费环境使用 `STORAGE_TRANSPORT=cloudbase_rpc`，运行 `uv run python -m scripts.provision_managed` 安装固定 RPC 并在本机保存服务端密钥。若另用原生 PostgreSQL，则设置 `DATABASE_URL=postgresql+psycopg://...`。
7. `npm run deploy:stage` 可离线检查源码暂存；`npm run deploy:dev` 部署开发服务。
8. 检查 `/healthz`，用真实微信临时 code 完成登录、刷题、重启与进度验收。

部署命令按已安装 CLI 的 `cloudrun deploy --help` 编写，开发环境最小实例 0、最大实例 1。
开通套餐和消费以实际腾讯云页面为准；项目脚本不自动购买套餐、不开自动续费。
原生连接模式首次启动在 PostgreSQL advisory lock 下创建初始表并发布内容；RPC 模式使用已发布内容和版本化 SQL。后续表结构变更必须增加版本化迁移，
不能依赖 `create_all` 做已有列修改；生产发布前另行完善迁移、备份、限流和运维监控。

注意：代码上传可能发生在 Docker 构建之前，所以不能仅依赖 `.dockerignore`。
部署脚本先在 `.study/platform/deploy-<时间戳>/` 构建源码白名单，再让 CLI 上传该目录。
白名单不含 `.env`、学习记录、密钥、Node 依赖或私人题库；Docker 还有第二层白名单。
云端镜像以非 root 用户运行，不使用容器本地磁盘保存学习状态。

### 本账号免费环境的实际开通结果（2026-11-01）

- 上海 PostgreSQL 免费体验环境已创建，0 元，六个月有效期；CLI 授权已完成。
- 环境 ID 与具体到期时间只写本机 `.study/platform/environment.json`，不保存兑换码。
- 当前共享集群在控制台没有内网地址，外网开启入口不可用，不能为当前直连后端提供 `DATABASE_URL`。
- 已实现并接通 `apps/api/managed.py`：通过固定 PostgREST RPC 访问独立 `coach` schema，免费环境不需要原生数据库地址。
- RPC 仅授予 `service_role` 执行权限，匿名与普通用户不能调用。服务端密钥只保存在本机 `.env` 和部署环境，禁止进入小程序。
- 新建的开发密钥有效期 30 天；正式发布前必须安排密钥轮换并重新部署，不能把本次开发密钥视为永久凭据。
- 更新学习状态采用目标行锁和状态比较；答题事件与新状态在同一事务提交。
- 这不影响 CLI 执行管理 SQL；`scripts/publish_cloud_content.py` 已将 70 道自编题发布到独立 `coach` schema。
- `coach` schema 已撤销 PUBLIC 权限，不在默认 `public` PostgREST 暴露范围；没有创建公开答案接口。
- 发布器为选定开发环境限定作用域，并采用不可变内容 ID、幂等批次和 draft/ready 发布标记。
- 可用 `TCB_ENV_ID=<本机环境ID> npm run content:cloud-verify` 独立核验内容与 PUBLIC schema 权限。
- 云托管已由账号本人启用，开发 API 版本 002 已带微信配置部署成功，公网 `/healthz` 与 `/v1/exams` 返回 200；`wechat_ready=true` 仅表示配置齐全，不代表真实微信登录已验收。
- 已通过用户给出的真实 AppID 在开发者工具中完成微信登录和云调用取题，提交答案后服务端判分、学习事件与进度保存均已验证；测试记录按精确 ID 清理并还原初始进度。真机体验与审核发布尚未验收，不要把模拟器和后端部署当作小程序上线。
- 旧版云开发控制台 v1.5.46 仍显示等待资源初始化，但 CLI 环境状态 NORMAL，实际 `wx.cloud.callContainer` 已可访问；不因该提示另建环境。
- 默认公网域名仅供开发测试，平台页面提示存在限频与稳定性限制；手机端优先采用关联环境后的微信云调用通道。
- `npm run cloud:smoke` 已通过真实云 RPC 的出题、判分、并发重试、隔离和匿名拒绝检查。只使用随机临时身份并清理，不读取或迁移已有私人学习记录。此检查在本机执行 API 代码，不能替代部署后 HTTP 与真实微信登录验收。

## 微信小程序预览与体验版

1. 获取真实小程序 AppID，确认操作者具备开发或管理权限。
2. 管理员从微信后台下载代码上传密钥，保存到仓库外；在后台设置 CI 出口 IP 白名单。
3. 服务端 `.env` 保存 AppSecret；小程序客户端禁止保存 AppSecret、数据库或模型密钥。
   可先在本机 `.study/platform/wechat-input.env` 填写 AppSecret 和仓库外上传密钥路径，再运行 `npm run wechat:credentials` 私下导入配置；脚本不会输出密钥值。
4. `.env` 设置 `WECHAT_APP_ID`、`MINIPROGRAM_PRIVATE_KEY_PATH`。默认 `MINI_TRANSPORT=cloud`，同时填写 `TCB_ENV_ID`、`TCB_SERVICE_NAME`。
5. 在 CloudBase 将真实小程序与环境关联，使用 `wx.cloud.callContainer`。此方式无需自有域名；仍使用真实 `wx.login` 临时 code 并由服务端校验身份。若改用 `MINI_TRANSPORT=https`，须填写 HTTPS `API_BASE_URL` 并注册请求合法域名。
6. `npm run mini:configure` 写入公开连接配置，可先在已登录的开发者工具中打开 `miniprogram/`；`npm run mini:preview` 使用 CI 密钥生成 `.study/platform/preview.jpg`，供有权限用户扫码预览。
7. `npm run mini:upload` 上传开发版本；在微信后台设为体验版并添加体验成员。

当前账号未配置 CI 上传密钥，已使用登录后的 Windows 开发者工具完成真实预览和 0.1.0 上传，工具显示「上传成功」。`MINIPROGRAM_PRIVATE_KEY_PATH` 只用于 `miniprogram-ci` 自动上传流程，暂不影响使用已登录的开发者工具上传。后台设为体验版时页面路径为 `pages/chat/index`；预览二维码具有短时有效期，不能当作长期体验版二维码。

预览脚本自动生成被忽略的 `miniprogram/config.local.js`，仅包含公开环境 ID、服务名或 API 地址与 `localDebug:false`。
本地 API 调试可从 `config.local.example.js` 复制配置；只允许回环地址。
默认游客 AppID 是占位值，不能替代真实 AppID 或绕过微信权限，不保证旧版工具能以游客身份编译。
当前项目已替换为用户提供的真实 AppID，工具登录和 AppID 开发权限已验证。旧版 Windows 工具加载 WSL UNC 路径出现异常，调试时使用仅含 `miniprogram/` 的 Windows 本地副本；不要复制服务端 `.env` 或私人 `.study/`。源码仍以仓库为准，副本只用于编译与预览。

若腾讯云账号已通过目标小程序注册，无需再关联其他账号。在开发者工具的云开发控制台中，按「设置 → 环境列表 → 管理我的环境 → 使用已有腾讯云环境」导入已创建的环境，并由管理员按提示验证。参见[官方导入流程](https://docs.cloudbase.net/quick-start/create-env)。不要为此另开一套付费环境或授权微搭代管小程序。

微信后台名称已确定为「无极架构笔记」（2026-11-15，个人性质备案整改口径），最终可用性以平台重名和审核结果为准；整改步骤见 `docs/BEIAN_RECTIFICATION.md`。
原「人人租车网」的名称、类目和备案信息须由管理员在微信后台核对；只改项目源码不等于后台已改名。
用户给出的微信开发者控制台被当前浏览器安全策略阻止访问，因此名称和头像无法代改；不得通过其他浏览器控制方式绕过。头像源文件为 `assets/brand/wuji-avatar.svg`，1024px PNG 位于 `miniprogram/assets/wuji-avatar.png`，页面已使用该图标。

## 当前验证方式

- `npm test`：原有本地教学回归与新增云 API 隔离、幂等、答案隐藏等检查。
- `npm run test:mini`：原生页面事件处理，验证网络重试保持原请求、反馈和主题模式。
- `scripts/verify_postgres.py`：只允许专用本机端口 55432 的一次性数据库，检查并发重试和重启持久化。
- `tests/test_managed_api.py`：设置指向专用本机端口 55439 的 `TEST_DATABASE_URL`，验证实际 PostgreSQL 固定 RPC 的权限、并发与隔离；未配置时跳过。
- `docker build -t wuji-coach:dev .`：检查部署镜像可构建。

小程序脚本测试不等于微信工具编译、真机或平台审核已通过，必须分别验收。

