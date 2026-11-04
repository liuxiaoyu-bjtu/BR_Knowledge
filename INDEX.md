---

> **足球单目几何迁移（2026-11-03）**：[说明与产物](04-shared/sdk-tests/足球坐标只读测试/单目几何测试说明.md)。按用户要求沿用工训课chapter12底部取点、相机射线与地面求交，OS SDK负责取数和检测。原高度来自/head_pose与相机外参，没有写死90cm；保留旧位姿入口，完整相机到身体TF入口另补镜头离地高度。仅有头部帧时明确缺少身体参考。独立v0.2.0工具包、9格/3代码Notebook及20项离线检查完成；原始现场文件保留，未运行机器人、修改正式课程或确认踢出。

> **足球坐标首份回读（2026-11-03）**：[说明与产物](04-shared/sdk-tests/足球坐标只读测试/结果回读/球位_20261103_113057_624030_回读.md)。用户首份快照检测与TF取得，球面RMS约11.49cm、同点云平面RMS约1.11cm，原[3.072,-0.207,-0.526]米拒用。用户补充球直径约20cm、身高90cm，2.5米从脚底量起；不能把trunk.x与脚底量测直接相减当定位误差。深度工具v0.1.1增加fit_rejected与独立诊断值，19项离线检查通过，未新增机器人运行或课程确认。

> **足球坐标只读测试（2026-11-03）**：[只读测试程序、Notebook与工具包](04-shared/sdk-tests/足球坐标只读测试/README.md)用于核对Ball框→深度球心→TF→trunk候选坐标，自动保存原始数据和卷尺偏差。无需教师JSON，无运动/踢球调用；0.001深度比例、配准及控制原点待核实。16项离线检查通过，未运行机器人或新增课程确认。

> **足球策略与SDK封装复核（2026-11-03）**：[策划案第17节](05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划/K1足球全流程_OSSDK策划案.md)补充新旧策略、教师JSON可选性及SDK分工/冗余审核，保留开发者连续供数仿真案例。v0.1.1修正合法零坐标被拒绝，37项离线检查通过；0的特殊含义、近脚持续供数及踢后退出待核实，未运行机器人或新增课程确认。

> **U4后三课P4（2026-11-02）**：用户明确确认U4-L2、L3、L4的P2、P3通过，三课③④登记；L2此前第16、19格待办按本次P2确认收口，不编造测试输出。三份P4逐页大纲已完成，28/27/29页，共84页，待确认⑤；覆盖90格、30代码格、9项目标、12项检查点、12道思考和9道评价。Notebook及生成器未改，P5未启动。当前24课教学设计、24课PPT内容大纲、21课PPTX。[逐页大纲与覆盖检查](05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U4-L2-L3-L4_P4覆盖检查记录.md)。下方旧待补验、待④及产物数量保留原日期含义，以本条与当前逐课表为准。

> **全课评价补齐与U4后三课P3（2026-10-30）**：32课已核对，补齐15课独立学习评价，统一19课检查点并分开思考题；U4-L1、U5-L1～L3的教学设计、大纲和PPTX已联动，新增评价页后为28/28/29/29页。U4-L2～L4三份45分钟P3教师稿已完成，L3/L4待④；L2第16、19格仍待定向真机补验，③未登记，本稿先供审阅。原代码与执行信息保留，未运行机器人，P6仍待全课程结束统一导出。 现有24课教学设计、21课PPTX。[逐课补项及P3覆盖](05-internal-materials/vocational-planning/03_X课程项目/实验验证/全课学习评价补齐与U4后三课P3覆盖记录.md)。


> U4-L2/L3/L4 P2 / 确认②③ / 行走中断停止 / 两格定向补验：[统一审定](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U4-L2-L3-L4_P2复核与定稿记录.md)（2026-10-30；L3/L4通过，L2获批修订待补验）。

> U4-L3用户简化稿 / 跟随参数 / STEP重排 / L4连续到位与致意交接：[回读与同步](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U4-L3_回读审查与L4同步.md)（2026-10-30；22/31格、8/13代码；P1待①②）。

> U7-L1能力选择 / 需求到技术方案 / 感知选型 / 一次读取与轮询订阅：[本轮修订](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U7-L1_能力选择与初步方案修订.md)（2026-10-30，21格/8代码；U7四课66格/26代码，八课109格/39代码；P1待①②）。

