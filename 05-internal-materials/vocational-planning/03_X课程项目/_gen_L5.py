# -*- coding: utf-8 -*-
"""U2-L1 实训手册生成器（单源，与 notebooks/U2-L1_ROS2通信基础.ipynb 对齐）。
重新运行本脚本将覆盖生成该 ipynb。
内容依据：X课程大纲-v4（U2-L1）、教案_L4_05_ROS2入门、清华工训课 Chapter_04。
SDK 事实：ROS2 humble；图像话题真实名 /boostercamera/head/rgb（以 ros2 topic list 实际为准）。
观测方式：命令行四件套（大纲要求）+ Booster Studio 图形组件对照（混合设计）；发布/订阅体验用 Studio 发布 + 命令行观察，不混写 Python。
BoosterStudio 组件术语（官方）：【机器人】页面 → 添加组件；「话题」是与「组件」并列的功能按钮，不是组件；发消息用「发布」组件，订阅看消息用「原始消息」组件。
【2026-09-04 回写】以 notebook 现状为准反向重建（用户 09-04 手动精修版：4.3 改用「原始消息」组件订阅演示 Subscription count 0→1；安全提示拆条；命令说明改列表；「话题」表述改为「机器人」面板 → 打开「话题」，符合官方页面结构）。
【2026-10-09 再回写】notebook 已定稿，生成器落后 1 处措辞（cell 24，4.3 的说明句现状更完整：
  「在 Booster Studio 的「组件」里选择「原始消息」，在“设置按钮”中把订阅的话题设为
  /greeting_u2l1」），以 notebook 为准对齐。此后纳入 _diffcheck_u2.py 常态对账。
【2026-10-20 回写】U2 全单元标题与去 AI 表达复审（用户指令）。本课改 5 处：
  2.3 标题压缩为「发布与订阅（C03、C04）」、3.4「抓一条消息」、4.3「多加一个订阅者」、
  删「问题来了：」、cell 2「公共邮箱」句改陈述。格数仍 31。
【2026-10-20 P4对照复审回写】修订顺序阻塞、节点与进程、ROS2定位和QoS表述；补全消息与频率的观测步骤、实际端点记录及评价。31格（21 Markdown / 10 code）。保留原有命令和真机输出。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U2-L1_ROS2通信基础.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# U2-L1：ROS2 通信基础
cells.append(md("""# U2-L1：ROS2 通信基础

**课程目标**

1. 能用持续拍照的例子说明：顺序执行的代码为什么需要安排数据传递与其他任务的执行时机。
2. 能解释节点、话题、发布、订阅和消息的关系，并说明发布端与订阅端通过话题名、消息类型及兼容的通信配置交换数据。
3. 能用 `ros2 topic list`、`info`、`echo`、`hz` 查找 K1 的话题，读取消息类型与当前观测到的频率，并判断端点数量能说明什么。
"""))

# 课程大纲映射（审核用）
cells.append(md("""## 课程大纲映射（审核用）

| 轻任务 | 对应位置 | 核心概念 | 轻量概念 |
| --- | --- | --- | --- |
| ① K1 终端：`ros2 topic list` → `hz /boostercamera/head/rgb` → `echo --once` | 三 3.2 / 3.5 / 3.4 | C02 话题、C05 消息 | E01 事件循环 |
| 认识发布/订阅如何协作 | 四 4.1–4.3（Studio 发布 + 命令行观察） | C03 发布、C04 订阅 | E02 回调 |
| 建立多模块通信认知 | 一、二 | C01 节点 | — |

> 本映射块用于大纲审核，导出学生 PDF 时移除。
"""))

# 一、为什么机器人需要 ROS2
cells.append(md("""## 一、为什么机器人需要 ROS2

前几课的 Python 代码按单元格顺序执行。假设在同一条执行线上写下这段程序：

```text
连接机器人()

while True:
    拍照()

# 如果循环一直不退出，下面两行就轮不到执行：
把照片发给视觉模块()
听指令停下()
```

这里的障碍是这段代码的**执行顺序**，不是 Python 文件或进程不能同时处理多件事。可以在一个进程中安排多条执行线，也可以拆成多个进程。真实机器人常把相机、视觉、决策、运动控制等工作分成模块；模块之间需要交换数据。

ROS2 为这些模块提供节点、话题和消息等通信机制。相机模块发图像，视觉模块接收图像并发布识别结果，决策模块再使用识别结果。每个模块仍需安排自己的持续工作和停止条件；ROS2 负责让它们按约定交换消息。

### 1.1 ROS2 与 Ubuntu 的区别

