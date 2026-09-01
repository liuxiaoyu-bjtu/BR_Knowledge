# AGENTS.md — 面向 AI Agent 的知识库使用指南 + 内容总览

> **本文件是知识库的统一总览入口**。作为新任务/新 Agent，**请先读本文件**——读完即可建立对知识库「有什么、在哪、怎么用」的整体认知，无需遍历全部目录。
> 本文件面向 AI Agent（Codex、Claude Code、WorkBuddy 等）。仓库是加速进化（Booster Robotics）课程设计岗位的知识库，用于支撑客户项目方案与课程设计。
> 如需按关键词检索，用 `INDEX.md`；需架构图看 `KNOWLEDGE-MAP.md`。

---

## 0. 一句话定位

这是一个**课程设计知识库**：一端沉淀公司能力（产品/技术/方案），一端沉淀教育体系（理论/课程/教学），通过交叉引用打通，支撑面对客户时快速构建课程设计方案。

## 1. 仓库结构速览

```
booster-knowledge-base/
├── README.md              # 给人看的导航入口（先读）
├── AGENTS.md              # ← 本文件，给 Agent 看的使用指南 + 内容总览
├── KNOWLEDGE-MAP.md       # 可视化知识地图（架构全貌）
├── INDEX.md               # 全局关键词索引（按需检索）
├── CHANGELOG.md           # 更新日志（记录每次变更）
│
├── 00-navigation/         # L0 导航层：dashboard / glossary / quick-reference
├── 01-booster-kb/         # Core A 公司知识库（8 模块，见其 _index.md）
├── 02-embodied-ai-edu/    # Core B 具身智能教育体系库（6 模块，见其 _index.md）
├── 03-cross-reference/    # 双核映射：product-to-standard / theory-to-product 等
├── 04-shared/             # 共享资源：templates 模板 / tools 工具 / media / sdk-tests
├── 05-internal-materials/ # 内部资料填充区（源文档 + 中间产物 + 课程规划）
└── 99-task-contexts/      # 任务元信息（上下文/提示词/日志），按任务独立成子文件夹
```

## 2. 知识库内容总览（读这一节建立「有什么」的认知）

> 下表是知识库的核心内容盘点。**每个模块的详细目录看对应的 `_index.md`**。表内为「主干文档」路径，非全部文件。

### Core A：公司知识库（`01-booster-kb/`，63 篇）

| 模块 | 收录内容 | 主干入口 |
|---|---|---|
| 01-company 公司概览（5） | 公司信息、发展历程、团队、信任状、品牌故事 | `profile.md` / `trust-assets.md` |
| 02-products 产品矩阵（8） | K1/T1/T2、配件生态、应用矩阵、定价、版本对比 | `_product-overview.md` / `booster-k1.md` |
| 03-solutions 解决方案（11） | 小学/初中/高中/高职/大学、课后、实验室建设、师资培训、竞训 | `_solution-overview.md` / `vocational.md` |
| 04-competitions 赛事（7） | RoboCup、海淀联赛等参赛路径 | `robocup.md` |
| 05-cases 案例库（5） | 客户案例，供方案复用 | `_cases-index.md` |
| 06-sales-support 销售支持（8） | 话术、FAQ、异议处理、报价 | `faq.md` / `elevator-pitch.md` |
| 07-tech-platform 技术平台（14） | **BoosterOS SDK、Agent Framework、Studio、HiChat、Motion Creator、产品生态、ROS2、训练/部署** | `_tech-overview.md` / `booster-sdk.md` |
| 08-competitive-analysis 竞品（5） | 竞品分析与差异化 | `differentiation.md` |

### Core B：具身智能教育体系库（`02-embodied-ai-edu/`）

| 模块 | 收录内容 | 主干入口 |
|---|---|---|
| 01-theory 教育理论（5） | 具身智能教育定义、素养框架 | `what-is-embodied-ai-edu.md` |
| 02-standards 课程标准（2） | K-12 能力图谱、课标对接 | `k12-ability-map.md` |
| 03-curriculum 课程体系 | K-12 四条课程线 + **K1 通识课 L1-L4 落地** | `_curriculum-overview.md` / `k1-通识课/README.md` |
| 04-implementation 实施（2） | 教学指南、安全规范 | `teaching-guide.md` |
| 05-assessment 评估（1） | 评估框架 | `assessment-framework.md` |
| 06-policy 政策（1） | AI 教育政策 | `national-ai-policy.md` |

### 交叉引用与共享层

| 层 | 内容 | 说明 |
|---|---|---|
| 03-cross-reference | 产品↔课标 / 案例↔方案 / 赛事↔课程 / 理论↔产品 4 个映射 | 双核互通桥梁 |
| 04-shared | templates 模板 / tools 工具（含建构笔记、联动规则）/ media / sdk-tests | 共享资源 |
| 05-internal-materials | **源文档 + 中间产物 + 课程规划**（清华工训课 18 章全文、K1 课程库 74 份、X 课程项目） | 一手资料区 |
| 99-task-contexts | 各任务元信息（上下文/提示词/日志） | 挂起任务唤醒入口 |

## 3. 快速导航（按任务类型）