> U7九处sss反馈 / U8项目逻辑 / u8_team_template / x_lab / 文件重载与逐模块测试：[学材补全与附件说明](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U7_U8_学材补全与附件说明.md)、[U8实施与真机测试](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U8_逐课实施与真机测试指导.md)（2026-10-29，八课103格/37代码，P1待①②）。下方101格/36代码为此前版本统计。
title: "全局关键词索引"
category: "导航层"
tags: ["索引", "搜索", "关键词"]
status: completed
last_updated: "2026-09-01"
---

# 全局关键词索引

> **OS SDK足球全流程策划（2026-11-02）**：能力迁移映射 / 单文件k1_soccer.py / 先转头后转身 / 标准流程图 / 球心与地面平面 / 当前身体坐标 / U7分支交接：[详细策划案](05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划/K1足球全流程_OSSDK策划案.md)。附4幅图与程序草案；32项离线检查通过，未做新方案真机验证。

> K1信息与状态实测 / 28坐标系 / 22关节 / 2传感器 / 10动作 / code100 / 缓存步态：[K1专用补充](01-booster-kb/07-tech-platform/booster-sdk-k1-info-state.md)、[原始结果](04-shared/sdk-tests/K1信息状态测试结果/K1信息状态_20261102_154403_101875/采集汇总.md)（SDK1.2.2；七项返回，robot_info失败，固件本次未取得）。

> 足球SDK完整能力 / 第4轮回读 / 四方法实际调用 / None返回 / 运动响应未等于踢出 / U7课程边界：[第4轮回读与课程边界](05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球SDK完整测试_回读与U7课程边界.md)、[已回填记录](05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球测试_第4轮_操作与记录.md)（2026-11-02；构造与四方法已调用、参数异常符合预期；用户观察到调整，完整踢出及视觉米制来源未证实）。

> 足球逐轮测试 / 静止检测 / 有球无球 / 自动统计与现场记录：[第1轮操作与记录](05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球测试_第1轮_操作与记录.md)、[配套测试Notebook](05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球测试_第1轮_静止检测.ipynb)（2026-10-30；先做第1轮，助手读记录后再安排下一轮；已替代旧分级计划和探查Notebook）。

> 足球SDK能力探查 / 球位坐标 / 像素米制映射 / 单应标定 / 定位测试验收：[联合审核](05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球方案联合审核_SDK能力与教学边界.md)、[第1轮操作与记录](05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球测试_第1轮_操作与记录.md)、[第1轮测试Notebook](05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球测试_第1轮_静止检测.ipynb)（2026-10-30；先核实本机SDK能力，固定映射为候选；全部真机项目待执行）。

> U4移动目标跟随 / 框高阈值 / 跟进与暂停 / 接待到位 / 机器人位移方向：[L3/L4新稿与验证](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U4-L3-L4_视觉移动跟随重设与验证.md)（2026-10-29；视觉控制、IMU/odom记录；新代码待①②）。

> U4课间承接 / 框高启动与停止阈值：[L3/L4同步审查](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U4-L3-L4_承接新版L2的同步审查.md)；U7逐格真机测试 / 足球动态标定 / 线程退出：[四课测试指导](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U7_逐课真机测试指导.md)（2026-10-29；未新增确认）。

> U4-L2重开发 / 行进速度比较 / 框高反比例估距 / 视觉停止阈值：[第五部分与后续Phase依据](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U4-L2_重开发回读与第五部分同步.md)（2026-10-29；36格/10代码，生成器同步，未新增真机确认）。

> X课程v5 / 多传感器融合与多模态 / 自动踢球 / 机器人坐标 / U8导览踢球二选一：[v5大纲](05-internal-materials/vocational-planning/03_X课程项目/X课程大纲-v5.md)、[八课P1与验证清单](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U7_U8_v5重构与验证清单.md)（101格/36代码格；32课主Notebook；①②待完成）。旧U7与U8准备记录保留历史含义。

> U7/U8内容重叠 / U8-P1准备 / 模块接口与验收 / 视觉踢球前置：[边界排查](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U7-L4与U8_内容边界排查.md)、[四课开发准备](05-internal-materials/vocational-planning/03_X课程项目/U8-P1开发准备.md)（2026-10-28；准备完成，U8学生稿尚未产出；U7 Notebook未改）。

> U5-L4与U6五课P4 / 逐页大纲 / 全格与评价覆盖：[P4审阅入口](05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U5-L4_U6_P4覆盖检查记录.md)（④已通过；28/28/25/27/26页，待⑤；含全部96格、20代码格及逐题映射）。

> X课程当前进度 / 32课阶段 / 确认节点 / 正式版与待补附件：[逐课进度总表](05-internal-materials/vocational-planning/03_X课程项目/X课程当前进度.md)。U1-L1的⑥通过已补记；文件存在与阶段确认分开统计。