- **Ubuntu** 是操作系统，负责进程、设备等基础资源。
- **ROS2** 的全称是 Robot Operating System 2，名字里有“操作系统”，实际使用时是一套运行在 Ubuntu 等操作系统上的机器人软件框架，提供通信、工具和开发组件。它不替代 Ubuntu。

运行 ROS2 命令时，程序仍由操作系统启动；`ros2 topic list` 读取的是当前 ROS2 环境中可发现的话题。

### 1.2 发布与订阅

相机节点在图像话题上**发布**消息；视觉节点**订阅**同一话题，收到图像后运行处理代码。处理“消息到达”这类事件的函数叫**回调**；让程序持续等待并处理事件的运行过程叫**事件循环**。

发布端无需预先写死某个订阅端的程序地址，双方通过话题名和消息类型对接；实际能否收到，还取决于通信配置是否兼容以及设备、网络是否正常。这种减少双方直接依赖的安排通常叫**解耦**。话题是通信名称，不是集中存放消息的实体邮箱。
"""))

# 二、ROS2 通信五元组
cells.append(md("""## 二、ROS2 通信五元组

### 2.1 节点 Node（C01）

节点是 ROS2 中参与通信的功能单元。例如相机节点发布图像，视觉节点订阅图像并发布识别结果。一个进程可以运行一个或多个节点；节点也可以分布在不同进程或设备上。某个节点出错是否影响其他节点，要看它们是否共用进程和资源，以及系统如何处理故障。

### 2.2 话题 Topic（C02）

话题是带名称的数据通道，适合连续传送图像、识别结果、电池或关节状态等数据。名称用于找到通信对象；消息本身有确定的类型。

### 2.3 发布与订阅（C03、C04）

- **发布**：节点向话题发送消息，一个话题可以有多个发布端。
- **订阅**：节点订阅话题并接收消息，一个话题可以有多个订阅端。
- 发布端不需要在代码中预先指定订阅端；话题名、消息类型以及服务质量（QoS）等配置要能匹配。QoS 是对可靠性、历史消息留存等通信行为的配置，本课先看它会怎样影响观察结果。

### 2.4 消息 Message（C05）

消息是传送的数据，有固定的类型和字段。例如 `std_msgs/msg/String` 有 `data` 字段；`sensor_msgs/msg/Image` 包含图像宽度、高度、编码和数据。下一课再看传感器消息中的具体数值。

订阅端收到消息后，回调才有机会运行。仅看到发布者和订阅者同时存在，还不能确认回调已经收到消息。
"""))

# 三、话题观测四件套
cells.append(md("""## 三、话题观测四件套

下面查看 K1 当前系统里的话题。`list` 找名称，`info` 看类型与端点，`echo` 看收到的消息，`hz` 统计观测到的消息频率。

⚠️ **安全**：这一部分只读系统信息，不发运动或动作指令，无需进入行走模式（WALK）。ROS2 已在本课设备环境中配置好；先确认终端能找到命令。

Booster Studio 的「机器人」面板也能查看话题。下面用命令行查看类型和频率。

### 3.1 确认环境

下面的单元格以 `!` 开头，表示在 Notebook 中执行终端命令。`ROS_DISTRO` 显示当前 ROS2 发行版；`which ros2` 显示命令路径。输出为空时，先请教师检查环境配置。
"""))

# !echo "ROS_DISTRO=$ROS_DISTRO"
cells.append(code("""!echo "ROS_DISTRO=$ROS_DISTRO"
!which ros2"""))

# 3.2 列出话题（list）
cells.append(md("""### 3.2 列出话题（list）

`ros2 topic list` 列出当前 ROS2 环境中可发现的话题，每行一个。观察图像、状态和输入相关的话题名。节点启动状态、网络连接及 ROS_DOMAIN_ID 等环境配置不同，列表和总数也可能不同。
"""))

# !ros2 topic list
cells.append(code("""!ros2 topic list"""))

# 话题多的时候，输出会被折叠，中间出现 `...` 看不全。要确认一共有多少条，在命令后面接上 `| wc -l`…
cells.append(md("""话题多的时候，输出会被折叠，中间出现 `...` 看不全。要确认一共有多少条，在命令后面接上 `| wc -l`，直接输出总行数。"""))

# !ros2 topic list | wc -l
cells.append(code("""!ros2 topic list | wc -l"""))

# 3.3 查看话题详情（info）
cells.append(md("""### 3.3 查看话题详情（info）

