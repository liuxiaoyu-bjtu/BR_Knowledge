# Chapter\_04\_ROS2通信与控制接口

# Chapter 04｜ROS2 通信与控制接口

Chapter 3 已经完成了第一个 K1 程序控制闭环：通过 SDK（软件开发工具包）创建控制客户端，切换准备模式和行走模式，发送 `Move` 运动指令，再发送停止指令。

这是建立“编写程序控制机器人运动”的初步尝试。但后续任务不会只由一个 Python 文件完成。ROS2 是 Robot Operating System 2 的缩写，通常译为“机器人操作系统 2”。在本课程中，它主要承担机器人软件模块之间的通信和组织作用。在ROS2中，相机图像、目标检测、位置理解、追球控制、动作触发和行为判断被拆成不同模块。

> 本章采用“随讲随练”的方式展开：
> 
> - 讲 Node（节点）时查看系统节点；
> 
> - 讲 Topic（话题）时写发布和订阅程序；
> 
> - 讲系统 Topic 时订阅 K1 图像话题并查看消息结构；
> 
> - 讲 Service（服务）时逐级调用基础运动、半身动作和全身舞蹈；
> 
> - 最后再把 Topic 和 Service 组合起来，形成后续感知控制系统的雏形。
> 
> 

## 4\.1 从单程序文件控制机器人到 ROS2 多节点系统

### 4\.1\.1 Chapter 3 的 SDK 控制链路回顾

Chapter 3 中的 `hello_robot.py` 使用 SDK 直接控制 K1。核心流程可以概括为：

```Plaintext
Python 程序
  ↓
初始化 SDK 通信
  ↓
创建 B1LocoClient 控制客户端
  ↓
切换准备模式
  ↓
切换行走模式
  ↓
发送 Move(vx, vy, vyaw)
  ↓
发送 Move(0.0, 0.0, 0.0) 停止
```

这条链路直观、短小，适合控制系统入门。读者可以从一个文件中看清模式切换、速度参数和停止逻辑。

但它也有边界。真实机器人系统不是只执行一个控制函数。以自主追球任务为例，相机节点需要持续发布图像，视觉节点需要识别足球，位置理解节点需要把图像坐标转换成更适合控制使用的数据，控制节点需要根据目标位置生成运动请求，行为节点还需要决定搜索、追踪、停稳和踢球的切换。

如果把这些都写进一个文件，程序会很快变成难以维护的长脚本。ROS2 要解决的不是“让代码更复杂”，而是让不同模块拥有清晰边界，并通过标准通信机制协作。

### 4\.1\.2 为什么需要 ROS2

ROS2 在本课程中主要解决四个问题。

第一，模块解耦。图像获取、目标检测、控制请求和行为判断可以拆成不同 Node。每个 Node 只负责一类任务。

第二，数据可观察。通过 `ros2 node list`、`ros2 topic list`、`ros2 service list` 等命令，可以查看系统中正在运行的模块、持续发布的数据流和可调用的服务。

第三，接口清晰。Topic 和 Service 都有明确的消息类型或服务类型。程序之间不是随意传递字符串，而是按照接口结构交换数据。

第四，便于扩展。后续把手写命令换成视觉检测结果，把简单状态判断换成 Behavior Tree（行为树），整体通信方式仍然可以保持一致。

从 Chapter 3 到 Chapter 4，关键变化是：

```Plaintext
Chapter 3：一个 Python 文件直接调用 SDK
Chapter 4：多个 ROS2 节点通过 Topic 和 Service 协作
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTk1MGIwMmYxMzAyOTBhMTM4ODcyZTA0MWM3YjhjZDZfOGI1NjNiNTc2MDQyODQ3NTMxZjUzMGJmMDMyODA5ZmRfSUQ6NzY2MDA4OTAzNzA2ODI5MTI4OV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

### 4\.1\.3 本章实践案例地图

本章包含七个递进实践案例。

|案例|主题|对应代码|
|---|---|---|
|案例 4\-1|查看 K1 当前 ROS2 系统|命令行操作|
|案例 4\-2|两个 Python 节点通过 Topic 发布和订阅|`topic_status_publisher.py`、`topic_status_subscriber.py`|
|案例 4\-3|订阅 K1 图像 Topic 并查看消息结构|`image_topic_inspector.py`|
|案例 4\-4|通过 Service 请求基础运动|`ros2_motion_request.py`|
|案例 4\-5|通过 Service 请求半身动作|`ros2_upper_body_action.py`|
|案例 4\-6|通过 Service 请求全身舞蹈|`ros2_whole_body_dance.py`|
|案例 4\-7|Topic 命令触发 Service 控制|`command_publisher.py`、`command_service_bridge.py`|

这些案例不是彼此孤立的。它们共同建立一条后续任务会反复使用的链路：

```Plaintext
系统节点运行
  ↓
Topic 持续发布数据
  ↓
控制节点订阅 Topic
  ↓
控制节点通过 Service 发送请求
  ↓
机器人执行运动或动作
```

## 4\.2 ROS2 系统观察：Node、Topic、Service 与 Message

### 4\.2\.1 Node：运行中的功能模块

Node 通常译为“节点”。在 ROS2 中，节点是一个正在运行的功能模块。一个节点可以由 Python 程序创建，也可以由 C\+\+ 程序创建；可以负责读取相机，也可以负责发布状态，还可以负责发送控制请求。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YTgzMTBlZmIwYzdjZjA1YjM0MzlhMTJjNzVkYWEyM2FfMTRhMTJhYjQ1OTM0YzJkNmQ3Njk2NTc1MTc3MWY3YzZfSUQ6NzY2MDA4OTMxMTYzNDAwMDg2OF8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

节点的重点不是文件名，而是运行身份。例如一个文件叫 `topic_status_publisher.py`，运行后创建的节点名可以是 `k1_demo_status_publisher`。ROS2 系统识别的是节点名、话题名和服务名，而不是普通文件路径。

查看当前系统中的节点：

```Bash
ros2 node list
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTczNTU4MzllNDQ2NGQ1MGQ1NzVjZDJkYzNlNzY2ZDZfNjkxN2I4OGFhMjI4Mzc1ZWViMmIyNzk2YjA5YjE3MzFfSUQ6NzY2MjI1NDA0MzA4MzUyNTA5Ml8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