> U6动作录制与回放 / 视频动作训练 / imretarget / 动作工坊与Booster Train / 混合动作编排：[重构与SDK核验](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U6_单元重构与动作编排核验.md)（2026-10-28更新；四课P2及④通过，P4大纲完成待⑤；L3现有资源调用示例，L4基础混编尚未接入工坊资源）。

> U4距离实验 / 框高估距 / 框面积与距离 / 指定位移 / U4与U7分工：[L2～L4复评与文字校对](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U4-L2-L4_距离实验复评与文字校对.md)（2026-10-26；策略2主线建议、官方SDK核验、42格文字修订，实验结构与代码未变）。

> 按关键词首字母排序，快速定位到对应文档。

## A

| 关键词             | 相关文档                                                        |
| --------------- | ----------------------------------------------------------- |
| AI教育政策          | `02-embodied-ai-edu/06-policy/national-ai-policy.md`        |
| Agent Framework | `01-booster-kb/07-tech-platform/booster-agent-framework.md` |
| AgentBase       | `01-booster-kb/07-tech-platform/booster-agent-framework.md` |
| API接口           | `01-booster-kb/07-tech-platform/booster-sdk.md`             |
| AGENTS 指南        | `AGENTS.md`                                                 |
| Agent 使用指南     | `AGENTS.md`                                                 |
| 公司知识库总览       | `01-booster-kb/_index.md`                                   |

## B

| 关键词 | 相关文档 |
|--------|----------|
| 百城万校 | `01-booster-kb/01-company/milestones.md` |
| Booster K1 | `01-booster-kb/02-products/booster-k1.md` |
| Booster Studio | `01-booster-kb/07-tech-platform/booster-studio.md` |
| Booster T1 | `01-booster-kb/02-products/booster-t1.md` |
| BoosterOS | `01-booster-kb/07-tech-platform/booster-sdk.md` |
| Booster Agent Framework | `01-booster-kb/07-tech-platform/booster-agent-framework.md` |
| booster_agent_framework | `01-booster-kb/07-tech-platform/booster-agent-framework.md` |
| Booster GYM | `01-booster-kb/07-tech-platform/booster-gym.md` |

## C

| 关键词 | 相关文档 |
|--------|----------|
| COCO 80 类（default 检测模型） | `01-booster-kb/07-tech-platform/booster-sdk.md#33-可用检测模型与类别能力` |
| 程昊 | `01-booster-kb/01-company/team.md` |
| 传感器 | `01-booster-kb/02-products/booster-k1.md` |

## D

| 关键词 | 相关文档 |
|--------|----------|
| 豆包大模型 | `01-booster-kb/07-tech-platform/doubao-integration.md` |

## F

| 关键词 | 相关文档 |
|--------|----------|
| FAQ | `01-booster-kb/06-sales-support/faq.md` |
| 福布斯AI TOP50 | `01-booster-kb/01-company/trust-assets.md` |

## G

| 关键词 | 相关文档 |
|--------|----------|
| 高中课程 | `01-booster-kb/03-solutions/k12-high.md` |
| 高职课程 | `02-embodied-ai-edu/03-curriculum/_curriculum-overview.md#高职课程线调研--开发执行` |
| 高职调研报告 | `05-internal-materials/vocational-planning/01_官方文件/2026-07-29_高职具身智能课程开发知识库与系统调研报告.md` |
| 高职应用开发大纲 | `05-internal-materials/vocational-planning/03_X课程项目/高职应用开发大纲-修订版.md` |
| 工具清单 | `04-shared/tools/_index.md` |
| 临时任务记录 | `98-临时任务记录/README.md` |

## H

| 关键词 | 相关文档 |
|--------|----------|
| 海淀联赛 | `01-booster-kb/04-competitions/haidian-league.md` |
| 合作伙伴 | `01-booster-kb/01-company/trust-assets.md` |

## I

| 关键词 | 相关文档 |
|--------|----------|
| ICC赛事 | `01-booster-kb/04-competitions/_competition-overview.md` |

## J

