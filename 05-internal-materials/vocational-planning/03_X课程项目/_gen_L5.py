# -*- coding: utf-8 -*-
"""U2-L1 实训手册生成器（与 notebooks/U2-L1_ROS2通信基础.ipynb 对齐，单源）。
重新运行本脚本将覆盖生成该 ipynb。
内容依据：X课程大纲-v4（U2-L1）、教案_L4_05_ROS2入门、清华工训课 Chapter_04。
SDK 事实：ROS2 humble；图像话题真实名 /boostercamera/head/rgb（以 ros2 topic list 实际为准）。
观测方式：命令行四件套（大纲要求）+ Booster Studio 图形组件对照（混合设计）；发布/订阅体验用 Studio 发布 + 命令行观察，不混写 Python。
表述规范：遵循《去AI化表达记录》（§1–§19）；§一 的引入段采用用户手动修订版。
"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U2-L1_ROS2通信基础.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# # U2-L1：ROS2 通信基础
cells.append(md("""# U2-L1：ROS2 通信基础

**课程目标**

1. 能说明机器人需要 ROS2 的原因：单个程序无法同时处理「边看边想边动」的多模块任务，ROS2 是运行在操作系统之上的通信框架（中间件）。
2. 能列举并解释 ROS2 通信五元组：节点（Node）、话题（Topic）、发布（Publish）、订阅（Subscribe）、消息（Message）。
3. 能使用话题观测四件套（`ros2 topic list` / `info` / `echo` / `hz`）观测 K1 系统中话题的名称、类型与发布频率。
4. 能完成一次发布 / 订阅操作，描述发布者与订阅者「只认话题名、互不相识」的协作方式。
"""))

# ## 课程大纲映射（审核用）
cells.append(md("""## 课程大纲映射（审核用）

| 轻任务 | 对应 cell | 核心概念 | 轻量概念 |
| --- | --- | --- | --- |
| ① K1 终端：`ros2 topic list` → `hz /boostercamera/head/rgb` → `echo --once` | 实验三 3.2 / 3.5 / 3.4 | C02 话题、C05 消息 | E01 事件循环 |
| 认识发布/订阅如何协作 | 实验四 4.1–4.3（Studio 发布 + 命令行观察） | C03 发布、C04 订阅 | E02 回调 |
| 建立「多模块通信」认知 | 实验一、实验二 | C01 节点 | — |

> 本映射块用于大纲对齐审核；导出 PDF 版本时移除此块。（P2 产物）
"""))

# ## 一、为什么机器人需要 ROS2（用户手动修订版为基础）
cells.append(md("""## 一、为什么机器人需要 ROS2

前面几课我们在一个 Python 文件就实现了 K1 的连接、模式切换、速度设定与动作执行，文件中的代码从上往下顺序执行。

可真实任务中的机器人大多需要「边看边想边动」，好几件事一起干。

比如，机器人踢足球的任务中，机器人需要「一直拍照片」，于是你写了个程序，让机器人持续拍照片：

```
连接机器人()

while True:
    拍照()

# 下面这两步永远到不了：
把照片发到网络()
听指令停下()
```

这段程序中，`拍照()` 一执行，程序就永远留在了 `while True` 的循环中。后面的「把照片发到网络」「听指令停下」永远排不上。

问题来了：机器人同一时间要干的远不止拍照，下面这些都在「一直」进行：

- 相机一直出图
- 视觉一直在检测图片里的目标
- 决策一直在算下一步往哪走
- 腿一直在调整姿态保持平衡
- 还要一直听上位机的指令

把这些全写进一个文件、用循环互相嵌套去凑，程序会乱成谁也看不懂的长毛线，改一处就崩一片。

一个程序如果只有一条执行线，遇到「一直做某事」就只能用无限循环，循环一旦被执行，后面的程序全被堵死。（专业上把这种「只有一条执行线」的程序叫单进程程序。）

ROS2 的解法很直接：相机交给一个程序，视觉交给另一个程序，决策再单独一个程序——每个程序只管自己的循环，谁也堵不着谁。程序之间要传数据时，ROS2 提供一套统一的通信规则。

### 1.1 ROS2 与 Ubuntu

- **Ubuntu**：真正的操作系统，管硬件、管进程。
- **ROS2**：跑在操作系统之上的**中间件 / 通信框架**。它名字里带「OS」，意思是「操作系统之上」——ROS2 不接管硬件，只在 Ubuntu 之上负责模块之间的通信。

> Ubuntu 是底座，ROS2 是架在底座之上的「对讲机系统」。

### 1.2 寄快递的类比

把 ROS2 通信想成寄快递：

- **发布者（Publisher）** 像寄件人，把包裹（消息）投进一个写着地址的邮箱（话题）；
- **话题（Topic）** 像那个邮箱，按名字区分，谁都能往里投、谁都能来取；
- **订阅者（Subscriber）** 像收件人，盯着某个邮箱，有包裹就收；
- 发布者和订阅者**不需要互相留电话**，只要都认同一个邮箱地址（话题名）和包裹规格（消息类型）。