如果 K1 上层程序已经运行，终端会列出当前活跃节点。不同系统版本和启动状态下，节点名称可能不同。关键不是背固定名称，而是理解：每一行都代表一个正在运行的软件模块。

### 4\.2\.2 Topic：持续数据流

Topic 通常译为“话题”。Topic 使用发布\-订阅模型，英文常写作 Publish / Subscribe。

在这个模型中，发布者把消息发布到某个话题，订阅者从同一个话题接收消息。发布者不需要直接调用订阅者函数，订阅者也不需要知道发布者内部怎么写。两者通过话题名称和消息类型连接。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjQ2NTY5OTY4ZDg1NTIyNTcyNjkxMjMxOTk3YjY3ZDdfNGRkMWY3NTE0YmZmYmE5N2NjY2E3MTA1YWQ3NDYwZjNfSUQ6NzY2MDA4OTcyNjM2NDQ1NDExMF8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

Topic 适合持续产生的数据，例如：

- 相机图像；

- IMU 姿态数据；

- 机器人关节状态；

- 电池状态；

- 检测结果；

- 目标位置；

- 调试状态。

查看当前系统中的话题：

```Bash
ros2 topic list
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzdkY2MzZjY1ZDI3NDg5Y2M2MjcyNWQ3ZTg0NTg1MWRfY2MzYWUzYTZmNjEzNmZiMTAyZTgxN2IyYzFlZjcxMTVfSUQ6NzY2MjI1NDczMjE5NDQ1MDczMV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

查看某个话题的信息：

```Bash
ros2 topic info <topic_name>
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjE0ZjNiZmUwMGRhODI1YzkzNmQzMDk5N2ZiZmEyMzNfMzcxY2M4OGJhNjRkMGY5Y2Y2OGQwZjFlYjRiMjA0NTVfSUQ6NzY2MjI1NTQxODQ0NTgxMDYzNV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

打印某个话题中的消息：

```Bash
ros2 topic echo <topic_name>
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjQxYWY0ZjZmMWRhMmNlOGYzZTczMzFjMmMzNjExMTJfYTIyNTM5YjVlMDljZjQ4ZDBjNmViZTJmMGY4YzgyODVfSUQ6NzY2MjI1NTQ5ODcyMDQzMTA1Ml8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

### 4\.2\.3 Service：一次请求与响应

Service 通常译为“服务”。Service 使用请求\-响应模型，英文常写作 Request / Response。

一次 Service 调用包含两个角色：

- Client：客户端，发送请求；

- Server：服务端，接收请求，处理后返回响应。

Service 适合一次明确操作，例如：

- 查询状态；

- 切换机器人模式；

- 请求基础运动；

- 触发半身动作；

- 触发全身舞蹈。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDRkNWY2NjA5NjFmYTU1MzI1N2Y3ZGIzMzE5NTEyMTlfNTY3OTlmYWI2M2E5OGIyMmM1NWJiZDIwNDhlMjFhYzdfSUQ6NzY2MDA5MDM2NDk2NzMyNDY0NV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

查看当前系统中的服务：

```Bash
ros2 service list
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTBjZTkwNTEyMWZkYTM1MzQ5ZTdmMDNjMDQzOTVlNWJfYTVmYTgxYjBlMzc0ZmRkZDNiZTZiMGVhNjdkNTEzY2JfSUQ6NzY2MjI1NTk4MTgyOTAzMjkwN18xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

查看某个服务的类型：

```Bash
ros2 service type <service_name>
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjM0MmMzNDIzOTk3YTkyY2RkNmFlYWRhZTllMjg2OWRfOWRiN2E5MjdiM2NiY2JmODA5M2VkN2EzODg1M2Q1NDdfSUQ6NzY2MjI1NjM2ODIwODM1MDQwN18xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

### 4\.2\.4 Message：消息类型决定数据结构

Message 通常译为“消息”。ROS2 中的数据不是随意传递的。Topic 使用消息类型，Service 使用服务接口类型。

本章会接触三类接口：

|接口|类型|用途|
|---|---|---|
|`/k1_demo/status`|`std_msgs/msg/String`|自定义字符串状态话题|
|`/boostercamera/head/rgb`|`sensor_msgs/msg/Image`|K1 图像话题|
|`/booster_rpc_service`|`booster_interface/srv/RpcService`|K1 控制服务|

`std_msgs/msg/String` 只有一个核心字段 `data`，适合入门理解 Topic。`sensor_msgs/msg/Image` 是 ROS2 标准图像消息，包含图像宽度、高度、编码和原始数据。`RpcService` 是服务接口，用于向 K1 控制服务发送包含 `api_id` 和 `body` 的请求。

### 4\.2\.5 实践案例 4\-1：查看 K1 当前 ROS2 系统

本案例不写代码，先用命令行观察 K1 当前 ROS2 系统。

查看节点：

```Bash
ros2 node list
```

查看话题：

```Bash
ros2 topic list
```

查看服务：

```Bash
ros2 service list
```

查看某个话题的信息：

```Bash
ros2 topic info /boostercamera/head/rgb
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjQ4YzdiMjJmMzE3ZGM1MmJhZTUwMmNlNGU0ZmQ0MzFfZDY0YzEyNWZkZGUwMTVkODE1NDMyZDExMWY2M2FlNmJfSUQ6NzY2MjI1NzY4OTI2MDgyMTQ4NV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

查看某个服务的类型：