| 关键词 | 相关文档 |
|--------|----------|
| 教师培训 | `01-booster-kb/03-solutions/teacher-training.md` |
| 师资培训沙龙（2026-09） | `05-internal-materials/training-materials/师资培训沙龙-2026-09/内容摘要.md`（K1 硬件/实操/软件/人才需求/课程体系；含上午+下午 PDF） |
| 教育解决方案 | `01-booster-kb/03-solutions/_solution-overview.md` |
| 竞品分析 | `01-booster-kb/08-competitive-analysis/_competitive-overview.md` |
| 具身智能教育 | `02-embodied-ai-edu/01-theory/what-is-embodied-ai-edu.md` |
| 具身智能应用开发（高职） | `05-internal-materials/vocational-planning/03_X课程项目/高职应用开发大纲-修订版.md` |
| 具身智能机器人实践（X课程） | `05-internal-materials/vocational-planning/03_X课程项目/X课程大纲-v5.md`（最新版；历史版v3/v4同目录） |
| X课程开发计划 | `05-internal-materials/vocational-planning/03_X课程项目/X课程开发计划-v4.md`（最新版；v1–v3 同目录） |
| X课程实验代码 | `05-internal-materials/vocational-planning/03_X课程项目/notebooks/` |
| X课程动作来源（示教器、行为克隆、模仿学习与强化学习） | `05-internal-materials/vocational-planning/03_X课程项目/notebooks/U6-L1_动作的来源.ipynb` |
| X课程实训手册/大纲嵌入 | `05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md` |
| 教学体例配色（PPT） | `05-internal-materials/vocational-planning/03_X课程项目/PPT视觉配色规范.md`（科技蓝=知识、青绿=实践、橘黄=思考/评价/总结、红=安全） |
| 去AI化表达记录 | `05-internal-materials/去AI化表达记录.md`（"AI 味"表述风格规则） |
| X课程教学设计 | `05-internal-materials/vocational-planning/03_X课程项目/教学设计/`（教师用 .md） |
| X课程PPT | `05-internal-materials/vocational-planning/03_X课程项目/PPT/`（+ `PPT内容设计/`） |
| X课程实训手册 | `05-internal-materials/vocational-planning/03_X课程项目/实训手册PDF/` |
| notebook 开发规则 / P2 审定 / 真机验证 | `05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md`（P1 含实验设计；①设计审阅、②用户真机验证；连续 P1–P6，确认①～⑥独立编号；P2 有问题先确认方案，无问题提示可进入 P3） |

## K

| 关键词 | 相关文档 |
|--------|----------|
| K-12课程体系 | `02-embodied-ai-edu/03-curriculum/_curriculum-overview.md` |
| K1 通识课（L1-L4） | `02-embodied-ai-edu/03-curriculum/k1-通识课/README.md` |
| K1 图形化编程工具前置调研 | `98-临时任务记录/20260903-BoosterStudio工具设计前置材料/01-BoosterStudio图形化编程工具前置调研与产品设计建议.md` |
| 课程库/教案 | `05-internal-materials/course-outlines/` |
| 课程标准 | `02-embodied-ai-edu/02-standards/k12-ability-map.md` |
| 客户案例 | `01-booster-kb/05-cases/_cases-index.md` |

## L

| 关键词 | 相关文档 |
|--------|----------|
| L1-L4 通识课 | `02-embodied-ai-edu/03-curriculum/k1-通识课/README.md` |
| 里程碑 | `01-booster-kb/01-company/milestones.md` |

## P

| 关键词 | 相关文档 |
|--------|----------|
| Python编程 | `01-booster-kb/07-tech-platform/booster-sdk.md` |
| Python Agent开发 | `01-booster-kb/07-tech-platform/booster-agent-framework.md` |

## Q

| 关键词 | 相关文档 |
|--------|----------|
| 起航计划 | `01-booster-kb/01-company/milestones.md` |
| 强化学习 | `01-booster-kb/07-tech-platform/booster-gym.md` |
| 清华工训中心课程（分析） | `02-embodied-ai-edu/03-curriculum/k1-通识课/清华工训中心课程.md` |
| 清华工训课 18 章全文 | `05-internal-materials/course-outlines/清华工训课-18章/` |
| 清华工训课 实验代码索引 | `05-internal-materials/course-outlines/清华工训课-18章/实验代码索引.md` |

## R

| 关键词 | 相关文档 |
|--------|----------|
| RoboCup | `01-booster-kb/04-competitions/robocup.md` |
| RoBoLeague | `01-booster-kb/04-competitions/roboleague.md` |
| ROS2 | `01-booster-kb/07-tech-platform/ros2-sdk.md` |
| 融资 | `01-booster-kb/01-company/profile.md` |

## S

| 关键词 | 相关文档 |
|--------|----------|
| 深度图示意（近白远黑、同距同灰度） | `05-internal-materials/vocational-planning/03_X课程项目/PPT/U3_Codex源文件/assets/U3-L1-p19/README.md` |
| SDK | `01-booster-kb/07-tech-platform/booster-sdk.md` |
| SDK测试 | `04-shared/sdk-tests/_README.md` |
| 视觉检测模型 | `01-booster-kb/07-tech-platform/booster-sdk.md#33-可用检测模型与类别能力` |
| UI组件系统 | `01-booster-kb/07-tech-platform/booster-agent-framework.md` |
| 实验室建设 | `01-booster-kb/03-solutions/lab-construction.md` |
| 双减政策 | `02-embodied-ai-edu/06-policy/national-ai-policy.md` |

