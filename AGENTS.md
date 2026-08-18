# AGENTS.md — 面向 AI Agent 的知识库使用指南

> 本文件是**给 AI Agent（Codex、Claude Code、WorkBuddy 等）看的**，不是给人看的。
> 当你在本项目内执行任何任务前，请先读本文件 + 根 `README.md`，快速建立对知识库的整体认知。
> 本仓库是加速进化（Booster Robotics）课程设计岗位的知识库，用于支撑客户项目方案与课程设计。

---

## 0. 一句话定位

这是一个**课程设计知识库**：一端沉淀公司能力（产品/技术/方案），一端沉淀教育体系（理论/课程/教学），通过交叉引用打通，支撑面对客户时快速构建课程设计方案。

## 1. 仓库结构速览

```
booster-knowledge-base/
├── README.md              # 给人看的导航入口（先读）
├── AGENTS.md              # ← 本文件，给 Agent 看的指南
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

## 2. 快速导航（按任务类型）

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

## 3. 三条硬性规则（务必遵守）

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

## 5. 当前进行中的工作（2026-08 上下文）

- **X 课程**（高职 BoosterOS SDK 实训实操基础课，8 单元 × 32 课时）：处于**开发执行阶段**，已独立为 `05-internal-materials/vocational-planning/03_X课程项目/`，采用 **Jupyter Notebook 单一源文件工作流**（`.ipynb` 导出即实训手册）。
  - 最新大纲：`X课程大纲-v4.md`；最新计划：`X课程开发计划-v3.md`（5 阶段流水线，开发周期至 2026-10-20）
  - 实验代码：`03_X课程项目/notebooks/`（U1-L1/U1-L2 已产出）
  - 开发规则：`02_共创规则与上下文/notebook开发规则.md`
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