```Bash
ros2 service type /booster_rpc_service
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MWY1YjJiNWI2ODI2NzhmYWQ3MjFkODUxYTk0NjQ4ODdfNzA2NmVkY2Y0OGQ4MDNkZGZhZmZjNTA5MDFiZGJiMGJfSUQ6NzY2MjI1Nzc5MzkzNjIxNDk2OV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

查看接口结构：

```Bash
ros2 interface show sensor_msgs/msg/Image
ros2 interface show booster_interface/srv/RpcService
```

这一步的目标是让读者先看到系统中确实存在节点、话题、服务和接口类型，而不是直接进入代码。

### 4\.2\.6 案例 4\-1 运行方式与效果观察

通过 SSH 登录 K1 后， 运行 `ros2 topic info /boostercamera/head/rgb` 后，重点观察：

- 话题是否存在；

- `Type` 是否为 `sensor_msgs/msg/Image`；

- `Publisher count` 是否大于 `0`；

- 当前是否已有订阅者。

运行 `ros2 service type /booster_rpc_service` 后，重点观察是否返回：

```Plaintext
booster_interface/srv/RpcService
```

如果服务类型正确，说明后续 Python 程序可以按 `RpcService` 结构构造请求。

### 4\.2\.7 案例 4\-1 常见问题排查

问题 1：`ros2` 命令不存在。

通常是 ROS2 环境未加载。先运行：

```Bash
source /opt/ros/humble/setup.bash
```

问题 2：找不到 `/boostercamera/head/rgb`。

按顺序检查：

- 打印所有话题名称，查看话题名称是否正确

- `ros2 topic list | grep boostercamera` 是否有其他图像话题；

- 是否在 K1 本机环境中查看。

本章实践统一以 `/boostercamera/head/rgb` 为主线。

问题 3：找不到 `/booster_rpc_service`。

按顺序检查：

- `ros2 service list` 是否能看到其他控制相关服务；

- 是否在同一个终端中加载环境并运行程序。

## 4\.3 Topic 发布与订阅：两个 Python 节点如何通信

### 4\.3\.1 发布者与订阅者

Topic 的核心是发布者和订阅者。

发布者负责产生消息：

```Plaintext
Publisher Node
  ↓
/topic_name
```

订阅者负责接收消息：

```Plaintext
/topic_name
  ↓
Subscriber Node
```

发布者和订阅者不直接调用彼此函数。只要话题名称一致、消息类型一致，ROS2 就会负责消息传递。

本节先用两个简单 Python 文件模拟两个节点：一个发布状态字符串，一个订阅状态字符串。这个案例不控制机器人，目的是把 Topic 的通信方式讲清楚。

### 4\.3\.2 消息类型：`std_msgs/msg/String`

`std_msgs/msg/String` 是 ROS2 中最简单的字符串消息类型。它只有一个核心字段：

```Plaintext
string data
```

在 Python 中使用时，可以这样创建消息：

```Python
from std_msgs.msg import String

msg = String()
msg.data = "K1 demo status tick: 1"
```

简单消息适合用来理解 Topic 机制。后续图像、检测结果、机器人状态都会换成更复杂的消息类型，但发布和订阅的基本模式是一样的。

### 4\.3\.3 实践案例 4\-2：自定义状态 Topic 发布与订阅

本案例对应两个代码文件：

```Plaintext
CourseCode/chapter_04_ros2_control/topic_status_publisher.py
CourseCode/chapter_04_ros2_control/topic_status_subscriber.py
```

发布节点负责向 `/k1_demo/status` 发布字符串：

```Plaintext
K1 demo status tick: 1
K1 demo status tick: 2
K1 demo status tick: 3
```

订阅节点负责订阅同一个话题，并打印收到的字符串。

这个案例体现了两个 Node 的不同作用：

|节点|作用|
|---|---|
|`k1_demo_status_publisher`|定时发布状态消息|
|`k1_demo_status_subscriber`|接收并打印状态消息|

### 4\.3\.4 案例 4\-2 代码说明

发布者中创建 Publisher：

```Python
self.publisher = self.create_publisher(String, TOPIC_NAME, 10)
```

这里的三个参数分别表示：

- `String`：消息类型；

- `TOPIC_NAME`：话题名称，本案例为 `/k1_demo/status`；

- `10`：消息队列深度。

发布者中创建定时器：

```Python
self.timer = self.create_timer(1.0, self.publish_status)
```

这表示每 `1.0 s` 调用一次 `publish_status()`。

发布消息：

```Python
msg = String()
msg.data = f"K1 demo status tick: {self.count}"
self.publisher.publish(msg)
```

订阅者中创建 Subscription（订阅）：

```Python
self.subscription = self.create_subscription(
    String,
    TOPIC_NAME,
    self.on_status,
    10,
)
```

当 `/k1_demo/status` 上有新消息到达时，ROS2 会调用 `on_status()`：

```Python
def on_status(self, msg):
    self.get_logger().info(f"收到：{msg.data}")
```

这就是 Topic 的基本结构：发布者只负责发布，订阅者只负责接收，双方通过话题和消息类型连接。

### 4\.3\.5 案例 4\-2 运行方式与效果观察

打开第一个终端，运行发布者：

```Bash
cd /home/booster/Workspace/CourseCode/chapter_04_ros2_control
python3 topic_status_publisher.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YTBkOTE2Mjk2OTRlNGNmZTM3NTIwMjcxMjkyN2Y1ZDdfODk2MzZjODUwMTI1ODIxOTc4Njg5ZDA2NzdjZGY4NDNfSUQ6NzY2MjI2MTc5Mjg5NDQwNTg5N18xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

打开第二个终端，运行订阅者：

