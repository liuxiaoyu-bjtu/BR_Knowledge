---
title: 技术平台
module: 07-tech-platform
status: completed
created: 2026-07-16
---

# 技术平台

本模块为加速进化（Booster Robotics）技术平台的完整文档，涵盖 SDK、开发工具、训练框架、部署方案等核心内容。

## 文档索引

| 文档                                                       | 说明                                                                 |
| -------------------------------------------------------- | ------------------------------------------------------------------ |
| [_tech-overview.md](_tech-overview.md)                   | 技术平台全景（含产品架构图）                                                     |
| [booster-sdk.md](booster-sdk.md)                         | **BoosterOS SDK V1.0** — 主 SDK 完整 API 参考（41 接口 + 5 独立模块 + 22 数据类型） |
| [booster-agent-framework.md](booster-agent-framework.md) | **Booster Agent Framework** — App 端高层应用开发框架（UI 组件/生命周期/参数系统/状态订阅）  |
| [ros2-sdk.md](ros2-sdk.md)                               | ROS2 SDK 文档                                                        |
| [booster-studio.md](booster-studio.md)                   | **Booster Studio** — 核心开发平台（仿真/Notebook/Agent 部署/云桌面）              |
| [hichat.md](hichat.md)                                   | **HiChat** — 语音对话 Agent（人设系统/多轮对话/灯语反馈）                            |
| [motion-creator.md](motion-creator.md)                   | **Motion Creator** — 动作编辑器（视频→动作，8月 P0 开发中）                        |
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
│   仿真 · Notebook · Agent 部署 · AI 助手 · 云桌面 · 云端仿真      │
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

## 使用指南

- **新开发者**：从 dev-onboarding.md 开始，按推荐路径学习
- **SDK 使用者**：直接查阅 booster-sdk.md 和 ros2-sdk.md
- **Agent 应用开发者**：查阅 booster-agent-framework.md，了解 UI 组件、生命周期和参数系统
- **算法研究员**：重点阅读 booster-gym.md、booster-train.md、booster-deploy.md
- **应用开发者**：关注 booster-studio.md、booster-agent-framework.md、doubao-integration.md、robocup-demo.md
