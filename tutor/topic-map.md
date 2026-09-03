# Topic Map（由脚本生成，请勿手改）

> 由 `python3 scripts/gen_topic_map.py` 从 [`tutor/curriculum.json`](./curriculum.json) 生成。若要修改，请改 curriculum.json 后重跑该脚本。

## 1. 聚合考点（`record --facet` 必填）

| Topic ID | 名称 | Facets |
|---|---|---|
| `K05.TEST_CMMI_PATTERNS` | 软件测试、CMMI 与常见设计模式 | `testing` / `cmmi` / `design_patterns` |
| `K06.DESIGN_DATA_VIEWS` | 概要设计、数据设计与 UML 视图 | `high_level_design` / `data_design` / `uml_views` |
| `K12.PATTERNS_SOA_MICROSERVICES` | 设计模式、SOA 与微服务核心概念 | `design_patterns` / `soa` / `microservices` |
| `K13.VIEWS_SOA_LAYERING` | 4+1 视图、SOA 与分层架构 | `four_plus_one` / `soa` / `layering` |

## 2. 所有考点 → 资源映射

| Topic ID | 名称 | 科目 | 频次 | 时长(分钟) | 有 exam-bank 题 | 主要资源 |
|---|---|---|---|---|---|---|
| `K01.OS_MEMORY_KERNEL` | 操作系统内核、进程与存储管理 | comprehensive | 15 | 120 | ✅ | `exam-bank/02-os-concepts.md`, `cheatsheets/os-concepts.md`, `past-papers/HIGH_FREQ.md` |
| `K02.NETWORK_PROTOCOLS` | 计算机网络与常用协议 | comprehensive/case | 15 | 90 | ✅ | `exam-bank/04-networking.md`, `knowledge-index/04-networking.md`, `notes/19-networking/README.md` |
| `K03.SOFTWARE_DESIGN_UML` | 软件设计、内聚耦合与 UML 建模 | comprehensive/case/essay | 14 | 150 | ✅ | `exam-bank/05-uml.md`, `knowledge-index/05-uml.md`, `past-papers/case-types/04-uml-modeling.md` |
| `K04.ARCH_STYLES_ABSD` | 架构风格、ABSD 与选型 | comprehensive/case/essay | 14 | 120 | ✅ | `exam-bank/10-architecture-styles.md`, `knowledge-index/10-architecture-styles.md`, `past-papers/case-types/03-style-comparison.md` (+1) |
| `K05.TEST_CMMI_PATTERNS` | 软件测试、CMMI 与常见设计模式 | comprehensive/essay | 14 | 120 | ✅ | `exam-bank/07-software-engineering.md`, `exam-bank/13-design-patterns.md`, `cheatsheets/software-engineering-cmmi.md` |
| `K06.DESIGN_DATA_VIEWS` | 概要设计、数据设计与 UML 视图 | comprehensive/case/essay | 12 | 120 | ✅ | `exam-bank/14-absd-views.md`, `knowledge-index/14-absd-views.md`, `cheatsheets/absd-and-adl.md` |
| `K07.REALTIME_EMBEDDED` | 实时系统、嵌入式与调度基础 | comprehensive/case | 11 | 150 | ✅ | `exam-bank/22-embedded.md`, `knowledge-index/22-embedded.md`, `past-papers/case-types/08-embedded-components.md` |
| `K08.SOFTWARE_PROCESS_MODELS` | 软件过程模型、敏捷与 RUP | comprehensive | 11 | 60 | ✅ | `exam-bank/07-software-engineering.md`, `notes/04-software-engineering/README.md`, `cheatsheets/software-engineering-cmmi.md` |
| `K09.QUALITY_SCENARIOS` | 质量属性六元组与质量战术 | comprehensive/case/essay | 11 | 90 | ✅ | `exam-bank/11-quality-attributes.md`, `knowledge-index/11-quality-attributes.md`, `cheatsheets/quality-attributes.md` (+1) |
| `K10.DATABASE_MODELING` | 关系数据库、范式与关系代数 | comprehensive/case | 10 | 150 | ✅ | `exam-bank/03-database.md`, `knowledge-index/03-database.md`, `past-papers/case-types/02-database-design.md` |
| `K11.COMPONENTS_4PLUS1` | 构件平台与 4+1 视图 | comprehensive/case/essay | 9 | 75 | ✅ | `exam-bank/14-absd-views.md`, `knowledge-index/14-absd-views.md`, `notes/06-system-architecture-design/README.md` |
| `K12.PATTERNS_SOA_MICROSERVICES` | 设计模式、SOA 与微服务核心概念 | comprehensive/case/essay | 9 | 150 | ✅ | `exam-bank/13-design-patterns.md`, `exam-bank/15-microservice-cloud-native.md`, `knowledge-index/15-microservice-cloud-native.md` (+1) |
| `K13.VIEWS_SOA_LAYERING` | 4+1 视图、SOA 与分层架构 | comprehensive/case/essay | 8 | 90 | ✅ | `exam-bank/14-absd-views.md`, `exam-bank/26-soa-evolution.md`, `notes/12-case-layered/README.md` (+1) |
| `K14.OS_SCHEDULING_FILES` | 操作系统调度与文件系统计算 | comprehensive | 7 | 120 | ✅ | `exam-bank/02-os-concepts.md`, `cheatsheets/os-concepts.md` |
| `K15.STRUCTURED_ANALYSIS_DFD` | 结构化分析与 DFD | comprehensive/case | 7 | 75 | ✅ | `exam-bank/07-software-engineering.md`, `past-papers/case-types/04-uml-modeling.md` |
| `K16.REQUIREMENTS_MANAGEMENT` | 需求工程、基线与变更管理 | comprehensive/case | 7 | 60 | ✅ | `exam-bank/07-software-engineering.md`, `notes/04-software-engineering/README.md` |
| `K17.IP_COPYRIGHT` | 知识产权、著作权与标准化 | comprehensive | 7 | 30 | ✅ | `exam-bank/06-ip-and-standards.md`, `knowledge-index/06-ip-and-standards.md`, `cheatsheets/ip-and-standards.md` |
| `K18.COMPUTER_ARCH_STORAGE` | 计算机组成与存储层次 | comprehensive | 6 | 90 | ✅ | `exam-bank/01-computer-systems.md`, `knowledge-index/01-computer-systems.md`, `cheatsheets/computer-systems-formulas.md` |
| `K19.ATAM_TACTICS` | ATAM、四类点与质量属性战术 | comprehensive/case/essay | 6 | 90 | ✅ | `exam-bank/12-atam-evaluation.md`, `knowledge-index/12-atam-evaluation.md`, `cheatsheets/architecture-evaluation.md` (+1) |
| `K20.SECURITY_FOUNDATIONS` | CIA、安全服务、STRIDE 与等保 | comprehensive/case/essay | 6 | 120 | ✅ | `exam-bank/21-security.md`, `knowledge-index/21-security.md`, `past-papers/case-types/07-security-architecture.md` (+1) |
| `K21.MESSAGING_CACHE` | 消息中间件、缓存与一致性 | comprehensive/case/essay | 5 | 120 | ✅ | `exam-bank/16-middleware.md`, `exam-bank/18-cache.md`, `knowledge-index/16-middleware.md` (+2) |
| `K22.ENGLISH_READING` | 专业英语阅读与高频词 | comprehensive | 23 | 75 | ✅ | `exam-bank/23-english-reading.md`, `cheatsheets/english-reading.md`, `past-papers/HIGH_FREQ.md` |
| `C01.CASE_ATAM` | 案例主赛道：架构评估与质量属性 | case | 0 | 120 | ⚠️ 无 | `past-papers/CASE_SURVIVAL.md`, `past-papers/case-types/01-architecture-evaluation.md` |
| `C02.CASE_DATABASE` | 案例主赛道：数据库设计 | case | 0 | 180 | ⚠️ 无 | `past-papers/CASE_SURVIVAL.md`, `past-papers/case-types/02-database-design.md` |
| `C03.CASE_MESSAGING_CACHE` | 案例主赛道：消息与缓存 | case | 0 | 150 | ⚠️ 无 | `past-papers/CASE_SURVIVAL.md`, `past-papers/case-types/06-messaging-caching.md` |
| `C04.CASE_MICROSERVICE` | 案例主赛道：微服务拆分与治理 | case | 0 | 180 | ⚠️ 无 | `past-papers/CASE_SURVIVAL.md`, `past-papers/case-types/05-microservice-refactor.md` |
| `P01.ESSAY_ARCHITECTURE` | 论文主题：软件架构设计 | essay | 10 | 300 | ⚠️ 无 | `past-papers/PAPER_SURVIVAL.md`, `past-papers/paper-topics/01-architecture-design.md`, `past-papers/paper-samples/01-architecture-design.md` |
| `P02.ESSAY_BIG_DATA` | 论文主题：大数据与 NoSQL | essay | 10 | 300 | ⚠️ 无 | `past-papers/PAPER_SURVIVAL.md`, `past-papers/paper-topics/06-big-data-nosql.md`, `past-papers/paper-samples/06-big-data-nosql.md` |
| `P03.ESSAY_RELIABILITY` | 论文主题：可靠性与高可用 | essay | 5 | 240 | ⚠️ 无 | `past-papers/PAPER_SURVIVAL.md`, `past-papers/paper-topics/03-reliability-design.md`, `past-papers/paper-samples/03-reliability-design.md` |
| `P04.ESSAY_MICROSERVICE` | 论文主题：微服务与云原生 | essay | 5 | 240 | ⚠️ 无 | `past-papers/PAPER_SURVIVAL.md`, `past-papers/paper-topics/05-microservice-cloud-native.md`, `past-papers/paper-samples/05-microservice-cloud-native.md` |
| `P05.ESSAY_EAI` | 论文主题：企业应用集成 EAI | essay | 5 | 240 | ⚠️ 无 | `past-papers/PAPER_SURVIVAL.md`, `past-papers/paper-topics/11-enterprise-integration.md`, `past-papers/paper-samples/11-enterprise-integration.md` |
| `P06.ESSAY_ATAM` | 论文主题：架构评估 | essay | 3 | 210 | ⚠️ 无 | `past-papers/PAPER_SURVIVAL.md`, `past-papers/paper-topics/02-architecture-evaluation.md`, `past-papers/paper-samples/02-architecture-evaluation.md` |

