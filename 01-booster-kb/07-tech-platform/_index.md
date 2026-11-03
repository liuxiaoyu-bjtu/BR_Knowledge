---
title: 技术平台
module: 07-tech-platform
status: completed
created: 2026-07-16
---

# 技术平台

> **足球策略与SDK封装复核（2026-11-03）**：[策划案第17节](../../05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划/K1足球全流程_OSSDK策划案.md)补充新旧策略、教师JSON可选性及SDK分工/冗余审核，保留开发者连续供数仿真案例。v0.1.1修正合法零坐标被拒绝，37项离线检查通过；0的特殊含义、近脚持续供数及踢后退出待核实，未运行机器人或新增课程确认。

> **OS SDK足球全流程策划（2026-11-02）**：[课程策划与应用草案](../../05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划/K1足球全流程_OSSDK策划案.md)提供旧SDK到OS SDK映射、单文件状态机/选球/定位/退出和4幅图。属于课程应用，不计作SDK新增API；32项离线检查通过，真机视觉定位和踢出仍待核实。

本模块为加速进化（Booster Robotics）技术平台的完整文档，涵盖 SDK、开发工具、训练框架、部署方案等核心内容。

## 文档索引

| 文档                                                       | 说明                                                                 |
| -------------------------------------------------------- | ------------------------------------------------------------------ |
| [_tech-overview.md](_tech-overview.md)                   | 技术平台全景（含产品架构图）                                                     |
| [booster-sdk.md](booster-sdk.md)                         | **BoosterOS SDK V1.0** — 主 SDK 完整 API 参考（41 接口 + 5 独立模块 + 22 数据类型） |
| [booster-sdk-k1-info-state.md](booster-sdk-k1-info-state.md) | K1八项信息状态接口实测：全部名称/字段；7项返回、robot_info报code=100，SDK1.2.2，2026-11-02 |
| [booster-agent-framework.md](booster-agent-framework.md) | **Booster Agent Framework** — App 端高层应用开发框架（UI 组件/生命周期/参数系统/状态订阅）  |
| [ros2-sdk.md](ros2-sdk.md)                               | ROS2 SDK 文档                                                        |
| [booster-studio.md](booster-studio.md)                   | **Booster Studio** — 具身智能原生 IDE（仿真/Vibe Coding/实时可视化/Sim-to-Real/云桌面） |
| [hichat.md](hichat.md)                                   | **HiChat** — 语音对话 Agent（人设系统/多轮对话/灯语反馈）                            |
| [motion-creator.md](motion-creator.md) | **Motion Creator动作工坊** — 视频骨架提取→imretarget重定向→Booster Train强化学习训练（2026-10-26用户更新）；Studio实践已纳入X课程U6-L3，导出与新SDK入口测试中 |
| [product-ecosystem.md](product-ecosystem.md)             | **产品生态体系** — App/技能库/加速豆/账号/AI 助手/应用中心/文档中心                        |
| [booster-gym.md](booster-gym.md)                         | Booster GYM 强化学习框架                                                 |
| [booster-train.md](booster-train.md)                     | Booster Train 训练框架（BeyondMimic）                                    |
| [booster-deploy.md](booster-deploy.md)                   | Booster Deploy 部署工具                                                |
| [doubao-integration.md](doubao-integration.md)           | 豆包大模型集成                                                            |
| [robocup-demo.md](robocup-demo.md)                       | RoboCup Demo 开源方案                                                  |
| [dev-onboarding.md](dev-onboarding.md)                   | 开发者入门指南                                                            |

## 技术栈概览

```
┌──────────────────────────────────────────────────────────────────┐
│                      Booster Studio                              │
│   仿真 · Vibe Coding · 实时可视化 · Sim-to-Real · 云桌面 · AI 助手 │
├──────────────────────────────────────────────────────────────────┤
│  BoosterOS SDK │ Booster Agent Framework │ ROS2 SDK │ 豆包 API   │
├──────────────────────────────────────────────────────────────────┤
│  Booster GYM   │ Booster Train (Isaac Lab) │ Booster Deploy      │
├──────────────────────────────────────────────────────────────────┤
│  Booster App · 技能库 · 加速豆 · 账号体系 · 应用中心 · 文档中心    │
├──────────────────────────────────────────────────────────────────┤
│                 K1 / T1 / T2 机器人硬件平台                        │
└──────────────────────────────────────────────────────────────────┘
```

## K1实机信息采集

[八项接口K1专用补充](booster-sdk-k1-info-state.md)：K1八项信息状态接口已回读：七项返回，robot_info在GetRobotInfo时报code=100，本次设备身份和固件未取得；公开模式walk、配置步态default，支持步态default/soccer。完整收录28个坐标系、22个关节、2个传感器、10个动作及字段；清单不等于动作执行或任意TF变换通过，不新增课程确认。

## 使用指南

- **新开发者**：从 dev-onboarding.md 开始，按推荐路径学习
- **SDK 使用者**：直接查阅 booster-sdk.md 和 ros2-sdk.md
- **Agent 应用开发者**：查阅 booster-agent-framework.md，了解 UI 组件、生命周期和参数系统
- **算法研究员**：重点阅读 booster-gym.md、booster-train.md、booster-deploy.md
- **应用开发者**：关注 booster-studio.md、booster-agent-framework.md、doubao-integration.md、robocup-demo.md
