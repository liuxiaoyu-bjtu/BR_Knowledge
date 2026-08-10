# 了解Booster Agent Framework

# 了解Booster Agent Framework

## 导言

在传统机器人开发流程中，开发者往往需要独自面对复杂的进程间通信（IPC）、繁琐的 ROS2 节点搭建、移动端 UI 开发、线程管理以及设备通信协议解析等问题。

Booster Agent Framework 是为了解决这些痛点而设计的高层 Python 开发框架。它将机器人控制、UI 组件、参数配置、事件处理以及状态管理等能力进行了统一封装，使开发者无需深入了解底层通信细节，即可快速开发功能完整的机器人 Agent。

一个 Booster Agent 可以理解为运行在机器人操作系统中的应用程序。运行后，它不仅能够控制机器人行为，还能够在 Booster Studio 或移动端 App 中自动生成对应的可视化交互界面。

本模块将带你了解 Booster Agent Framework 的核心架构、开发模式和工程组织方式。

---

## 单元1：Booster Agent Frame Work的架构

Booster 智能体生态主要由三部分组成：  

- **移动端**：用户使用的手机 App 负责呈现控制面板，捕获用户的点击或摇杆操作。  

- **通信网关**：移动端与机器人端之间使用协议进行同屏毫秒级的高带宽多模态数据交互。  

- **机器人端**：**Booster Agent Manager** 负责接收移动端信令，并自动通过底层的 ROS2 通信机制调度和管理处于激活状态的各个核心 Agent 进程。这使得开发者完全不需要手写一行底层的 ROS2 节点代码，就能复用前端极其丰富且流畅的 UI 控制能力。 

当用户点击按钮或操作摇杆时，事件首先由移动端产生，通过通信网关发送到机器人端，再由对应的 Agent 进行处理。机器人产生的状态信息、图像数据和组件状态变化，也会通过相同链路实时同步到用户界面。

为了支持 Agent 开发，Booster Agent Framework 提供了多个核心子系统：

- Agent 基类

- UI 组件系统

- 参数管理系统

- 本地存储系统

- 机器人状态系统

- 手柄输入系统

- 日志系统

开发者只需要关注机器人行为逻辑本身，而无需处理底层通信和系统管理工作。

---

## 单元2：实现一个极简的Agent示例

在 Framework 中开发 Agent 遵循固定模式：

1. **导入接口**：`import booster_agent_framework`

2. **继承基类**：实现一个类，继承自 `AgentBase`。

3. **获取指针**：通过 `self` 访问组件、参数和存储管理器。

4. **调用接口**：复写生命周期或绑定回调。

让我们来看一段极简 Agent 代码：

```Python
from booster_agent_framework import (
    AgentBase,
    AgentFeatures,
    DefaultStateIconComponent,
    LocaleString,
)

class MyAgent(AgentBase):
    def __init__(self) -> None:
        super().__init__(AgentFeatures())

        demo_component = DefaultStateIconComponent(
            "demo",
            LocaleString("Demo", "示例"),
            "res/demo.png",
            False,
            self.on_demo_click,
        )
        self.component_manager.add_component(demo_component)

    def on_demo_click(self, component):
        self.logger.info(f"clicked: {component.id}")
        return LocaleString("Clicked", "已点击")

    def on_agent_activated(self) -> None:
        self.logger.info("agent activated")

    def on_agent_close(self) -> None:
        self.logger.info("agent closing")
```

一个完整的 Agent 通常包含三个部分：

- Agent 生命周期管理

- UI 组件定义

- 事件回调处理

用户点击界面组件后，Framework 会自动触发对应回调函数，而开发者只需要在回调中编写业务逻辑即可。

---

## 单元3：Agent 生命周期与回调机制

理解生命周期和回调机制，是掌握 Booster Agent Framework 的关键。

**生命周期**

与脚本不同，Agent 执行完代码后不会立即退出，而是会持续运行在机器人系统中，等待用户操作和机器人状态变化，并响应各种事件。因此，开发 Agent 时需要理解 Agent 的生命周期。

一个 Agent 从启动到退出，通常会经历如下过程：