## 3. 无 exam-bank 题的考点（自编题时 `--source-type self_authored`）

- `C01.CASE_ATAM` — 案例主赛道：架构评估与质量属性
- `C02.CASE_DATABASE` — 案例主赛道：数据库设计
- `C03.CASE_MESSAGING_CACHE` — 案例主赛道：消息与缓存
- `C04.CASE_MICROSERVICE` — 案例主赛道：微服务拆分与治理
- `P01.ESSAY_ARCHITECTURE` — 论文主题：软件架构设计
- `P02.ESSAY_BIG_DATA` — 论文主题：大数据与 NoSQL
- `P03.ESSAY_RELIABILITY` — 论文主题：可靠性与高可用
- `P04.ESSAY_MICROSERVICE` — 论文主题：微服务与云原生
- `P05.ESSAY_EAI` — 论文主题：企业应用集成 EAI
- `P06.ESSAY_ATAM` — 论文主题：架构评估

## 4. exam-bank 文件 → topic 反查

- `exam-bank/01-computer-systems.md` → `K18.COMPUTER_ARCH_STORAGE`
- `exam-bank/02-os-concepts.md` → `K01.OS_MEMORY_KERNEL`, `K14.OS_SCHEDULING_FILES`
- `exam-bank/03-database.md` → `K10.DATABASE_MODELING`
- `exam-bank/04-networking.md` → `K02.NETWORK_PROTOCOLS`
- `exam-bank/05-uml.md` → `K03.SOFTWARE_DESIGN_UML`
- `exam-bank/06-ip-and-standards.md` → `K17.IP_COPYRIGHT`
- `exam-bank/07-software-engineering.md` → `K05.TEST_CMMI_PATTERNS`, `K08.SOFTWARE_PROCESS_MODELS`, `K15.STRUCTURED_ANALYSIS_DFD`, `K16.REQUIREMENTS_MANAGEMENT`
- `exam-bank/10-architecture-styles.md` → `K04.ARCH_STYLES_ABSD`
- `exam-bank/11-quality-attributes.md` → `K09.QUALITY_SCENARIOS`
- `exam-bank/12-atam-evaluation.md` → `K19.ATAM_TACTICS`
- `exam-bank/13-design-patterns.md` → `K05.TEST_CMMI_PATTERNS`, `K12.PATTERNS_SOA_MICROSERVICES`
- `exam-bank/14-absd-views.md` → `K06.DESIGN_DATA_VIEWS`, `K11.COMPONENTS_4PLUS1`, `K13.VIEWS_SOA_LAYERING`
- `exam-bank/15-microservice-cloud-native.md` → `K12.PATTERNS_SOA_MICROSERVICES`
- `exam-bank/16-middleware.md` → `K21.MESSAGING_CACHE`
- `exam-bank/18-cache.md` → `K21.MESSAGING_CACHE`
- `exam-bank/21-security.md` → `K20.SECURITY_FOUNDATIONS`
- `exam-bank/22-embedded.md` → `K07.REALTIME_EMBEDDED`
- `exam-bank/23-english-reading.md` → `K22.ENGLISH_READING`
- `exam-bank/26-soa-evolution.md` → `K13.VIEWS_SOA_LAYERING`