## T

| 关键词 | 相关文档 |
|--------|----------|
| 团队介绍 | `01-booster-kb/01-company/team.md` |
| 图形化编程 | `02-embodied-ai-edu/03-curriculum/programming-track/_index.md` |
| 图形化编程工具 | `98-临时任务记录/20260903-BoosterStudio工具设计前置材料/01-BoosterStudio图形化编程工具前置调研与产品设计建议.md` |

## W

| 关键词 | 相关文档 |
|--------|----------|
| 文档模板 | `04-shared/templates/doc-template.md` |

## X

| 关键词 | 相关文档 |
|--------|----------|
| 信任状 | `01-booster-kb/01-company/trust-assets.md` |
| 销售支持 | `01-booster-kb/06-sales-support/_sales-overview.md` |
| 选型决策 | `01-booster-kb/02-products/version-comparison.md` |
| 学-练-赛-评 | `01-booster-kb/03-solutions/_solution-overview.md` |
| X 课程（具身智能机器人实践） | `05-internal-materials/vocational-planning/03_X课程项目/X课程大纲-v5.md` |
| X 课程开发计划 | `05-internal-materials/vocational-planning/03_X课程项目/X课程开发计划-v4.md` |
| X 课程实验代码 | `05-internal-materials/vocational-planning/03_X课程项目/notebooks/` |
| X课程 U5-L4 / U6 P3 / 教学设计 / 确认④ / 全格覆盖 | [五课教学设计及覆盖检查](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U5-L4_U6_P3教学设计覆盖检查记录.md)（五份45分钟教师稿；P2通过、P3待④；含取消终态与现场表现、训练等待、附件及补做安排） |
| X课程 PPT 制作与图示验收 / PPT Master 方法借鉴 | `05-internal-materials/vocational-planning/03_X课程项目/PPT制作与图示验收规范.md`（延续 U1 视觉规则、按内容选构图、关键图示规格、素材溯源与逐页验收；附官方版本与来源） |
| X课程 U7 / 去AI化 / 阅读衔接 / Python cell分格 / bottle / 线程收尾 / 小剧场 | [修订与分格核查](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U7_修订与分格核查记录.md)（2026-10-28；90格、32代码格；原33项逐条处理，时间戳条件待核；四课P1修订稿待①②） |
| X课程 U3 P4 / PPT内容大纲 / 覆盖检查 | `05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U3_P4覆盖检查记录.md`（四课大纲入口、42个代码格与15道评价题覆盖、真机补验范围；待确认⑤） |

## 临时任务记录

| 关键词 | 相关文档 |
|---|---|
| 98 临时任务记录 | `98-临时任务记录/README.md` |
| BoosterStudio 图形化编程工具 | `98-临时任务记录/20260903-BoosterStudio工具设计前置材料/README.md` |
| Booster Educational IR | `98-临时任务记录/20260903-BoosterStudio工具设计前置材料/02-Booster-Educational-IR设计思考与目的.md` |
| 积木工具框架选型 | `98-临时任务记录/20260903-BoosterStudio工具设计前置材料/01-BoosterStudio图形化编程工具前置调研与产品设计建议.md` |

## Z

| 关键词 | 相关文档 |
|--------|----------|
| 中国科技馆 | `01-booster-kb/05-cases/case-cstm.md` |
| 中高职方案 | `01-booster-kb/03-solutions/vocational.md` |
| 状态机/FSM | `05-internal-materials/vocational-planning/03_X课程项目/高职应用开发大纲-修订版.md#模块-4状态机与任务流程4-课时` |
| 综合项目（视觉踢球） | `05-internal-materials/vocational-planning/03_X课程项目/高职应用开发大纲-修订版.md#模块-7综合项目开发与展示5-课时` |

## 周末项目课

| 关键词 | 入口 |
|---|---|
| K1周末班 / 少年机器人创作社 / 初中混合基础 / 两小时周末课 / 机器人作品 / 招生宣介 | [课程总纲与招生宣介](05-internal-materials/course-outlines/K1周末创作班/课程总纲与招生宣介-v1.md) |
| 周末班实施 / 分层创作 / Agent作品出口 / 动作创作条件 | [设计依据与实施口径](05-internal-materials/course-outlines/K1周末创作班/设计依据与实施口径.md) |
