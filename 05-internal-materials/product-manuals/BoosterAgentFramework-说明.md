---
title: "Booster Agent Framework 原始文档备份"
category: "内部资料"
tags: ["Agent Framework", "应用开发", "API文档", "备份"]
source: "Booster 官方技术文档"
status: completed
last_updated: "2026-08-10"
---

# Booster Agent Framework 原始文档备份

本目录下三份文档为 Booster Agent Framework 的官方原始技术文档，作为知识库一手信息来源存档。

## 文档清单

| 文件名 | 原始文件名 | 内容概述 |
|--------|-----------|----------|
| `BoosterAgentFramework-概述.md` | 了解Booster Agent Framework.md | 框架定位、架构设计、核心概念（AgentBase 生命周期、UI 组件系统、参数配置、状态订阅、回调机制）、与 BoosterOS SDK 的层级关系 |
| `BoosterAgentFramework-快速入门.md` | 开发第一个 Booster Agent.md | 从零搭建 Agent 项目：环境准备、项目结构、UI 页面开发、生命周期实现、构建部署、调试技巧的完整教程 |
| `BoosterAgentFramework-Python-API参考.md` | Booster Agent Framework Python API.md | 完整 Python API 参考：8 大子系统全部接口、参数类型、返回值、回调签名、线程模型、最佳实践 |

## 技术定位

```
应用层:  Booster Agent Framework (booster_agent_framework)
         UI 组件 / 生命周期 / 参数 / 状态订阅
              ↕ call_booster_interface_api()
驱动层:  BoosterOS SDK (boosteros)
         传感器 / 运动控制 / AI 检测 / 语音
              ↕
硬件层:  K1 / T1 机器人
```

- **Agent Framework** 运行在 App 端，负责 UI 组件、生命周期管理、机器人状态订阅与回调响应
- **BoosterOS SDK** 运行在机器人本体或 PC 端，负责底层传感器读取、运动控制、AI 检测
- 两者通过 `call_booster_interface_api()` 通信，Agent Framework 不直接操作机器人硬件

## 与知识库的关联

| 知识库文档 | 关系 |
|-----------|------|
| `01-booster-kb/07-tech-platform/booster-agent-framework.md` | 基于本备份三份文档系统梳理的核心知识文档 |
| `01-booster-kb/07-tech-platform/booster-sdk.md` | 底层 BoosterOS SDK 文档，Agent Framework 的下层依赖 |
| `01-booster-kb/07-tech-platform/_tech-overview.md` | 技术平台全景，Agent Framework 位于应用框架层 |

## 课程设计意义

- SDK 课程教的是**底层能力**（传感器读取、运动控制、视觉检测）
- Agent 框架课程教的是**应用开发**（UI 组件、生命周期、状态订阅）
- 课程有明确因果顺序：先 SDK 后 Agent Framework