`ros2 topic info <话题名>` 显示消息类型（Type）、发布端数量（Publisher count）和订阅端数量（Subscription count）。下面使用本课 K1 上已核对的图像话题 `/boostercamera/head/rgb`；若实际列表中的名称不同，以本机输出为准，并把后续命令中的话题名一并替换。
"""))

# !ros2 topic info /boostercamera/head/rgb
cells.append(code("""!ros2 topic info /boostercamera/head/rgb"""))

# 端点数量描述**命令执行时发现了哪些发布者与订阅者**。例如 `Pub=1, Sub=0` 表示当前发现一个发布…
cells.append(md("""端点数量描述**命令执行时发现了哪些发布者与订阅者**。例如 `Pub=1, Sub=0` 表示当前发现一个发布端、没有订阅端；`Pub=1, Sub=1` 表示两端都存在；`Pub=0, Sub=1` 表示当前只发现订阅端。要判断是否真正收到消息，还需核对类型、QoS、网络，并用 `echo` 或接收端输出验证。

图像话题的 Type 通常为 `sensor_msgs/msg/Image`，以本机实际输出为准。
"""))

# 3.4 抓一条消息（echo --once）
cells.append(md("""### 3.4 抓一条消息（echo --once）

`ros2 topic echo <话题名>` 持续打印收到的消息。`--once` 表示**收到一条后退出**；如果没有收到，它会等待。图像消息的 `data` 数组很长，`--no-arr` 用来隐藏数组内容，便于先读宽度、高度、编码等字段。
"""))

# !ros2 topic echo /boostercamera/head/rgb --once --no-arr
cells.append(code("""!ros2 topic echo /boostercamera/head/rgb --once --no-arr"""))

# 3.5 观测消息频率（hz）
cells.append(md("""### 3.5 观测消息频率（hz）

`ros2 topic hz <话题名>` 根据本机收到的消息估算频率，通常显示 `average rate`。它不是发布端承诺的固定频率；网络或通信配置也会影响观测结果。

命令会持续运行。记录一组输出后，用 Notebook 的「内核 → 中断」或当前界面的停止按钮结束，再运行后面的单元格。
"""))

# !ros2 topic hz /boostercamera/head/rgb
cells.append(code("""!ros2 topic hz /boostercamera/head/rgb"""))

# 四、发布与订阅体验
cells.append(md("""## 四、发布与订阅体验

这次只在自建话题 `/greeting_u2l1` 上发送字符串，观察单次发布和持续发布在 `echo`、`hz` 中的差别；不向机器人发送运动指令。

多组共用同一设备时，先把以下 Studio 配置和所有命令中的话题名统一改为 `/greeting_u2l1_groupN`（N 为组号）。

### 4.1 用 Booster Studio 发布消息

在 Studio 的「发布」组件中设置话题 `/greeting_u2l1`，消息类型选 `std_msgs/String`。JSON 内容为：

```json
{"data": "Hello K1"}
```

点一次「发布」发送一条消息。请保留发布组件；稍后运行 `echo --once` 或 `hz` 时，必要时还要再点「发布」。本课设备曾观察到 Studio 桥接发布端使用历史消息留存配置，晚加入的 `echo` 也可能收到先前的一条。这个现象由发布端及订阅端的 QoS 配置决定，不能推广到所有 ROS2 话题。

### 4.2 用命令行观察

先运行 `info`，记录当前端点数量；数量可能随组件是否仍在运行而改变。
"""))

# !ros2 topic info /greeting_u2l1
cells.append(code("""!ros2 topic info /greeting_u2l1
"""))

# 运行 `echo --once` 等待一条消息。如果命令持续等待，请在 Studio 再点一次「发布」。拿到消息…
cells.append(md("""运行 `echo --once` 等待一条消息。如果命令持续等待，请在 Studio 再点一次「发布」。拿到消息后记录 `data`，不要把它当作“正在持续发布”的证据。
"""))

# !ros2 topic echo /greeting_u2l1 --once
cells.append(code("""!ros2 topic echo /greeting_u2l1 --once
"""))

# 运行 `hz` 后，先等待观察；若没有频率输出，在 Studio 连续点几次「发布」。`hz` 需要接收到多条消…
cells.append(md("""运行 `hz` 后，先等待观察；若没有频率输出，在 Studio 连续点几次「发布」。`hz` 需要接收到多条消息才能估算频率。记录后中断当前命令，再继续下一格。
"""))

# !ros2 topic hz /greeting_u2l1
cells.append(code("""!ros2 topic hz /greeting_u2l1
"""))

# 如果 `hz` 显示 `WARNING: topic ... does not appear to be pub…
cells.append(md("""如果 `hz` 显示 `WARNING: topic ... does not appear to be published yet`，只能说明**这段观测时间里没有收到可供统计的消息**。可能是之前只点了一次发布、话题名改错、发布组件已关闭，或通信配置/网络不匹配。先核对 `info` 和话题名，再在 `hz` 仍运行时从 Studio 连续发布，观察是否出现 `average rate`。