普通写程序，发件人得认识收件人、记下对方电话，这叫「耦合」在一起。ROS2 换了一种办法——中间摆一个公共邮箱，两边谁也不认识谁，只认邮箱名字就能寄和收。不用互相认识，就叫「解耦」；因为两边只靠一个共同的名字对接，所以也叫「按名字解耦」。

这种「互不认识也能传数据」的组织方式，就是 ROS2 里说的「解耦」。
"""))

# ## 二、ROS2 通信五元组
cells.append(md("""## 二、ROS2 通信五元组

ROS2 的通信由五个基本对象组成。

### 2.1 节点 Node（C01）

节点是 ROS2 里最小的可运行模块，通常是一个独立进程：相机节点出图，决策节点算路线，运动节点管腿脚，各管一摊。一个节点出错，不拖垮其他节点。

系统里运行着哪些节点，后面会专门用命令查看。

### 2.2 话题 Topic（C02）

话题是一条命名好的数据通道，采用发布 / 订阅模式。它适合装那些「一直不停产生」的数据：

- 摄像头从早到晚拍出来的画面；
- 足球在场地里的具体位置（视觉算法一直在算）；
- 机器人自身的状态，比如电池还剩多少、关节温度多高。

这些数据不停往外冒，靠话题一条条传出去，谁想看谁来取。

### 2.3 发布 Publish（C03）与 订阅 Subscribe（C04）

- **发布**：把消息投到某个话题上。一个话题可以有多个发布者。
- **订阅**：从某个话题上取消息。一个话题也可以有多个订阅者。
- 发布者不调用订阅者，订阅者也不知道发布者是谁。两边都只认话题名和消息类型。

### 2.4 消息 Message（C05）

消息是话题上流动的数据，有固定的类型（规格）。比如：

- `std_msgs/msg/String`：只有一个 `data` 字段的字符串，适合入门；
- `sensor_msgs/msg/Image`：图像消息，含宽、高、编码、原始数据；
- 后面传感器课还会遇到更多类型。

> 轻量概念：**事件循环（E01）** 是节点里那个「不停转、有消息就处理」的循环；**回调（E02）** 是「收到消息时自动跑的那段函数」。发布 / 订阅能一直工作，靠的就是它俩。
"""))

# ## 三、话题观测四件套
cells.append(md("""## 三、话题观测四件套

下面动手看 K1 当前系统里的话题。这是机器人开发者的「X 光机」。

⚠️ **安全**：本实验是**观测课**，只读系统信息，**不发任何运动 / 动作指令**。因此不需要让机器人进入 walk 模式。ROS2 已随 K1 机器人的系统出厂预置，开机即可用，无需额外安装。

> 同样的内容在 Booster Studio 的「话题」面板里也能看到，图形界面更直观；命令行胜在能精确拿到类型、频率这些细节。两种方式都可以，下面先用命令行操作。

### 3.1 确认环境

下面的单元格都以 `!` 开头，用来查看 K1 当前系统里的话题信息。直接运行单元格即可。

先确认 ROS2 已加载。版本读环境变量 `ROS_DISTRO`（如 `humble`），各版本都支持；部分发行版没有 `ros2 --version` 这个全局参数，这里不用它。
"""))

cells.append(code("""!echo "ROS_DISTRO=$ROS_DISTRO"
!which ros2"""))

# ### 3.2 列出所有话题（list）
cells.append(md("""### 3.2 列出所有话题（list）

`ros2 topic list` 列出系统中正在广播的全部话题，每行一个。先扫一眼：有图像吗？有状态吗？有输入吗？

话题多的时候，输出会被折叠，中间出现 `...` 看不全。要确认一共有多少条，在命令后面接上 `| wc -l`，数出总行数。
"""))

cells.append(code("""!ros2 topic list"""))

cells.append(code("""!ros2 topic list | wc -l"""))

# ### 3.3 看单个话题的详情（info）
cells.append(md("""### 3.3 看单个话题的详情（info）

运行 `ros2 topic info <话题名>`，会列出该话题的消息类型（Type）、发布者数量（Publisher count）、订阅者数量（Subscription count）。

下面看图像话题。K1 的图像话题通常是 `/boostercamera/head/rgb`；如果 `ros2 topic list` 里名字不一样，以你机器上实际的为准。
"""))

cells.append(code("""!ros2 topic info /boostercamera/head/rgb"""))

cells.append(md("""从 Pub / Sub 这两个数能看出三种情况：

- `Pub=1, Sub=0`：有人发，没人看；
- `Pub=1, Sub=1`：正常通信；
- `Pub=0, Sub=1`：有人等，没人发。

看 Type 是不是 `sensor_msgs/msg/Image`。Pub / Sub 数是判断系统通没通的最快办法。
"""))

# ### 3.4 抓一条消息看看（echo --once）
cells.append(md("""### 3.4 抓一条消息看看（echo --once）

