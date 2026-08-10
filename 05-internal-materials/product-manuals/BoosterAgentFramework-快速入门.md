# 开发第一个 Booster Agent

> English version: [Develop the first Booster Agent](https://booster.feishu.cn/wiki/BnnNwuzh9iARtQkjHj9c8mkZn7g)
> 
> 

# 开发第一个 Booster Agent

[https://www.bilibili.com/video/BV1fbMx6oE3a/?share_source=copy_web&vd_source=792101f1dec59159be4c87b151c6f399]()

## 模块导言

对于很多机器人开发者而言，开发流程的复杂性是和算法同样巨大的挑战。

传统机器人开发往往需要分别完成环境搭建、代码编写、仿真测试、程序部署以及真机调试等工作。开发者需要频繁切换 IDE、仿真器、终端和机器人控制工具，导致大量时间消耗在工具链配置上。

Booster Studio 提供了统一的 Agent 开发平台，内置 Booster Agent Framework 和仿真环境。开发者可快速创建 Agent、编写行为逻辑、部署到仿真环境并进行调试验证。

本模块将通过一个最简单的机器人 Agent——挥手（Hello World），帮助你快速体验 Booster Studio 中基于 Booster Agent Framework 的 Agent 开发流程，理解 Agent 的基本结构以及构建、部署和运行方式。

> 准备Booster Studio开发环境，可参考：[了解Booster Studio机器人开发工具](https://booster.feishu.cn/wiki/CE0ZwCQOoi7Es0kMzs9c5lrNnui?from=from_copylink)
> 
> Booster Studio [下载地址](https://studio.booster.tech/)
> 
> 

---

## 单元1：创建第一个机器人 Agent

Agent 是机器人的“大脑程序”。无论是控制机器人行走、感知环境，还是参与机器人足球比赛，本质上都是 Agent 能力。Booster Agent Framework 为开发者封装了机器人连接、消息通信、生命周期管理等基础能力，使开发者能够将精力集中在机器人行为逻辑本身，而不必处理大量底层细节。

我们来创建第一个机器人 Agent 吧！

进入 Booster Studio 的欢迎界面，点击创建 Agent。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTJjODEwYmY0ODU0YzM4Njc3MmIyMzIwMTY2NzQxZWNfNGU3ZWVlODlhNDdlZjMwYmViOTMzY2UxZTk2M2ZjMWFfSUQ6NzY1NTEzNTU5MDI3NDQ2OTA3OF8xNzg2MzU0NTk1OjE3ODY0NDA5OTVfVjM)

设置 Agent 名称，项目位置，选择在仿真环境调试使用的虚拟机器人。如果你还没创建过虚拟机器人，可以创建一个，这里以 `Booster K1`为例。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTA3YTdkMjE3ZmZhOWQxODU5YjQ5ZWU3MzUyZDY2ZGJfODcyMTk5MGViYjBiYThkZjFmOGI1ZjVjMGYwYzk1OTVfSUQ6NzY1NTEzNTg4MzA2NzI2NDI0M18xNzg2MzU0NTk1OjE3ODY0NDA5OTVfVjM)

选择`足球场`场景，点击`创建`。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzYxYWM5ODM5ZmM4YzNjMGEyMTYyNzJhOTI1MzcyODNfOGNiZTUyMWRmMTBiYzg2MjlmZjU5MTNmZjczODU5YjdfSUQ6NzY1NTEzNTkzMjQwMDI3NDM4OV8xNzg2MzU0NTk1OjE3ODY0NDA5OTVfVjM)

稍等片刻，仿真环境加载完毕后，我们可以在仿真环境中看到刚刚选择的机器人。同时，左侧项目的代码面板，已初始化了基于`Booster Agent Framework`的示例代码。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YTkyNmIxZjY4MGFjZjVlMTUxN2U1YTc2Y2IxMjE5NTlfOWFhNzAwNDhjOGYyZjkwZjliMzUyOGQ4ZjkyMDhkNTJfSUQ6NzY1NTEzOTg3NDUwMTAyMDg4M18xNzg2MzU0NTk1OjE3ODY0NDA5OTVfVjM)

## 单元2：构建并部署 Agent

在代码面板中选择Agent的入口文件`src/main.py`，找到`on_custom_component_click`函数，增加一行代码：