```Bash
cd /home/booster/Workspace/CourseCode/chapter_04_ros2_control
python3 topic_status_subscriber.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Zjc5ZGNhZjYwZGFkOWI2ZGMyODY1NWJiMjc3MzBlNTdfODdhZDNhZjMwOTM0NzliM2ZkNTc1ZWNlYjU2ODQ3YzdfSUQ6NzY2MjI2MTcwODQ2MzUyNDg0NV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

订阅者终端应持续打印类似：

```Plaintext
收到：K1 demo status tick: 1
收到：K1 demo status tick: 2
收到：K1 demo status tick: 3
```

打开第三个终端，可以直接查看话题：

```Bash
ros2 topic list | grep k1_demo
ros2 topic info /k1_demo/status
ros2 topic echo /k1_demo/status
```

`ros2 topic info /k1_demo/status` 中应能看到消息类型：

```Plaintext
Type: std_msgs/msg/String
```

也能看到发布者和订阅者数量。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NWZlYzNlM2U4M2VmZTAzM2U5ZTRmNDcwZDlmYjAyNjZfZmI4MmI2OWY4OWE0MzlkYzc0ZDJhODcyNDEzYTQ1ZTJfSUQ6NzY2MjI2MjI0NTQ0NDE5MzU3OV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

### 4\.3\.6 案例 4\-2 常见问题排查

问题 1：订阅者没有收到消息。

按顺序检查：

- 发布者是否正在运行；

- 话题名称是否都是 `/k1_demo/status`；

- 消息类型是否都是 `std_msgs/msg/String`。

问题 2：`ros2 topic list` 看不到 `/k1_demo/status`。

通常说明发布者没有运行，或者发布者程序启动失败。先查看发布者终端是否持续打印“发布”日志。

问题 3：`ros2 topic echo` 能看到消息，但 Python 订阅者看不到。

重点检查订阅者代码中的话题名称和消息类型。Topic 名称只要多一个字符，订阅者就会订阅到另一个不存在的话题。

## 4\.4 系统 Topic：订阅 K1 图像话题并查看消息结构

### 4\.4\.1 发布方也可以是系统节点

案例 4\-2 中，发布方和订阅方都是自己写的 Python 节点。但在真实机器人系统中，发布方经常是系统节点。例如 K1 的相机节点会持续发布图像，视觉程序只需要订阅图像话题即可获得相机数据。

这意味着 Topic 的发布方不一定由当前程序创建。只要系统中已有节点发布某个话题，其他节点就可以订阅它。

### 4\.4\.2 K1 图像 Topic

本章统一使用 K1 图像话题：

```Plaintext
/boostercamera/head/rgb
```

它的消息类型应为：

```Plaintext
sensor_msgs/msg/Image
```

`sensor_msgs/msg/Image` 是 ROS2 标准图像消息。它适合在机器人系统中传输图像，但它不是 OpenCV（开源计算机视觉库）中的图像矩阵。本章只查看图像消息结构，不显示图像，也不保存图像。OpenCV 图像转换会在后续视觉章节展开。

运行前可以确认话题信息：

```Bash
ros2 topic info /boostercamera/head/rgb
```

如果系统中还有其他相近图像话题，仍以本章指定的 `/boostercamera/head/rgb` 为主线。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ODUxOTU2YTgxYTQ3OGNiZGNlNWM0ZjAyMDAyOTkwOTVfNTAzYzgxODc5YWJkNzk5NmNjYTUxNTVmZmJjZjdlMjlfSUQ6NzY2MjI3MjA1MTE4OTg5NDEyMl8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

### 4\.4\.3 `sensor_msgs/msg/Image` 关键字段

查看图像消息接口：

```Bash
ros2 interface show sensor_msgs/msg/Image
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Yzc1NWYwYjZhMzE1Mjc4ZWI1N2ZhN2NiMjVjNzI3YTRfNzJkMDk2ZmY2NWViYjU3Mjc5N2RlOWEzNDZhZjFlNDhfSUQ6NzY2MjI3MjI5MjEwMTM0NDIyOF8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

常见关键字段包括：

|字段|含义|
|---|---|
|`header`|时间戳和坐标帧信息|
|`height`|图像高度|
|`width`|图像宽度|
|`encoding`|图像编码格式|
|`step`|每一行图像数据占用的字节数|
|`data`|图像原始字节数据|

其中 `data` 通常很长，不适合直接完整打印。查看图像话题时可以使用：

```Bash
ros2 topic echo /boostercamera/head/rgb --no-arr
```

`--no-arr` 会省略数组内容，更适合观察宽、高、编码、时间戳等元信息。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ODRiM2ZiNTRiYWUyOWU4ZjAwYzgxZjRjZjUxMTQzYjFfYzdjNmM5NmQyMDZmMzQzNjM1NDkwYTk4MDViODlhODhfSUQ6NzY2MjI3MjY0MTc3MjY1MzUxM18xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

### 4\.4\.4 实践案例 4\-3：订阅图像 Topic 并打印图像元信息

本案例对应代码文件：

```Plaintext
CourseCode/chapter_04_ros2_control/image_topic_inspector.py
```

程序订阅：

```Plaintext
/boostercamera/head/rgb
```

每收到一帧图像，就打印：

- 帧序号；

- 时间戳；

- `frame_id`；

- 图像宽度；

- 图像高度；

- 编码格式；

- 每行字节数；

- `data` 字节长度。

程序默认打印 5 帧后退出。

### 4\.4\.5 案例 4\-3 代码说明

导入图像消息类型：

```Python
from sensor_msgs.msg import Image
```

设置默认图像话题：

```Python
DEFAULT_IMAGE_TOPIC = "/boostercamera/head/rgb"
```

创建订阅：

```Python
self.subscription = self.create_subscription(
    Image,
    topic_name,
    self.on_image,
    10,
)
```

回调函数中读取图像元信息：

```Python
data_length = len(msg.data)

self.get_logger().info(
    "width=%d height=%d encoding=%s step=%d data_len=%d"
    % (
        msg.width,
        msg.height,
        msg.encoding,
        msg.step,
        data_length,
    )
)
```

这里不处理 `data` 中的像素内容，只读取它的长度。这样可以先确认程序已经收到图像消息，并理解消息结构。

### 4\.4\.6 案例 4\-3 运行方式与效果观察

先确认图像话题存在：

```Bash
ros2 topic info /boostercamera/head/rgb
```

再运行程序：