`ros2 topic echo <话题名>` 实时打印话题上的消息；加 `--once` 只抓最新一条就退出。图像消息的 `data` 很长，加 `--no-arr` 省掉数组内容，只留宽、高、编码等元信息，屏幕不会炸。
"""))

cells.append(code("""!ros2 topic echo /boostercamera/head/rgb --once --no-arr"""))

# ### 3.5 量发布频率（hz）
cells.append(md("""### 3.5 量发布频率（hz）

`ros2 topic hz <话题名>` 统计话题的发布频率。它会一直跑，看完用「内核 → 中断」或连按 I、I 停掉。图像话题通常是 30 Hz 上下。
"""))

cells.append(code("""!ros2 topic hz /boostercamera/head/rgb"""))

# ## 四、发布与订阅体验
cells.append(md("""## 四、发布与订阅体验

下面往一个自己建的话题发字符串，再订阅回来，看看两个互不相识的程序怎么靠话题名把消息送到。

<font color="red">本实验只在自建话题 `/greeting_u2l1` 上发一条字符串，**不碰机器人**，因此也不需要让机器人进入 walk 模式。多组共用环境时，把话题名改成 `/greeting_u2l1_groupN`（N 是组号），免得各组的消息混在一起。</font>

### 4.1 用 Booster Studio 发布消息

在 Booster Studio 里打开「话题发布」组件，向 `/greeting_u2l1` 发布字符串。发布页面的 JSON 编辑器里，`data` 放要发出去的内容：

```json
{
  "data": "Hello K1"
}
```

填好后点发布。（组件入口随版本略有差异，一般在「话题 / 发布」面板；多组请把话题名改成 `/greeting_u2l1_groupN`。）

注意：点一次「发布」只发出去一条消息，这个话题上不会一直有数据在流。

### 4.2 用命令行观察

先用 `info` 看发布 / 订阅数量，再用 `echo --once` 抓一条消息看看。
"""))

cells.append(code("""!ros2 topic info /greeting_u2l1
"""))

cells.append(code("""!ros2 topic echo /greeting_u2l1 --once
"""))

cells.append(md("""`echo` 拿到消息了。那这个话题上的消息是不是一直在发？用 `hz` 测一下。
"""))

cells.append(code("""!ros2 topic hz /greeting_u2l1
"""))

cells.append(md("""`hz` 没有输出，只看到一行 `WARNING: topic ... does not appear to be published yet`。

`echo` 明明拿到消息了，`hz` 为什么说没在发？

因为刚才点一次「发布」只发出了一条消息，发完就停了。ROS2 会把话题上的最后一条消息留着，给后面新来的订阅者——`echo --once` 拿到的正是这条留存的消息，不代表话题还在持续发。

所以两件套的用途不一样：**`echo` 看消息内容，`hz` 判断话题是不是在持续发布**。判断后者，只能用 `hz`。
"""))

# ### 4.3 多来一个订阅者 + 收尾
cells.append(md("""### 4.3 多来一个订阅者，再收尾

在 Booster Studio 里再开一个话题监控（订阅 `/greeting_u2l1`），然后回到这里运行下面的 `info`——Subscription count 会从 1 变成 2。发布者从头到尾不知道多了谁，这就是「发布者不感知订阅者」的协作方式。

收尾时，在 Booster Studio 里关掉话题发布面板，再运行下面的 `info`，会看到 Publisher count 变回 0。
"""))

cells.append(code("""!ros2 topic info /greeting_u2l1"""))

# ## 五、观察与记录
cells.append(md("""## 五、观察与记录

| 观察项 | 你看到的 | 说明 |
| --- | --- | --- |
| `ros2 topic list` 的话题数 |  | 系统里大概几条数据通道？ |
| 图像话题的 Type |  | 是 `sensor_msgs/msg/Image` 吗？ |
| 图像话题的 Pub / Sub 数 |  | 谁在发？谁在看？ |
| `hz` 测到的帧率 |  | 大约多少 Hz？ |
| 自己发的话题，用 `hz` 测到了吗 |  | 为什么 `echo` 能看到消息，`hz` 却测不到？ |
| 发布 / 订阅里 Sub count 的变化 |  | 多一个订阅者，发布者为什么没感觉？ |
| Studio 发布 vs 命令行观察 |  | 两种方式看到的内容一致吗？ |

**想一想**

1. Booster Studio 的发布组件和命令行的 `ros2 topic echo`，怎么靠 `/greeting_u2l1` 这个名字换到了消息？
2. 把话题名改错一个字母会怎样？（试试把发布端的话题名改成 `/greeting_u2l1x`，订阅端不变，看还能不能收到。）
3. 为什么我们常把「图像、机器人状态（电池 / 关节温度）、视觉检测结果」用话题传，而「切模式、做动作」用另一种通信（服务）？
"""))

nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