```Python
self.robot.do_action("hand_wave")
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NWViNzhhN2UwZmM1ODJjNjRiYzViMjg0YjE1ZjVhMGFfMTIyMjU2ZDkyZWExZjhjNGM5MTQ3MTg3NzliYThjYzlfSUQ6NzY1NTEzODgzMTkyNjcyNTU4Ml8xNzg2MzU0NTk1OjE3ODY0NDA5OTVfVjM)

`on_custom_component_click`函数会在Agent启动后，点击自定义按钮时执行。我们加入的代码，是让机器人执行挥手动作。

接下来，我们**保存文件**，点击屏幕顶端的`激活、构建、部署和运行代理`按钮。项目会立刻开始从构建到部署仿真环境的自动化流程。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MGU2ZmY4ODg1YmRjMzViYzM2OWNkNWM5ODQ5NzNmNDJfY2JkOWYxYWRlZjQ4ZDg2NDJjN2MyNGRlNjEwODk0YjNfSUQ6NzY1NTEzODA2MzIyMDAzNDUxMF8xNzg2MzU0NTk1OjE3ODY0NDA5OTVfVjM)

稍等片刻，项目的`build`文件夹中会新增构建出的`.agent`文件，同时此 Agent 也已部署并运行在仿真环境中。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTY1N2UyYjI5Mjc4ZWJjMGZhNzkxYjQ1Y2UyMDZiN2VfMGEwYjZlYzhjY2ZiZmQyNWEwYWU3NjJhN2M1ODE5MzdfSUQ6NzY1NTE0MDQxNTQ5MDY5MDI4M18xNzg2MzU0NTk1OjE3ODY0NDA5OTVfVjM)

我们进入已自动开启的仿真环境，左上角即对应了当前正在调试的 Agent。我们首先点击机器人，将机器人的模式调整为walk模式。

刚刚修改了点击`自定义按钮`触发的函数。这里点击测试一下，可以看到机器人开始执行挥手动作，向你问好：Hello World！

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjM2ODFmZDRjYzA0NmIwMTJlYjllNTJiMTYyZDY3YjBfNzJiNWY0YzU4ZTkzNTFhMDM3MjZhMDM0YmE1NTUzYWRfSUQ6NzY1NTE0MDEyNTA2NDY0NTYwMV8xNzg2MzU0NTk1OjE3ODY0NDA5OTVfVjM)

## 单元3：Agent开发流程

一个复杂的 Agent 中，可能包含运动控制、环境感知、任务决策、多机器人协同等多个功能模块。然而，无论功能如何变化，开发过程通常遵循相同的工作流：修改代码、构建 Agent、部署 Agent、运行验证，并根据运行结果持续迭代优化。

在 Booster Studio 中，开发者首先在项目中编写或修改 Agent 逻辑。Agent 可以理解为机器人行为的载体，开发者编写的各种控制逻辑、感知逻辑和决策逻辑都会被组织到 Agent 中。代码修改完成后，Agent构建管道会自动检查项目依赖，并将源代码打包为可部署的 Agent 文件。相比传统机器人开发中繁琐的编译与打包流程，使用Booster Studio的开发者无需关注复杂的底层细节。

构建完成后，Agent 可以直接部署到仿真环境中运行。部署过程会自动完成 Agent 安装与启动，使最新版本的代码立即生效。开发者可以在仿真环境中观察机器人的行为表现，验证功能是否符合预期。例如本课程中的挥手动作，就是通过修改代码、构建部署并在仿真环境中验证效果完成的。

当 Agent 行为与预期不符时，开发者只需返回代码继续修改，然后再次构建、部署和验证。机器人开发很少能够一次完成，更多时候是在不断迭代中逐步完善功能。因此，快速完成“修改—部署—验证”的循环，对于提升开发效率至关重要。

Booster Agent Framework 与 Booster Studio 的组合简化这一开发流程。框架负责提供机器人控制接口、事件机制以及运行时管理能力，而 Booster Studio 则负责构建、部署和调试流程。开发者可以将更多精力放在机器人行为设计上，而不必花费大量时间处理环境配置、工程管理和部署细节。

## 总结

在本模块中，你完成了第一个机器人 Agent 的开发。

虽然 Agent 只实现了一个简单的挥手动作，但你已经体验了完整的机器人开发流程：创建 Agent、修改代码、构建部署以及运行验证。与传统机器人开发相比，Booster Studio 将环境管理、代码开发、仿真验证以及真机部署统一到同一个平台。Booster Agent Framework 为机器人开发提供了统一的运行架构和丰富的机器人接口，使开发者能够专注于行为逻辑设计，而无需处理复杂的底层系统细节。