若 `echo --once` 在晚加入后读到先前那条消息，而 `hz` 没得到持续频率，可据此讨论历史消息留存。历史消息是否送达取决于发布端生命周期和双方 QoS 配置；本课不把这一现象当作 ROS2 默认规则。
"""))

# 4.3 增加一个订阅端
cells.append(md("""### 4.3 增加一个订阅端

先确认前面运行的 `echo` 已结束、`hz` 已中断，再用 `info` 记录当前 Subscription count。在 Studio 的「原始消息」组件中订阅 `/greeting_u2l1`，保持组件打开，再运行下面的 `info`。比较**本组操作前后的实际数量**；数量变化受其他正在运行的订阅者影响，不预设一定从 0 变成 1。

发布端无需事先知道具体订阅端是谁。`info` 能显示当前发现的端点数量，但不能单凭这个数字证明消息已经送达；可在 Studio 再发布一条并检查接收组件的显示。
"""))

# !ros2 topic info /greeting_u2l1
cells.append(code("""!ros2 topic info /greeting_u2l1"""))

# 五、观察与记录
cells.append(md("""## 五、观察与记录

| 观察项 | 你的记录 | 判断依据 |
| --- | --- | --- |
| `ros2 topic list` 的话题数 |  | 当前环境中可发现的话题数量 |
| 图像话题 Type 与 Pub/Sub |  | 记录类型和端点数量；它们能否证明消息已送达？ |
| 图像话题 `echo` 与 `hz` |  | 一条消息的宽、高、编码；观测频率和停止方式 |
| 自建话题 `echo` 与 `hz` |  | `data`、是否出现 `average rate`、测试时发布了几次 |
| 增加 Studio 订阅端前后 |  | 两次 Subscription count、是否在组件中收到消息 |
"""))

# 六、检查点、思考题与学习评价
cells.append(md("""## 六、检查点、思考题与学习评价
"""))

# 6.1 分步检查点
cells.append(md("""### 6.1 分步检查点

- [__] `ros2 topic list` 能列出当前话题并数出总数。
- [__] `ros2 topic info /boostercamera/head/rgb` 能读出类型与 Pub/Sub 数，并说明数量的局限。
- [__] `ros2 topic echo --once` 能取得一条图像消息的元信息；等待时知道怎样处理。
- [__] `ros2 topic hz /boostercamera/head/rgb` 能读出观测频率，记录后已中断。
- [__] 自建话题由 Studio 发布，`echo --once` 取得字符串；用多次发布观察 `hz`，结束后已中断。
- [__] 比较增加 Studio「原始消息」订阅端前后的实际数量，并验证组件是否收到新消息。
"""))

# 6.2 思考题
cells.append(md("""### 6.2 思考题

课堂完成第 1、3 题；第 2 题课后验证。

1. Studio 发布组件和 `ros2 topic echo` 分别扮演什么角色？它们还需满足哪些条件，消息才可能送达？
2. 把发布端话题名改成 `/greeting_u2l1x`，订阅端保持不变，再发一条消息。订阅端会收到这条新消息吗？记录你的观察。
3. 如果视觉节点识别出足球，要把结果交给决策节点，至少需要约定哪些信息？试用节点、话题、消息三个词描述。
"""))

# 6.3 学习评价
cells.append(md("""### 6.3 学习评价

**一、判断题**

1. `ros2 topic info` 同时显示一个发布者和一个订阅者，就能证明订阅者已经收到消息。（    ）

**二、填空题**

2. ROS2 中按名字传数据的通道叫 ______，它上面流动的数据有固定的 ______。

**三、选择题**（单选）

3. 已核对话题名和消息类型正确，Studio 发布组件仍打开；本组只点过一次「发布」，随后运行 `ros2 topic hz /greeting_u2l1`，观测期间没有再次发布，也没有得到可统计的频率。下一步最合适的是（    ）
   A. 断定 K1 没有连接
   B. 在 `hz` 仍运行时从 Studio 再连续发布几条，并查看是否出现 `average rate`
   C. 断定 ROS2 总会留存最后一条消息
   D. 将 `hz` 改成图像话题，避开字符串消息

> 参考答案（教师留存，导出学生 PDF 时移除）：
> 1. ×。2. 话题；消息类型。3. B。
"""))


nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