| 任务类型 | 去哪里找 |
|---|---|
| 了解公司整体 / 客户背景 | `01-booster-kb/01-company/` |
| 产品规格与选型 | `01-booster-kb/02-products/` |
| 为客户做教育解决方案 | `01-booster-kb/03-solutions/` + `02-embodied-ai-edu/03-curriculum/` |
| 赛事 / 客户案例 / 销售支持 | `01-booster-kb/04-competitions/`、`05-cases/`、`06-sales-support/` |
| SDK / 开发框架 / 技术平台 | `01-booster-kb/07-tech-platform/`（SDK 见 `booster-sdk.md`） |
| 竞品 | `01-booster-kb/08-competitive-analysis/` |
| 具身智能教育理论 / 标准 | `02-embodied-ai-edu/01-theory/`、`02-standards/` |
| K-12 / 高职课程体系 | `02-embodied-ai-edu/03-curriculum/` + `05-internal-materials/vocational-planning/` |
| 全局搜索关键词 | 用 `INDEX.md` 检索，别盲目翻目录 |
| 被指派了一个"挂起任务" | 去 `99-task-contexts/` 找对应子文件夹，读 `00-任务上下文.md` + `01-执行提示词.md` + `02-产出清单与状态日志.md` |

## 4. 三条硬性规则（务必遵守）

1. **先看 `INDEX.md` / 子模块 `_index.md`，再动手**。本库文档间有大量交叉引用，直接翻文件容易漏。
2. **产出文档必须按规范落到对应模块**，不要乱放。
   - 最终知识沉淀 → `01-booster-kb/` 或 `02-embodied-ai-edu/` 对应子模块
   - 源文档 / 中间产物 → `05-internal-materials/`
   - 任务元信息（上下文/提示词/日志）→ `99-task-contexts/YYYYMMDD-任务名/`
3. **每次改动后必须联动更新**：`CHANGELOG.md`、`INDEX.md`（如涉及新关键词）、受影响模块的 `_index.md`、根 `README.md` 统计（如涉及）。**改动需要 git 提交并推送**。

## 4. 双层技术架构（理解课程设计因果的关键）

课程内容依赖两层技术能力，设计课程时必须理清因果：

| 层 | 载体 | 运行位置 | 职责 | 文档 |
|---|---|---|---|---|
| **底层能力层** | BoosterOS SDK（`boosteros`） | 机器人本体 / PC | 传感器读取、运动控制、AI 检测（41 接口 + 5 独立模块） | `booster-sdk.md`（主 SDK） |
| **上层应用层** | Booster Agent Framework | App 端 | UI 组件、生命周期、参数系统，经 `call_booster_interface_api()` 与 SDK 通信 | `booster-agent-framework.md` |

> SDK V1.0 是未来针对 K1 机器人研发的**主 SDK**，其他版本辅助。后续可能出现 V1.x / Vx 更新，注意以最新主文档为准。

## 5. 当前进行中的工作（2026-09 上下文）

- **X 课程**（高职 BoosterOS SDK 实训实操基础课，8 单元 × 32 课时）：处于**开发执行阶段**，已独立为 `05-internal-materials/vocational-planning/03_X课程项目/`，采用 **Jupyter Notebook 单一源文件工作流**。
  - 最新大纲：`X课程大纲-v4.md`；最新计划：`X课程开发计划-v3.md`（**七阶段流水线 P1-P7**，含 5 道用户确认闸门，开发周期至 2026-10-20）
  - 实验代码：`03_X课程项目/notebooks/`（U1-L1~L4、U2-L1~L3 已产出 7 个）
  - 教学设计/PPT内容/PPT/实训手册：`03_X课程项目/` 下对应子目录（U1-L1~L4 已完成）
  - 开发规则：`02_共创规则与上下文/notebook开发规则.md`（七阶段 + 真机安全约束）
  - PPT 配色：`03_X课程项目/PPT视觉配色规范.md`
  - **重要纪律**：P3→P4、P4→P5、P5→P6 之间必须暂停向用户确认，不得自动连做
- **高职「具身智能应用开发」课程**（7 模块 × 32 课时）：**挂起中**，唤醒入口在 `99-task-contexts/20260806-高职应用开发/`。
- 目录总览见 `vocational-planning/README.md`（01_官方文件 / 02_共创规则与上下文 / 03_X课程项目）。

## 6. 给 Codex 的特别说明

- 本仓库用 Git 管理，远端在 GitHub，改动请 `git commit` + `git push`。
- 沙箱共享：同一项目下的子任务共享本地工作区与 Git 配置，无需重新 clone。
- 若遇到 GitHub 连接异常，优先尝试 GitHub 连接器（MCP）；必要时检查 `/etc/hosts` 是否存在 DNS 劫持条目（github.com → 198.18.x.x）。

## 7. 人读文档 vs 本指南

| 文档 | 读者 |
|---|---|
| `README.md` | 人（含 Agent 起步阶段） |
| `AGENTS.md`（本文件） | **Agent 专属**，持续更新 |
| `KNOWLEDGE-MAP.md` | 人 + Agent 的架构全貌 |
| `INDEX.md` | 检索入口 |
| 各 `_index.md` | 模块入口 |
