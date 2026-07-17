---
title: 技术平台
module: 07-tech-platform
status: completed
created: 2026-07-16
---

# 技术平台

本模块为加速进化（Booster Robotics）技术平台的完整文档，涵盖 SDK、开发工具、训练框架、部署方案等核心内容。

## 文档索引

| 文档 | 说明 |
|------|------|
| [_tech-overview.md](_tech-overview.md) | 技术平台全景 |
| [booster-sdk.md](booster-sdk.md) | BoosterOS SDK 文档 |
| [ros2-sdk.md](ros2-sdk.md) | ROS2 SDK 文档 |
| [booster-gym.md](booster-gym.md) | Booster GYM 强化学习框架 |
| [booster-studio.md](booster-studio.md) | Booster Studio 一体化开发平台 |
| [booster-train.md](booster-train.md) | Booster Train 训练框架 |
| [booster-deploy.md](booster-deploy.md) | Booster Deploy 部署工具 |
| [doubao-integration.md](doubao-integration.md) | 豆包大模型集成 |
| [robocup-demo.md](robocup-demo.md) | RoboCup Demo 开源方案 |
| [dev-onboarding.md](dev-onboarding.md) | 开发者入门指南 |

## 技术栈概览

```
┌─────────────────────────────────────────────────────┐
│                   Booster Studio                     │
│          (一体化 Agent 开发平台，虚拟仿真+真机)        │
├─────────────────────────────────────────────────────┤
│  BoosterOS SDK  │  ROS2 SDK  │  豆包大模型 API       │
├─────────────────────────────────────────────────────┤
│  Booster GYM    │  Booster Train   │ Booster Deploy  │
│  (强化学习)     │  (Isaac Lab)     │  (Sim2Real)     │
├─────────────────────────────────────────────────────┤
│              K1 / T1 机器人硬件平台                   │
└─────────────────────────────────────────────────────┘
```

## 使用指南

- **新开发者**：从 dev-onboarding.md 开始，按推荐路径学习
- **SDK 使用者**：直接查阅 booster-sdk.md 和 ros2-sdk.md
- **算法研究员**：重点阅读 booster-gym.md、booster-train.md、booster-deploy.md
- **应用开发者**：关注 booster-studio.md、doubao-integration.md、robocup-demo.md