当 Agent 启动时，Framework 会创建 Agent 实例并完成初始化，随后进入运行状态。运行过程中，Agent 会持续等待各种事件发生，例如用户点击按钮、切换开关、操作摇杆，或者网页组件发送消息等。当这些事件发生时，Framework 会自动调用开发者编写的回调函数来处理对应逻辑。

Framework 提供了生命周期函数，`on_agent_activated()`和`on_agent_close()`。当 Agent 被激活和关闭时，对应函数会自动执行。

`on_agent_activated()`在 Agent 激活后自动执行。开发者通常会在 `on_agent_activated()` 中完成一些初始化工作，例如：创建初始状态、加载配置文件、恢复上次保存的数据、启动后台线程或任务。

`on_agent_close()`在 Agent 关闭前自动执行。通常用于保存运行数据、停止后台线程、释放资源、记录日志。

**回调机制**

除了生命周期回调之外，Agent 运行期间的大部分逻辑都通过事件回调驱动，例如：用户点击按钮、用户切换开关、用户操作摇杆、网页组件发送消息，都会触发对应回调函数。

需要特别注意的是，Booster Agent Framework 的回调函数默认运行在主线程中，并按照触发顺序依次执行。这意味着，如果某个回调长时间阻塞，后续所有回调都必须等待它执行完成。比如：

```Plain Text
def on_button_click(self, component):
    time.sleep(10)
```

在这 10 秒内后续按钮点击无法响应，页面状态无法刷新，App 交互可能出现卡顿。因此在实际开发中，回调函数应尽量快速处理，快速返回。对于耗时任务，应交由独立线程、子进程或外部服务处理。

理解这一机制，对于后续开发复杂 Agent 非常重要。

## 单元4：Agent的工程结构

一个标准的 Booster Agent 工程通常包含如下结构：

```Plain Text
example_agent/ 
├── agent.toml 
├── build.toml 
├── src/ 
│   └── main.py 
├── res/ 
└── build/     
    └── xxx.agent
```

虽然目录看起来较多，但日常开发时真正需要频繁接触的文件并不多。理解每个目录和文件的职责，有助于快速定位代码和资源。

|文件/目录|作用|
|---|---|
|agent\.toml|Agent 的运行配置文件，用于配置 Agent ID、名称、版本号、入口类以及快捷键等基础信息|
|build\.toml|Agent 的构建配置文件，用于配置构建参数和打包选项|
|src/|存放 Agent 核心业务代码，是开发过程中最常修改的目录|
|src/main\.py|Agent 的主入口文件，组件定义、生命周期函数以及事件回调通常都编写在这里|
|res/|存放图片、图标、配置文件等静态资源|
|build/|构建完成后生成的输出目录|
|xxx\.agent|最终生成的 Agent 安装包，可用于部署和分发|

绝大部分代码开发工作都会在 `src/main.py` 中完成。随着项目规模逐渐扩大，也可以将代码拆分到多个 Python 文件中。

当 Agent 构建完成后，生成的 `.agent` 文件会出现在 `build` 目录中。该文件相当于 Agent 的发布包，可以直接部署到仿真环境或机器人系统中运行。

后续学习组件开发、参数配置以及复杂行为逻辑时，了解工程结构有助于更快地找到对应文件的位置并合理设计项目架构。

---

## 单元5：部署与构建Agent

把当前项目构建为Agent，开发者只需要在`Booster Studio`界面顶部点击锤子图案的图标`只构建agent`。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YWExMDcxMmM1MzU0NjE0ODc1YTBkMzY1N2M5Mjg3MTNfMzE0MmU4YzA5MGVlMjhmMmEzMjFkN2FmZDBjN2MwYzRfSUQ6NzY1NTE1NzQ2MjE2MTAzNDQzNF8xNzg2MzU0NTU3OjE3ODY0NDA5NTdfVjM)

构建过程随即开始，构建引擎在后台自动运行。

首先，它会严格扫描并校验 `agent.toml` 中的版本、反向域名 ID 等元数据格式。

随后，构建工具会去解析 `build.toml` 中的平台参数。工具链会根据配置自动前往指定的国内或官方 `pip_repos` 镜像源中下载并打包指定的 `numpy` 等三方科学计算依赖包。