```Bash
cd /home/booster/Workspace/CourseCode/chapter_04_ros2_control
source /opt/ros/humble/setup.bash
python3 image_topic_inspector.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTlkNGNiYmFiMzZmYTI1NjRhYmMzOTdiOTU5MTFiYWJfOTZiZWNhMjJkYjM2NDI2NjhiNzVkYWRkMmVlMjEzNWNfSUQ6NzY2MjI3MzUzMDU0NTU3MjgwOV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

终端应打印类似信息：

```Plaintext
frame=1 stamp=... frame_id=... width=1280 height=720 encoding=rgb8 step=3840 data_len=2764800
frame=2 stamp=... frame_id=... width=1280 height=720 encoding=rgb8 step=3840 data_len=2764800
```

具体分辨率和编码以当前 K1 相机输出为准。读者需要关注的是：程序是否收到连续图像帧，宽高是否合理，`encoding` 是否符合当前系统输出，`data_len` 是否与图像大小匹配。

也可以指定打印帧数：

```Bash
python3 image_topic_inspector.py --frames 10
```

如果图像话题名称需要临时调整，可以使用：

```Bash
python3 image_topic_inspector.py --topic /boostercamera/head/rgb
```

### 4\.4\.7 案例 4\-3 常见问题排查

问题 1：程序一直没有输出图像帧。

按顺序检查：

- `/boostercamera/head/rgb` 是否存在；

- `ros2 topic info /boostercamera/head/rgb` 中 `Publisher count` 是否大于 `0`；

- 相机服务是否启动；

- 当前终端是否加载了 ROS2 环境。

问题 2：导入 `sensor_msgs` 失败。

通常是 ROS2 环境未加载。运行：

```Bash
source /opt/ros/humble/setup.bash
```

再测试：

```Bash
python3 -c "from sensor_msgs.msg import Image; print('sensor_msgs ok')"
```

问题 3：`ros2 topic echo` 输出太多内容。

图像消息中的 `data` 字段很大，不适合完整打印。使用：

```Bash
ros2 topic echo /boostercamera/head/rgb --no-arr
```

只观察元信息。

## 4\.5 Service 控制基础：通过 `/booster_rpc_service` 请求运动

### 4\.5\.1 Service 与 Topic 的区别

Topic 适合持续数据流，Service 适合一次明确请求。

基础运动控制通常是明确请求。例如希望机器人进入准备模式、进入行走模式、向前小幅移动、停止。这些操作不是连续图像流，而是一条条控制请求，因此适合使用 Service。

### 4\.5\.2 K1 控制服务结构

本章使用的 K1 控制服务为：

```Plaintext
/booster_rpc_service
```

服务类型为：

```Plaintext
booster_interface/srv/RpcService
```

请求结构可以简化理解为：

```Plaintext
api_id：功能编号
body：参数内容，通常是 JSON 字符串
```

本节使用两个功能编号：

|功能|`api_id`|`body` 示例|
|---|---|---|
|切换模式|`2000`|`{"mode":1}`|
|基础运动|`2001`|`{"vx":0.2,"vy":0.0,"vyaw":0.0}`|

其中模式值：

|模式|数值|
|---|---|
|准备模式|`1`|
|行走模式|`2`|

### 4\.5\.3 实践案例 4\-4：Service 调用基础运动

本案例对应代码文件：

```Plaintext
CourseCode/chapter_04_ros2_control/ros2_motion_request.py
```

程序执行流程为：

```Plaintext
创建 ROS2 服务客户端
  ↓
等待 /booster_rpc_service 可用
  ↓
发送准备模式请求
  ↓
发送行走模式请求
  ↓
发送小幅前进请求
  ↓
等待 1.5 s
  ↓
发送停止请求
```

这个案例与 Chapter 3 的 `hello_robot.py` 效果相近，但进入控制系统的方式不同：Chapter 3 直接调用 SDK，Chapter 4 通过 ROS2 Service 请求。

### 4\.5\.4 案例 4\-4 代码说明

服务请求的公共逻辑放在：

```Plaintext
CourseCode/chapter_04_ros2_control/k1_rpc_client.py
```

它封装了：

- `RpcService.Request()` 创建；

- `api_id` 和 `body` 填写；

- 异步服务调用；

- 超时判断；

- 响应打印；

- 模式切换、运动、动作调用的辅助方法。

基础运动脚本中调用：

```Python
control.change_mode(MODE_PREPARE)
control.change_mode(MODE_WALKING)
control.move(0.2, 0.0, 0.0)
```

停止逻辑放在 `finally` 中：

```Python
finally:
    if control is not None:
        if control.service_ready:
            control.move(0.0, 0.0, 0.0)
```

`finally` 的作用是：即使中途发生异常，也尽量发送停止请求。机器人控制程序不能只考虑正常流程。

### 4\.5\.5 案例 4\-4 运行方式与效果观察

运行前确认服务存在：

```Bash
ros2 service list | grep booster_rpc_service
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDkyZjMwMjcxNjhiZTRmM2FlNmE1ODU4ZThlNDZjNWZfMWY5MmRmYzhiMmM4YWQwNjY5NGE4N2UwMmRlODIwNzRfSUQ6NzY2MjI3NDg1MzMwNjc0ODE5NF8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

运行程序：

```Bash
cd /home/booster/Workspace/CourseCode/chapter_04_ros2_control
python3 ros2_motion_request.py
```

运行前必须确认：

- 机器人已经完成开机初始化；

- 双脚平稳接触地面；

- 周围有足够空间；

- 可以立即按下背部 `STAND` 按钮让机器人回到准备模式。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MzU5Njc3MzFmNGQyNDllN2RlZjQ1NzBlZGY2MWY0OGNfOTA5YTlmN2M2YTExOTUzZDc1ZDFkZmM3OGY2NmZlZDBfSUQ6NzY2MjI3ODgwODU1NzcwMjA5MV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

运行后观察：

- 终端是否打印服务请求和响应；

- 机器人是否进入准备模式；

- 机器人是否进入行走模式；

- 机器人是否向前小幅移动；

- 停止请求后机器人是否停止。

### 4\.5\.6 案例 4\-4 常见问题排查

问题 1：程序一直等待 `/booster_rpc_service`。

检查：

```Bash
ros2 service list | grep booster_rpc_service
```

如果没有输出，先排查控制服务是否启动和 ROS2 环境是否加载。

问题 2：有服务响应，但机器人不移动。

按顺序检查：

- 是否已经切换到行走模式；

- `vx`、`vy`、`vyaw` 是否全部为 `0`；

- 机器人是否处于保护状态；

- 当前地面和站姿是否安全；

- Booster Studio 中状态是否正常。

问题 3：机器人移动后没有停止。

立即按下背部 `STAND` 按钮。后续排查：

- `finally` 中是否发送停止请求；

- 服务请求是否超时；

- 程序是否在停止请求前卡住；

- `time.sleep()` 是否被改得过长。

问题4：出现报错ModuleNotFoundError: No module named 'booster\_interface'

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTk5MTAwMTUyOTQ5NWUzYjVmNzkwYzdiMTJhNmZiM2VfNGQ4ODY2ZWJiODA1N2Q1M2EwOTRlNjIxNzAxMzA0MWFfSUQ6NzY2MjMwNTI3NjQwNjAwODc5MV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

说明当前 Python 环境中找不到 ROS 2 接口包 `booster_interface`。

解决办法：

- 第一步：查找接口包存在位置

```Plain Text
find ~/Workspace -type d -name "booster_interface" 2>/dev/null
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjEyZWE3ZmZhNmIzNzhmNzczODM4ZWI0MjU3ZDAwYmNfOTViOTFmM2E1MzQwY2ZiNzZlN2VkMWJiOTg1MzI3MTRfSUQ6NzY2MjI3OTM4NTc4MTc1MDcxMl8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

第二步：进入它所在工作空间的根目录，图片示例为`k1_booster`。

第三步：加载 ROS 2 环境

```Plain Text
source /opt/ros/$ROS_DISTRO/setup.bash
```

第四步：检查 `colcon` 识别

```Plain Text
colcon list | grep booster_interface
```

可以看到booster\_interface。

第五步：执行编译

```Plain Text
colcon build --packages-select booster_interface --symlink-install
```

第六步：加载工作空间

```Plain Text
source install/setup.bash
```

第七步：测试是否可以导入

```Plain Text
python3 -c "from booster_interface.srv import RpcService; print('booster_interface 导入成功')"
```

导入成功后，可以正常执行代码。

```Bash
cd /home/booster/Workspace/CourseCode/chapter_04_ros2_control
python3 ros2_motion_request.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZmJjZjk3ZGM4YzNjNzJkYzY2NDRlYWViMTBmMTFkZDJfMjI2NmEzN2U0ODgwOTEyZWU0YmY0MjE2Mjg0YjM4MWFfSUQ6NzY2MjI4MDIwOTk0OTA1MTg2M18xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

## 4\.6 Service 动作调用：半身动作

### 4\.6\.1 运动控制与动作调用的区别

运动控制描述的是速度意图，例如 `vx`、`vy`、`vyaw`。机器人会根据速度意图持续移动，直到收到新的速度请求或停止请求。

动作调用描述的是触发某个预置动作或动作序列。例如半身动作、手势动作、舞蹈动作。它更像“执行一个动作编号”，而不是持续给速度。

### 4\.6\.2 半身动作请求结构

本节使用半身/上肢动作类请求：

```Plaintext
api_id = 2016
body = {"dance_id": 0}
```

常用动作编号包括：

|动作|`dance_id`|
|---|---|
|新年动作|`0`|
|哪吒动作|`1`|
|奔向未来动作|`2`|
|Dabbing 手势|`3`|
|奥特曼手势|`4`|
|停止动作|`1000`|

具体动作表现以当前 K1 系统版本为准。本章默认使用 `dance_id = 0`，并在等待后发送 `dance_id = 1000` 停止请求。

### 4\.6\.3 实践案例 4\-5：Service 调用半身动作

本案例对应代码文件：

```Plaintext
CourseCode/chapter_04_ros2_control/ros2_upper_body_action.py
```

运行逻辑：

```Plaintext
创建 ROS2 服务客户端
  ↓
等待 /booster_rpc_service
  ↓
发送半身动作请求
  ↓
等待指定时间
  ↓
发送停止动作请求
```

这个案例用于理解动作类 Service 请求。它与基础运动的区别是：请求体不再包含 `vx`、`vy`、`vyaw`，而是包含 `dance_id`。

### 4\.6\.4 案例 4\-5 代码说明

核心调用：

```Python
control.dance(args.dance_id)
time.sleep(args.duration)
control.dance(DANCE_STOP)
```

`control.dance()` 内部实际发送：

```Plaintext
api_id = 2016
body = {"dance_id": ...}
```

程序默认动作持续 `4.0 s` 后发送停止请求。可以通过参数调整：

```Bash
python3 ros2_upper_body_action.py --dance-id 0 --duration 4
```

如果需要只发送动作、不发送停止请求，可以使用：

```Bash
python3 ros2_upper_body_action.py --dance-id 0 --no-stop
```

初次运行不建议使用 `--no-stop`。

### 4\.6\.5 案例 4\-5 运行方式与效果观察

运行程序：

```Bash
cd /home/booster/Workspace/CourseCode/chapter_04_ros2_control
source /opt/ros/humble/setup.bash
python3 ros2_upper_body_action.py --dance-id 0 --duration 4
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTE3Nzc2ZDZmY2Q3NzNjOGNiNzQ2YjcxNGEzODUxOGNfZDM4YmQ1MzE2YjM4ZTJhOWMwMDY4MjY3MzBhYTQ3Y2ZfSUQ6NzY2MjI4MjcxNzM5Mjk5NzY1OV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

运行前确认机器人站稳，周围没有人员贴近手臂运动范围。运行后观察：

- 终端是否打印 `api_id=2016`；

- `body` 中 `dance_id` 是否正确；

- 机器人是否执行对应半身/上肢动作；

- 等待结束后是否发送 `dance_id=1000` 停止请求。

### 4\.6\.6 案例 4\-5 常见问题排查

问题 1：服务有响应，但动作没有执行。

检查：

- 当前系统版本是否支持该 `dance_id`；

- 机器人是否处于允许执行动作的状态；

- 是否有其他动作或控制请求占用机器人；

- 终端响应中是否包含异常状态。

问题 2：动作持续时间过长。

先按下背部 `STAND` 按钮。后续运行时缩短 `--duration`，并确认程序没有使用 `--no-stop`。

问题 3：动作编号不确定。

不要随意尝试大量编号。先使用本章列出的基础编号，确认动作链路正常后，再结合当前系统接口表扩展。

## 4\.7 Service 动作调用：全身舞蹈

### 4\.7\.1 全身动作的安全边界

全身舞蹈会涉及更大幅度的身体运动，风险高于半身动作。运行这类程序前，必须确认：

- 机器人站在平整地面；

- 周围空间充足；

- 旁边没有人员、桌椅、线缆或易碰撞物；

- 操作人员可以立即按下背部 `STAND` 按钮；

- 不在电量过低、姿态异常或保护状态下运行。

全身动作不适合作为随手测试命令。程序中需要加入明确确认参数，避免误运行。

### 4\.7\.2 全身舞蹈请求结构

全身舞蹈请求使用：

```Plaintext
api_id = 2029
body = {"dance_id": 0}
```

常见全身舞蹈编号包括：

|动作|`dance_id`|
|---|---|
|Arbic Dance|`0`|
|Michael Dance 1|`1`|
|Michael Dance 2|`2`|
|Michael Dance 3|`3`|
|Boxing Style Kick|`5`|
|Roundhouse Kick|`6`|

初次运行建议使用较基础的 `dance_id = 0`，不要直接尝试大幅踢腿类动作。

### 4\.7\.3 实践案例 4\-6：Service 调用全身舞蹈

本案例对应代码文件：

```Plaintext
CourseCode/chapter_04_ros2_control/ros2_whole_body_dance.py
```

程序必须带 `--confirm` 才会发送请求：

```Bash
python3 ros2_whole_body_dance.py --dance-id 0 --confirm
```

如果没有 `--confirm`，程序只打印提示并退出，不会向机器人发送全身舞蹈请求。

### 4\.7\.4 案例 4\-6 代码说明

确认参数检查：

```Python
if not args.confirm:
    print("未提供 --confirm，已取消全身舞蹈请求")
    return