> 如果开发者在 `build.toml` 中配置了 `obfuscation = true`，Studio 会在编译期间自动对核心 `src/` 下的 Python 源码进行轻量级的词法混淆保护，大幅度降低其代码的可读性，从而起到保护知识产权、防止核心控制逻辑被低成本逆向工程的效果。 
> 
> 

最后，输出成果物前，工具链会调起专用的 Agent 签名工具，读取证书文件和环境变量密码，对整包进行国密/安全数字签名。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDIxNThhMGZiMWI1NzY3MGRiNjc0NDI2MjA2OTk2NWZfYjUzMjMyZjAyY2NkOGY3OWU2NDRkY2NhMjFlY2E5MGRfSUQ6NzY1NTE1NzQ2NDIxNTgzMzU1M18xNzg2MzU0NTU3OjE3ODY0NDA5NTdfVjM)

完成构建后，可在项目下的build文件夹中，看到构建好的\.agent文件。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzFlMTdiODAwY2RkNjU1YWJkM2IzMDljNDllMTZiMWRfNjcwOTRiMjJkMzFmNDQwMDZmMmYzYTk3ZTY0MGQ5ZjdfSUQ6NzY1NTE1NzQ2Mjc1MjMzMzAwNV8xNzg2MzU0NTU3OjE3ODY0NDA5NTdfVjM)

> 除了点击锤子图标，你也可以直接在Booster Studio 中点击“一键运行部署”，将其直接推送到当前连接的虚拟机器人或真实硬件上进行真机效果验证。
> 
> 

---

## 单元6：进阶开发能力

除了基础组件（`DefaultStateIconComponent`），Framework 还提供了更丰富的开发能力。

在线网页组件 `OnlineWebviewComponent`允许开发者直接嵌入网页界面。网页中的 JavaScript 可以与 Python Agent 双向通信，从而实现复杂交互界面。适用于：数据大屏、监控面板、地图显示、AI 对话界面。

状态页代理 `ComponentStatePageProxy` 允许根据机器人状态动态切换页面，例如行走模式显示运动控制界面、足球模式显示比赛控制界面、调试模式显示诊断界面。

> 更多细节可参考：[Booster Agent Framework Python API](https://booster.feishu.cn/wiki/JoYXwfPB4iTqhLkCJ0ccgSXunyd?from=from_copylink)
> 
> 

---

## 单元7：Agent开发的最佳实践

对于功能复杂的 Agent ，大多数业务逻辑最终都会演化为以下几种典型模式：

- 按钮触发动作：适用于挥手、起立、坐下等简单功能，或简单功能的组合。

- 按钮更新状态并刷新UI：适用于开关控制、模式切换等场景。

- 按钮触发后台任务：适用于视觉识别、长时间动作序列等耗时工作。

- 状态驱动页面：当机器人状态变化时显示不同组件，使用于复杂 Agent 界面管理。

在使用 Booster Agent Framework 开发时，我们建议遵循以下原则：

- **先验证，再扩展：**每次只增加一个小功能，并立即部署到仿真环境验证结果，避免一次修改过多逻辑导致问题难以定位。

- **保持模块职责清晰：**将运动控制、感知处理、任务决策等逻辑分别组织在不同模块中，降低后期维护成本。

- **优先利用框架能力：**Booster Agent Framework 已经提供机器人控制接口、事件回调机制以及生命周期管理能力。开发过程中应尽量复用框架能力，而不是重复实现底层功能。

## 测验

1. 在 Booster Agent Framework 中，如果在一个按钮的点击回调函数（Callback）中执行了耗时 10 秒的同步阻塞操作，会导致什么后果？ 

A\. 框架会自动将其放入后台线程，没有任何影响 

B\. 阻塞后续的 Python 回调，延迟请求返回，并可能导致前端 App 操作卡顿 

C\. 机器人会切换到安全阻尼模式 

D\. 导致 Python 解释器直接崩溃退出

2. 想要实现“只有当机器人处于特定状态时，才在 App 上显示某一组按钮”，最推荐使用以下哪个组件或系统？ 

A\. StorageManager

B\. OnlineWebviewComponent

C\. ComponentStatePageProxy

D\. AgentFeatures

**答案**：B / C