```

发送全身舞蹈请求：

```Python
control.whole_body_dance(args.dance_id)
```

内部实际发送：

```Plaintext
api_id = 2029
body = {"dance_id": ...}
```

全身舞蹈是否自动结束取决于动作本身和当前系统实现。本案例重点是演示 Service 如何触发全身动作，不把全身舞蹈当作基础运动调参工具。

### 4\.7\.5 案例 4\-6 运行方式与效果观察

先运行不带确认参数的命令：

```Bash
python3 ros2_whole_body_dance.py --dance-id 0
```

程序应取消请求并提示需要 `--confirm`。

确认安全后运行：

```Bash
python3 ros2_whole_body_dance.py --dance-id 0 --confirm
```

观察：

- 终端是否打印 `api_id=2029`；

- 机器人是否执行全身舞蹈；

- 动作过程中是否保持稳定；

- 动作结束后机器人状态是否正常。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZWRlN2FkNTU2YTAyMTQ2OGQzOTM1MDRhNzg4Y2FjOWNfMWI2OThiYjQ5MWM1OTE3ZTc2MDJiNzk1OGVmZTZjZjhfSUQ6NzY2MjI4MzU2Mzg3ODQxOTcxNV8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

### 4\.7\.6 案例 4\-6 常见问题排查

问题 1：程序提示取消请求。

这是正常保护逻辑。需要确认安全后添加：

```Bash
--confirm
```

问题 2：动作幅度过大。

立即按背部 `STAND` 按钮。后续避免尝试大幅动作编号，先回到半身动作或基础运动案例确认系统状态。

问题 3：服务有响应但机器人不动作。

检查：

- 当前系统是否支持该全身舞蹈编号；

- 机器人当前模式是否允许动作；

- 是否存在保护状态；

- 是否有其他控制程序正在运行。

## 4\.8 Topic \+ Service 组合：命令话题触发控制服务

### 4\.8\.1 为什么需要组合 Topic 和 Service

前面的案例分别讲了 Topic 和 Service。真实机器人任务通常需要把两者组合起来。

在后续视觉追球任务中，感知节点会通过 Topic 持续发布目标信息。控制节点订阅目标信息后，不会直接变成机器人动作，而是需要根据目标位置决定是否发送运动或动作请求。这些请求适合通过 Service 发送给控制服务。

因此，一条常见链路是：

```Plaintext
感知结果 Topic
  ↓
控制或行为节点
  ↓
Service 请求
  ↓
机器人运动或动作
```

本节用字符串命令模拟感知结果或行为决策输出。命令发布节点只负责发布命令，控制桥接节点负责订阅命令并转换成 K1 服务请求。

### 4\.8\.2 实践案例 4\-7：命令发布节点 \+ 控制桥接节点

本案例对应两个代码文件：

```Plaintext
CourseCode/chapter_04_ros2_control/command_publisher.py
CourseCode/chapter_04_ros2_control/command_service_bridge.py
```

`command_publisher.py` 向以下话题发布命令：

```Plaintext
/k1_demo/control_command
```

消息类型为：

```Plaintext
std_msgs/msg/String
```

支持的命令包括：

|命令|含义|
|---|---|
|`prepare`|切换准备模式|
|`walk`|切换行走模式|
|`move_forward_short`|小幅前进后停止|
|`stop`|发送停止运动请求|
|`upper_dance`|触发半身动作|
|`upper_dance_stop`|停止半身动作|
|`whole_body_dance`|触发全身舞蹈|

`command_service_bridge.py` 订阅 `/k1_demo/control_command`，将字符串命令转换成 `/booster_rpc_service` 请求。

### 4\.8\.3 案例 4\-7 节点分工

这个案例中至少有三个角色：

|角色|作用|
|---|---|
|命令发布节点|发布字符串命令，不关心 K1 服务细节|
|控制桥接节点|订阅命令，把命令翻译成 Service 请求|
|K1 控制服务|接收请求并控制机器人|

这种分工体现了 ROS2 的价值：命令来源可以替换。现在命令来自 `command_publisher.py`；后续命令可以来自视觉检测节点、状态机节点或 Behavior Tree（行为树）节点。只要输出的话题和命令格式一致，控制桥接节点就可以继续工作。

### 4\.8\.4 案例 4\-7 代码说明

命令发布节点创建 Publisher：

```Python
self.publisher = self.create_publisher(String, TOPIC_NAME, 10)
```

发布命令：

```Python
msg = String()
msg.data = command
self.publisher.publish(msg)
```

控制桥接节点创建订阅：

```Python
self.subscription = self.create_subscription(
    String,
    COMMAND_TOPIC,
    self.on_command,
    10,
)
```

收到命令后，根据字符串选择请求：

```Python
if command == "prepare":
    body = to_json_body({"mode": MODE_PREPARE})
    self.send_rpc_request_async(API_CHANGE_MODE, body)
```

短距离移动命令先发送运动请求，再创建定时器发送停止请求：

```Python
if command == "move_forward_short":
    body = to_json_body({"vx": 0.2, "vy": 0.0, "vyaw": 0.0})
    self.send_rpc_request_async(API_MOVE, body)
    self.stop_timer = self.create_timer(1.5, self.on_stop_timer)
```

这里的控制桥接节点就是一个小型行为接口：它把上层命令翻译成底层服务请求。

### 4\.8\.5 案例 4\-7 运行方式与效果观察

打开第一个终端，运行桥接节点：

```Bash
cd /home/booster/Workspace/CourseCode/chapter_04_ros2_control
python3 command_service_bridge.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTE3OTVjZDFjYWMyZTQ4ZjdkYzcwMmZjMDM5YTY1YmVfOTAzNTkzNWIzZjg1NzczMzhjYjdkNDEyYjQwYjFjZDJfSUQ6NzY2MjI4NjUxMDIwODk3Nzg4OF8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

打开第二个终端，发布准备模式命令：

```Bash
python3 command_publisher.py --command prepare
```

发布行走模式命令：

```Bash
python3 command_publisher.py --command walk
```

发布短距离移动命令：

```Bash
python3 command_publisher.py --command move_forward_short
```

发布停止命令：

```Bash
python3 command_publisher.py --command stop
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZGFjODY0YmI0ZmM3YTdjNGExZjA5YWIyMmQ4OGJhNjlfMjg3OWU0OTkxZWVlZjMxNTgyNmQ5Y2M3MTQxN2JlZThfSUQ6NzY2MjI4NjYxMjYwODUxOTA5Nl8xNzg1ODM5NDMxOjE3ODU5MjU4MzFfVjM)

可以再打开第三个终端观察命令话题：

```Bash
ros2 topic echo /k1_demo/control_command
```

观察重点：

- 命令发布节点是否把字符串发布到 Topic；

- 桥接节点是否收到命令；

- 桥接节点是否打印对应 Service 请求；

- K1 是否执行对应运动或动作。

触发全身舞蹈前，必须确认空间安全：

```Bash
python3 command_service_bridge.py --allow-whole-body-dance
python3 command_publisher.py --command whole_body_dance
```

如果只是理解桥接逻辑，建议先使用 `prepare`、`walk`、`move_forward_short` 和 `stop`。

如果桥接节点启动时没有添加 `--allow-whole-body-dance`，即使收到 `whole_body_dance` 命令，也只会打印警告，不会转发全身舞蹈请求。

### 4\.8\.6 案例 4\-7 常见问题排查

问题 1：命令发布了，但桥接节点没有收到。

检查：

- 桥接节点是否正在运行；

- 两个程序是否使用同一个话题 `/k1_demo/control_command`；

- 消息类型是否为 `std_msgs/msg/String`；

- `ros2 topic echo /k1_demo/control_command` 是否能看到命令。

问题 2：桥接节点收到命令，但机器人没有动作。

检查：

- `/booster_rpc_service` 是否存在；

- 桥接节点是否打印服务响应；

- 机器人是否处于允许运动或动作的状态；

- 对于 `move_forward_short`，是否先发送过 `prepare` 和 `walk`。

问题 3：输入了未知命令。

`command_publisher.py` 会限制命令范围。如果使用其他方式发布命令，桥接节点会打印未知命令警告。应使用本章列出的命令字符串。

## 4\.9 为什么要走 ROS2 Service，而不是只用 Python 直接调 SDK

### 4\.9\.1 直接 SDK 调用的优势

直接 SDK 调用有明确优势：

- 代码短；

- 容易理解；

- 适合建立第一个控制闭环；

- 适合快速确认机器人能否运动。

Chapter 3 的 `hello_robot.py` 就属于这种方式。它让读者先理解机器人模式、速度参数和停止逻辑。

### 4\.9\.2 ROS2 Service 的优势

ROS2 Service 的优势不在于“写起来更短”，而在于系统组织能力。

第一，模块解耦。感知节点、控制节点和行为节点可以分开。控制节点不需要知道图像处理细节，感知节点也不需要知道 K1 控制服务细节。

第二，可观察。Topic 和 Service 都可以通过命令行查看。出现问题时，可以逐层检查：话题有没有数据、服务是否存在、消息类型是否正确、请求是否有响应。

第三，可替换。案例 4\-7 中，命令发布节点可以被替换成视觉检测节点。只要它仍然向同一个 Topic 发布约定格式的数据，控制桥接节点就可以继续工作。

第四，可扩展。后续 Behavior Tree（行为树）、追球控制和视觉踢球都需要多个模块协作。ROS2 提供了这些模块之间的通信基础。

### 4\.9\.3 从本章案例看后续系统雏形

本章的多个案例组合起来，已经形成后续系统的雏形：

```Plaintext
自定义 Topic 发布订阅
  ↓
订阅系统图像 Topic
  ↓
调用 K1 控制 Service
  ↓
Topic 命令触发 Service 控制
```

在后续章节中，`command_publisher.py` 的角色可以被视觉节点替换。视觉节点不再发布 `prepare` 这样的手写命令，而是发布“足球在左侧”“足球在前方”“目标丢失”等结构化信息。控制桥接节点或行为节点根据这些信息，再决定发送前进、转向、停止或踢球请求。

这就是从单个控制脚本走向机器人系统的关键一步。

## 4\.10 本章小结

### 4\.10\.1 本章建立的 ROS2 能力

本章完成了从单程序控制到多节点通信的过渡。

首先，本章介绍了 Node、Topic、Service 和 Message。Node 是运行中的功能模块，Topic 适合持续数据流，Service 适合一次请求与响应，Message 和 Service 类型决定数据结构。

其次，本章通过两个 Python 文件演示了 Topic 发布和订阅。发布者和订阅者不直接调用彼此函数，而是通过话题名称和消息类型连接。

再次，本章订阅了 K1 的图像话题 `/boostercamera/head/rgb`，查看了 `sensor_msgs/msg/Image` 的宽、高、编码、步长和数据长度，为后续视觉章节打基础。

然后，本章通过 `/booster_rpc_service` 分别调用了基础运动、半身动作和全身舞蹈，说明同一个 Service 入口可以承载不同 `api_id` 和 `body` 请求。

最后，本章用命令 Topic 触发 Service 控制，展示了多个 Node 分工协作的基本形态。

### 4\.10\.2 进入下一章

进入下一章后，课程仍然处在控制系统部分，但关注点会从 ROS2 通信接口转向示教与基础动作。读者将进一步理解动作如何被记录、回放和组织。

到这里，读者已经具备一个重要基础：机器人应用不是把所有逻辑写进一个文件，而是让不同节点通过 Topic 和 Service 协作。这个基础会在后续动作生成、视觉感知、追球控制和视觉踢球中反复使用。

