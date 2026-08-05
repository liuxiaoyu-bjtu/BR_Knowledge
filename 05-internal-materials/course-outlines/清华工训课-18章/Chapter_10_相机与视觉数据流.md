# Chapter\_10\_相机与视觉数据流

# Chapter 10｜相机与视觉数据流

> Chapter 9 完成了动作生成系统的综合项目。
> 
> 进入 Chapter 10 后，课程转入感知系统。感知系统要解决的问题是：机器人如何从传感器获得环境信息，并把这些信息变成后续检测、定位、控制和行为决策能够使用的数据。
> 
> 

对 Booster K1 来说，视觉感知的第一步不是直接运行目标检测模型，而是获得图像。只有确认相机话题存在、图像消息连续发布、编码能够正确转换、RGB 图像和深度图能够保存和显示，后续使用 YOLO 足球目标检测检测、空间定位、自主追球和视觉踢球才有意义。

本章围绕 K1 相机与 ROS2（Robot Operating System 2，机器人操作系统 2）视觉数据流展开。学习者将完成四类实践案例：

1. 检查相机图像话题并打印图像消息元信息；

2. 读取 RGB（Red、Green、Blue，红绿蓝彩色图像）并保存图片；

3. 读取深度图并保存原始深度与伪彩色结果；

4. 在有图形界面的环境中实时显示相机画面。

本章程序只读取相机数据，不向机器人发送运动指令。运行时仍应保持基本安全习惯：机器人放置稳定，头部相机无遮挡，周围不要有人员或物体贴近机器人运动范围。如果机器人同时运行了其他控制程序并出现异常姿态，应立即按下机器人背部 `STAND` 按钮，让机器人回到可控状态。

## 10\.1 感知系统从哪里开始

人形机器人要完成自主追球或视觉踢球，首先需要知道环境中的足球在哪里、人是否出现在画面中、地面和障碍物大致位于什么方向，这些信息都来自感知系统。

感知系统的入口通常是传感器。K1 的头部相机可以持续采集图像，并通过 ROS2 话题发布到系统中。视觉程序订阅这些话题后，才能进一步做图像转换、目标检测、空间定位和调试显示。

可以把视觉数据流理解为下面的链路：

```Plaintext
K1 头部相机
  ↓
相机驱动与相机节点
  ↓
ROS2 图像话题
  ↓
视觉程序订阅图像
  ↓
OpenCV 图像处理
  ↓
目标检测或空间定位
```

这条链路中，每一层都可能影响最终效果。相机没有发布图像，YOLO 就没有输入；图像编码没有处理正确，检测模型看到的可能是颜色错乱或形状异常的画面；深度图与 RGB 图像没有对齐，足球距离估计就可能明显偏差。因此，视觉系统的第一章必须先把“图像从哪里来、如何被程序读到、如何确认它是对的”讲清楚。

### 10\.1\.1 从相机到视觉节点的数据链路

K1 相机不是把一张普通图片文件交给程序，而是在机器人系统中持续发布图像消息。图像消息是一种实时数据流，视觉程序通常不会主动“拍一张照片”，而是订阅某个 Topic（话题），每当相机发布新帧时，程序的回调函数就会被调用。

这个过程和普通文件读取不同：

```Plaintext
普通图片文件:
读取 image.jpg -> 得到一张固定图片

机器人相机图像:
订阅图像 Topic -> 持续收到一帧一帧的图像消息
```

视觉节点接收到的每一帧图像都带有时间戳、图像宽度、高度、编码格式和原始数据。后续程序要做的第一件事，就是把 ROS2 图像消息转换成 OpenCV（Open Source Computer Vision Library，开源计算机视觉库）能够处理的图像矩阵。

### 10\.1\.2 Chapter 10 与后续章节的分工

Chapter 10 只处理视觉输入层，不直接检测足球，也不控制机器人头部或身体运动。

本章与后续章节的关系如下：

|章节|解决的问题|输入|输出|
|---|---|---|---|
|Chapter 10|如何获得和处理相机图像流|K1 相机 Topic|可保存、可显示、可转换的 RGB/深度图|
|Chapter 11|如何用 YOLO 检测足球|RGB 图像|足球像素坐标、检测框、置信度|
|Chapter 12|如何把检测结果转为空间位置|检测框、深度图、相机参数|足球相对机器人位置|
|Chapter 13\-16|如何根据感知结果组织行为|足球位置、目标状态|搜索、追球、停稳、踢球|

这意味着 Chapter 10 的完成标准不是“机器人已经会追球”，而是学习者能够确认：

- 相机图像 Topic 正在发布；

- 程序能够连续收到图像帧；

- 图像编码能够正确转换；

- RGB 图像可以保存和查看；

- 深度图可以保存并生成伪彩色图；

- 有图形界面时可以实时显示画面；

- 出现无图像、编码错误、窗口打不开等问题时知道如何排查。

## 10\.2 K1 相机话题与运行前检查

在 ROS2 系统中，相机图像通过 Topic 发布。Topic 可以理解为一个持续更新的数据频道。相机节点负责向频道中发布图像，视觉节点负责订阅频道并读取图像。

正式写视觉程序前，应先用命令行确认相机话题存在。这样可以把问题分成两类：

- 如果命令行看不到图像 Topic，优先排查相机服务或 ROS2 环境；

- 如果命令行能看到图像 Topic，但 Python 程序收不到数据，优先排查程序中的话题名称、消息类型和运行环境。

### 10\.2\.1 RGB、深度图与 camera\_info

K1 视觉任务中常用的相机话题包括：

```Plaintext
/boostercamera/head/rgb
/boostercamera/head/rgb/camera_info
/boostercamera/head/depth
/boostercamera/head/depth/camera_info
/boostercamera/head/right/rgb
/boostercamera/head/right/rgb/camera_info
```

这些话题的作用不同。

|话题|主要作用|
|---|---|
|`/boostercamera/head/rgb`|左目 RGB 彩色图像，适合目标检测、显示和保存|
|`/boostercamera/head/rgb/camera_info`|RGB 相机内参信息，用于像素到空间方向的计算|
|`/boostercamera/head/depth`|与左目图像对齐的深度图，用于估计距离|
|`/boostercamera/head/depth/camera_info`|深度相机内参信息|
|`/boostercamera/head/right/rgb`|右目 RGB 图像，在双目相关任务中可能使用|
|`/boostercamera/head/right/rgb/camera_info`|右目相机内参信息|

本章默认使用：

```Plaintext
/boostercamera/head/rgb
/boostercamera/head/depth
```

前者用于 RGB 图像读取、保存和显示；后者用于深度图读取和保存。`camera_info` 不在本章展开计算，但学习者需要知道它的存在。进入 Chapter 12 后，像素坐标要转成空间位置，就会用到相机内参。

### 10\.2\.2 raw 图像与统一图像话题

有些 K1 环境中还会看到类似下面的话题：

```Plaintext
/boostercamera/head/raw/rgb
```

`raw` 表示更接近原始输出的图像流。它常见的编码可能是 `NV12`，需要手动转换后才能作为 OpenCV BGR 图像使用。

在后续足球检测和空间定位任务中，建议优先使用统一后的 RGB 话题：

```Plaintext
/boostercamera/head/rgb
```

原因是它更适合作为后续模块的公共输入，尤其是要和深度图、相机内参、目标检测和空间定位组合时，统一话题更容易保持数据一致。如果当前机器人环境只发布 `raw/rgb`，也可以在本章代码中通过 `--topic /boostercamera/head/raw/rgb` 临时切换。

可以用下面的命令查看当前系统有哪些相机话题：

```Bash
ros2 topic list | grep boostercamera
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Y2NkNWYxYWNlYjI4ZDg5NTlhNzIwMzMxN2NiYTBhZjZfN2UzMjgyMjRiZjM5NGRkMWRjYTlmNWFiNzQ3MGYyZmJfSUQ6NzY2MjU4NzMzNjM0OTI0MDUyMl8xNzg1ODM5NDg2OjE3ODU5MjU4ODZfVjM)

也可以查看某个图像话题的类型和发布者数量：

```Bash
ros2 topic info /boostercamera/head/rgb
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTk4ZjFhYTRjYTc2OGUyMjhiYWE5MDAzZThhY2NmY2FfYWU3MzczOWFkNGJlYTI4ZjA2YjNiZDM1MTkyNDVjYjdfSUQ6NzY2MjU4NzQ4NzgzMjk1MjEwN18xNzg1ODM5NDg2OjE3ODU5MjU4ODZfVjM)

正常情况下，类型应为：

```Plaintext
sensor_msgs/msg/Image
```

并且 `Publisher count` 应大于 0。`Publisher count` 为 0 表示当前没有节点正在发布该话题，即使话题名出现过，程序也收不到连续图像。

## 10\.3 `sensor_msgs/msg/Image` 图像消息结构

ROS2 中常用的图像消息类型是：

```Plaintext
sensor_msgs/msg/Image
```

它不是普通的 `.jpg` 或 `.png` 图片文件，而是一条结构化消息。可以用下面的命令查看接口定义：

```Bash
ros2 interface show sensor_msgs/msg/Image
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OWE1YWQ4MWJiYWM1NWM3NWI2MWRiMTM4Y2VkYTk4NzVfNDJhODJmZDY2ODdlYzJkZTllMTc0Mzg1ZjY4MzU3MzdfSUQ6NzY2MjU4Nzc0MzQ0MDYwNDEzNV8xNzg1ODM5NDg2OjE3ODU5MjU4ODZfVjM)

在视觉程序中，最常用的字段包括：

|字段|含义|
|---|---|
|`header`|时间戳和坐标帧信息|
|`height`|图像高度，单位是像素|
|`width`|图像宽度，单位是像素|
|`encoding`|图像编码格式，例如 `bgr8`、`rgb8`、`nv12`、`16UC1`|
|`is_bigendian`|数据字节序标记，普通图像处理中较少直接修改|
|`step`|每一行图像数据占用的字节数|
|`data`|原始图像字节数组|

### 10\.3\.1 宽、高、编码、步长和 data

`height` 和 `width` 决定图像尺寸。假设一帧 RGB 图像的宽度是 544，高度是 448，那么它表示一个由 544 列、448 行像素组成的二维画面。

`encoding` 决定 `data` 应该如何解释。相同的 `data` 字节，如果编码解释错误，得到的图像就会变色、变形，甚至无法转换。

`step` 表示每一行图像数据的字节数。对于普通 `bgr8` 图像，每个像素通常有 3 个字节，因此 `step` 通常接近 `width * 3`。但对于 `NV12`、深度图等编码，`step` 的含义和普通三通道图像不同，不能简单套用。

`data` 是图像真正的原始内容。它通常非常长，不适合完整打印。查看图像消息时，应使用：

```Bash
ros2 topic echo /boostercamera/head/rgb --no-arr
```

`--no-arr` 会省略长数组，只保留宽、高、编码、时间戳等元信息。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZmUxOTVjZGFkODIwN2NjY2I0MjRkZjAxZGRlOGI2N2NfMzE4ZjI2NzEyN2QzMDgxZWM1YzZjYWM5YmU1MzZkOGZfSUQ6NzY2MjU4ODQzOTg3MTk5OTE1N18xNzg1ODM5NDg2OjE3ODU5MjU4ODZfVjM)

### 10\.3\.2 图像帧率与延迟

相机图像是实时数据流。视觉程序处理每一帧都需要时间，如果处理速度低于相机发布速度，就可能出现延迟或积压。

例如，相机以 20 FPS（Frames Per Second，每秒帧数）发布图像，表示每秒约有 20 帧进入系统。如果检测模型每帧推理需要 100 毫秒，理论上每秒只能处理约 10 帧。此时程序可能出现两类现象：

- 画面显示比真实环境慢；

- 检测结果滞后于机器人当前看到的画面。

本章的程序只做轻量处理，主要用于确认图像流和保存调试图片。进入 Chapter 11 后，YOLO 推理会增加计算量，需要进一步关注帧率和延迟。

## 10\.4 图像编码与 OpenCV 转换

视觉程序真正处理图像时，通常希望得到 OpenCV 图像。OpenCV 在 Python 中通常使用 NumPy 数组表示图像，例如：

```Python
frame.shape
```

可能输出：

```Plaintext
(448, 544, 3)
```

这表示图像高度为 448、宽度为 544、有 3 个颜色通道。

ROS2 图像消息不能直接交给 OpenCV 处理，需要先转换：

```Plaintext
sensor_msgs/msg/Image
  ↓
读取 encoding
  ↓
cv_bridge 或手动编码转换
  ↓
OpenCV BGR 图像
  ↓
保存、显示、检测、调试
```

### 10\.4\.1 OpenCV BGR 图像是什么

OpenCV 默认使用 BGR 通道顺序。BGR 表示 Blue、Green、Red，也就是蓝、绿、红。一般图像处理中更常见的是 RGB，即红、绿、蓝。两者表示的都是彩色图像，只是通道顺序不同。

如果把 RGB 当成 BGR 使用，画面不会一定报错，但颜色可能明显异常。例如红色足球可能显示偏蓝，后续基于颜色的处理会受到影响。因此，视觉程序中经常会看到 `cv2.cvtColor()`，它用于在不同颜色空间或通道顺序之间转换。

本章代码将不同来源的图像统一转换成 OpenCV BGR 图像，后续保存、显示和检测都基于这个格式。

### 10\.4\.2 `cv_bridge` 的作用

`cv_bridge` 是 ROS 图像消息与 OpenCV 图像之间的转换工具。对于常见编码，例如 `bgr8`、`rgb8`、`mono8`，可以使用：

```Python
bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
```

这行代码的含义是：把 ROS2 的 `Image` 消息转换成 OpenCV 可用的 BGR 图像。

但 `cv_bridge` 不是所有编码都能自动解决。对于 `NV12` 这类视频编码格式，本章代码会先把原始字节整理成 YUV 图像，再使用 OpenCV 转换为 BGR。

### 10\.4\.3 NV12、BGR8、RGB8、MONO8

本章需要重点理解几类编码。

|编码|含义|处理方式|
|---|---|---|
|`bgr8`|8 位三通道 BGR 图像|可直接通过 `cv_bridge` 转为 OpenCV BGR|
|`rgb8`|8 位三通道 RGB 图像|通过 `cv_bridge` 转为 BGR|
|`mono8`|8 位单通道灰度图|通过 `cv_bridge` 转为 BGR 或灰度|
|`nv12`|YUV 视频编码格式|需要先整理字节数组，再执行 `cv2.COLOR_YUV2BGR_NV12`|
|`16UC1`|16 位无符号单通道图像，深度图常用|通常按毫米解释，再转成米|
|`32FC1`|32 位浮点单通道图像，深度图可能使用|通常已经是米制深度|

`NV12` 转换的核心逻辑如下：

```Python
yuv = np.frombuffer(msg.data, dtype=np.uint8).reshape(
    (msg.height * 3 // 2, msg.width)
)
yuv = np.ascontiguousarray(yuv)
frame_bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_NV12)
```

这段代码体现了一个重要原则：视觉模型之前，必须先保证图像数据解释正确。很多视觉程序失败，不是因为模型能力不足，而是因为输入图像在编码转换阶段已经出错。

## 10\.5 实践案例 10\-1：检查并打印相机图像流

本案例对应代码目录：

```Plaintext
CourseCode/chapter_10_camera_vision_flow/
```

使用脚本：

```Plaintext
camera_topic_inspector.py
```

它的任务很简单：订阅一个图像话题，打印前几帧的元信息，然后退出。这个脚本不保存图片、不显示窗口、不处理像素，只用于确认图像流是否存在。

### 10\.5\.1 实践目标

本案例完成三件事：

1. 确认图像话题能被 Python 节点订阅；

2. 打印图像宽、高、编码、步长和数据长度；

3. 为后续图像转换和保存排除基础问题。

如果本案例不能收到图像，后续 RGB 保存、深度保存、YOLO 检测都不应继续执行，应先排查图像流。

### 10\.5\.2 文件目录

第 10 章代码目录建议放在 K1 的工作目录中，例如：

```Plaintext
/home/booster/Workspace/chapter_10_camera_vision_flow/
```

目录结构如下：

```Plaintext
chapter_10_camera_vision_flow/
├─ README.md
├─ vision_utils.py
├─ camera_topic_inspector.py
├─ rgb_image_capture.py
├─ depth_image_capture.py
└─ live_image_viewer.py
```

其中 `vision_utils.py` 保存图像转换和保存的公共函数，其余脚本分别对应不同实践任务。

### 10\.5\.3 运行方式

进入代码目录并加载 ROS2 环境：

```Bash
cd /home/booster/Workspace/chapter_10_camera_vision_flow
source /opt/ros/humble/setup.bash
```

检查默认 RGB 图像话题：

```Bash
python3 camera_topic_inspector.py --topic /boostercamera/head/rgb --frames 5
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=N2M4NjNmMDdhMWY2MjdjYWUwNjk2MzQzYTFkYTY2OThfMjcxYzc4Zjk2ZDY5ZjEwZTc2YTJlMGIxMGZiNjI2ZjRfSUQ6NzY2MjU5MTEwNTAzNDA0NjY2NF8xNzg1ODM5NDg2OjE3ODU5MjU4ODZfVjM)

如果当前机器人只发布 raw 图像，可以临时切换：

```Bash
python3 camera_topic_inspector.py --topic /boostercamera/head/raw/rgb --frames 5
```

### 10\.5\.4 效果说明

正常情况下，终端会打印类似信息：

```Plaintext
frame=1 stamp=... frame_id=... width=544 height=448 encoding=rgb8 step=... data_len=...
frame=2 stamp=... frame_id=... width=544 height=448 encoding=rgb8 step=... data_len=...
```

具体宽高和编码以当前 K1 系统输出为准。学习者应关注四点：

- 是否连续收到多帧；

- `width` 和 `height` 是否合理；

- `encoding` 是否是后续代码支持的格式；

- `data_len` 是否不是 0。

如果看到 `encoding=nv12`，说明后续 RGB 转换需要走 `NV12 -> BGR` 路径。如果看到 `encoding=bgr8` 或 `rgb8`，通常可以通过 `cv_bridge` 转换。

## 10\.6 实践案例 10\-2：读取 RGB 图像并保存图片

检查图像流之后，下一步是把 ROS2 图像消息转换成 OpenCV BGR 图像，并保存为普通图片文件。

本案例使用脚本：

```Plaintext
rgb_image_capture.py
```

它会订阅 RGB 图像话题，持续缓存最新一帧。终端中按 Enter 后，程序会保存当前图像。

### 10\.6\.1 实践目标

本案例要完成以下任务：

1. 订阅 K1 RGB 图像话题；

2. 根据 `encoding` 转换图像；

3. 将图像统一整理为 OpenCV BGR 格式；

4. 保存彩色图、灰度图和水印图；

5. 通过保存结果确认相机画面是否正常。

保存图片不仅是为了记录画面，也是一种重要调试方式。后续检测效果不好时，可以先保存当前输入图像，检查图像是否模糊、过曝、偏色、遮挡、目标太远或目标不在画面中。

### 10\.6\.2 关键代码含义

RGB 图像转换由 `vision_utils.py` 中的 `ros_image_to_bgr()` 完成。它会先读取：

```Python
encoding = (msg.encoding or "").lower()
```

然后按编码选择处理方式。

对于 `NV12`：

```Python
yuv = np.frombuffer(msg.data, dtype=np.uint8)
yuv = yuv.reshape((msg.height * 3 // 2, msg.width))
frame_bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_NV12)
```

对于 `bgr8`、`rgb8`、`mono8`：

```Python
frame_bgr = bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
```

保存图片由 `save_bgr_variants()` 完成。一次保存三种结果：

|文件|作用|
|---|---|
|`*_color.jpg`|保留彩色画面|
|`*_gray.jpg`|保存灰度图，便于理解单通道图像|
|`*_watermark.jpg`|带时间水印，便于调试记录|

### 10\.6\.3 运行方式

运行默认 RGB 话题：

```Bash
python3 rgb_image_capture.py --topic /boostercamera/head/rgb
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTI4YmQwZTAxZDA4NTExM2ZkYmZjNDdkYzI0YjIzNDNfZGEwYjYzMDY5OTZmMTViNThlZjg1M2Q5M2Q2MDRkNWJfSUQ6NzY2MjU5MTk1NTc4NDcxNTI1Ml8xNzg1ODM5NDg2OjE3ODU5MjU4ODZfVjM)

程序启动后，终端会提示：

```Plaintext
订阅 RGB 图像话题: /boostercamera/head/rgb
图片保存目录: ./saved_images
终端中按 Enter 保存当前图像，按 Ctrl+C 退出。
```

看到持续帧数输出后，按 Enter 保存当前图像。保存目录默认为：

```Plaintext
./saved_images/
```

如果当前图像话题为 raw：

```Bash
python3 rgb_image_capture.py --topic /boostercamera/head/raw/rgb
```

如果运行环境不方便按 Enter，可以收到第一帧后自动保存一次：

```Bash
python3 rgb_image_capture.py \
  --topic /boostercamera/head/rgb \
  --save-on-first-frame
```

### 10\.6\.4 效果说明

保存成功后，会看到类似输出：

```Plaintext
已保存彩色图: ./saved_images/rgb_20260708_213000_color.jpg
已保存灰度图: ./saved_images/rgb_20260708_213000_gray.jpg
已保存水印图: ./saved_images/rgb_20260708_213000_watermark.jpg
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzMxMDFjNjljNGFkY2M3N2U2OTNhNDgwNDc4MmQ5ZWZfZTgzYWM0MWUyNTgzODQ3ZGM5MjRhYTEwMTgwOGRhMzJfSUQ6NzY2MjU5MjY5NDQ4MDM5MTM2N18xNzg1ODM5NDg2OjE3ODU5MjU4ODZfVjM)

打开彩色图，应能看到 K1 头部相机当前视野。若图像颜色明显异常，优先检查 `encoding` 是否被正确处理。若图像很暗或模糊，应调整环境光照、目标距离和相机视角。

### 10\.6\.5 无窗口保存版本的意义

机器人开发经常通过 SSH、VSCode Remote 或远程终端完成。这类环境不一定支持 OpenCV 窗口显示。如果强行运行 `cv2.imshow()`，可能出现窗口打不开、程序卡住或报错。

因此，本案例默认不弹出窗口，只在终端中保存图片。这样更适合远程环境，也更接近后续机器人系统的运行方式：视觉节点在后台处理数据，调试时通过保存图片和打印日志确认输入是否正确。

## 10\.7 实践案例 10\-3：读取深度图并生成可视化图

RGB 图像告诉机器人“画面中有什么”和“目标在图像中的哪个方向”。但只看 RGB 图像，通常无法直接得到目标距离。深度图提供每个像素对应的距离信息，是后续空间理解的重要输入。

本案例使用脚本：

```Plaintext
depth_image_capture.py
```

它会订阅深度图话题，将深度图转换为米制数组，并保存原始深度图、米制数组和伪彩色深度图。

### 10\.7\.1 深度图表示的是什么

深度图也是一张图，但它的像素值不是颜色，而是距离。

RGB 图像中的一个像素通常表示颜色：

```Plaintext
(B, G, R)
```

深度图中的一个像素通常表示距离：

```Plaintext
depth = 1.25 m
```

深度图常见编码包括：

|编码|含义|
|---|---|
|`16UC1`|16 位无符号单通道图像，常以毫米保存深度|
|`32FC1`|32 位浮点单通道图像，常以米保存深度|

如果深度图是 `16UC1`，像素值 `1250` 通常表示 `1.250 m`。本章代码会把它转换为米：

```Python
depth_m = raw_depth.astype(np.float32) * 0.001
```

如果深度图是 `32FC1`，通常可以直接按米处理。

### 10\.7\.2 保存原始深度图与伪彩色深度图

深度图不适合直接用普通图片方式观察。因为人眼看的是颜色和亮度，而深度值本身是一组距离数字。为了方便观察，可以把深度范围映射成颜色，生成伪彩色图。

本章代码会保存三类文件：

|文件|作用|
|---|---|
|`*_raw_mm.png`|原始深度图，按毫米保存为 16 位 PNG|
|`*_meters.npy`|米制深度数组，适合后续 Python 数值分析|
|`*_color.png`|伪彩色深度图，适合人眼观察|

伪彩色图只用于调试观察，不应替代真实深度数组参与后续计算。进入 Chapter 12 后，如果要估计足球距离，应使用米制深度数组或实时深度消息，而不是使用彩色化后的图片。

### 10\.7\.3 运行方式

运行深度图保存程序：

```Bash
python3 depth_image_capture.py --topic /boostercamera/head/depth
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OGE1NmFlZmY5MjYzNTU0OGI5NmQ3OTlhYTU1M2FmOGRfYTA0NjhlYTM4YWZlMjA1YTMwNmE5Yzg4ODkzYzVlZmZfSUQ6NzY2MjU5MzQ2NDQwOTAwMTE5NV8xNzg1ODM5NDg2OjE3ODU5MjU4ODZfVjM)

程序启动后，终端中按 Enter 保存当前深度图。也可以自动保存第一帧：

```Bash
python3 depth_image_capture.py \
  --topic /boostercamera/head/depth \
  --save-on-first-frame
```

如果希望调整伪彩色图显示范围，例如只关心 0 到 3 米：

```Bash
python3 depth_image_capture.py \
  --topic /boostercamera/head/depth \
  --max-range-m 3.0
```

### 10\.7\.4 效果说明

正常输出类似：

```Plaintext
已接收深度帧: 20, shape=(448, 544), encoding=16UC1, valid=..., range=0.500..5.800m
已保存原始深度图: ./saved_depth_images/depth_..._raw_mm.png
已保存米制深度数组: ./saved_depth_images/depth_..._meters.npy
已保存伪彩色深度图: ./saved_depth_images/depth_..._color.png
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YWYwYTdhMGE1ZWVhYzhhMTQ3MjBjYTAwN2VkY2Y4YzBfZTFlZjZmYjQxMDRhMzM0NDMyNzUyNmYyZjAyM2FlNjVfSUQ6NzY2MjU5MzczODIxMjMzMDczNl8xNzg1ODM5NDg2OjE3ODU5MjU4ODZfVjM)

如果有效深度数量很少，可能是目标太近、太远、表面反光、相机被遮挡，或深度话题没有正常发布。K1 深度数据有有效工作范围，超出范围后深度值可能无效。

### 10\.7\.5 RGB 与深度图对齐的意义

后续足球定位通常会先在 RGB 图像中检测足球，再到深度图中读取足球区域的距离。这个过程要求 RGB 图像和深度图在空间上尽量对齐。

可以先理解为：

```Plaintext
YOLO 在 RGB 图像中框出足球
  ↓
找到足球框覆盖的像素区域
  ↓
在深度图对应区域读取距离
  ↓
估计足球相对机器人有多远
```

如果 RGB 图和深度图没有对齐，足球检测框对应到深度图时可能落在背景、地面或其他物体上，距离估计会错误。Chapter 12 会继续展开像素坐标、深度值和机器人坐标之间的关系。

## 10\.8 实践案例 10\-4：实时图像显示

保存图片适合远程调试，但有图形界面时，实时显示图像更直观。本案例使用：

```Plaintext
live_image_viewer.py
```

它会订阅 RGB 图像话题，转换成 OpenCV BGR 图像，并在窗口中实时显示。

### 10\.8\.1 有图形界面的运行方式

在支持图形界面的环境中运行：

```Bash
python3 live_image_viewer.py --topic /boostercamera/head/rgb
```

窗口打开后：

- 按 `s` 保存当前图像；

- 按 `q` 或 `Esc` 退出；

- 终端中按 `Ctrl+C` 也可以退出。

如果当前环境使用 raw 图像：

```Bash
python3 live_image_viewer.py --topic /boostercamera/head/raw/rgb
```

实时显示程序的核心逻辑是：

```Plaintext
收到图像消息
  ↓
转换成 OpenCV BGR 图像
  ↓
cv2.imshow() 显示窗口
  ↓
cv2.waitKey() 刷新窗口并读取按键
```

`cv2.waitKey()` 不能省略。OpenCV 窗口需要它来刷新画面和处理键盘事件。

### 10\.8\.2 无图形界面时的替代方案

很多 K1 开发环境并没有可用图形界面。例如通过普通 SSH 连接机器人时，`cv2.imshow()` 可能无法打开窗口。此时不要把窗口问题误判为相机问题。

可以改用下面的方式确认相机是否正常：

```Bash
python3 camera_topic_inspector.py --topic /boostercamera/head/rgb --frames 5
python3 rgb_image_capture.py --topic /boostercamera/head/rgb --save-on-first-frame
```

只要能打印图像元信息，并且能保存出正常图片，就说明相机图像流本身是可用的。窗口打不开只是图形显示环境问题。

如果确实需要在远程环境中显示窗口，应确认：

- 是否使用支持图形转发的登录方式；

- `DISPLAY` 环境变量是否存在；

- 当前 OpenCV 是否带 GUI 支持；

- 本地系统是否允许远程窗口显示。

这些问题属于图形界面环境问题，不是 ROS2 图像话题本身的问题。

## 10\.9 常见问题排查

### 10\.9\.1 `ros2 topic list` 看不到相机话题

先确认终端是否加载 ROS2 环境：

```Bash
source /opt/ros/humble/setup.bash
```

再查看：

```Bash
ros2 topic list | grep boostercamera
```

如果仍看不到相机话题，检查相机服务是否启动、机器人系统是否正常运行、相机硬件是否被遮挡或异常占用。

### 10\.9\.2 `ros2 topic info` 中 `Publisher count` 为 0

`Publisher count` 为 0 表示当前没有节点正在发布该话题。此时 Python 程序即使订阅成功，也不会收到任何图像。

处理顺序：

1. 确认话题名称是否写对；

2. 查看是否存在相近话题，例如 `/boostercamera/head/raw/rgb`；

3. 重启或恢复相机相关服务；

4. 再次执行 `ros2 topic info`。

### 10\.9\.3 Python 程序提示导入 `sensor_msgs` 失败

通常是 ROS2 环境没有加载。运行：

```Bash
source /opt/ros/humble/setup.bash
```

再测试：

```Bash
python3 -c "from sensor_msgs.msg import Image; print('sensor_msgs ok')"
```

如果仍失败，说明当前 Python 环境与 ROS2 环境不一致，需要切换到机器人系统中正确的 Python 环境。

### 10\.9\.4 Python 程序提示导入 `cv_bridge` 失败

`cv_bridge` 是 ROS 图像和 OpenCV 图像之间的转换工具。导入失败通常说明当前环境缺少 ROS2 图像依赖，或没有使用 ROS2 对应的 Python 环境。

先测试：

```Bash
python3 -c "from cv_bridge import CvBridge; print('cv_bridge ok')"
```

若失败，优先确认：

- 是否已经 `source /opt/ros/humble/setup.bash`；

- 是否在 K1 的 ROS2 环境中运行；

- 是否使用了与 ROS2 不匹配的 Conda 或虚拟环境。

### 10\.9\.5 图像转换失败，提示不支持的编码

查看当前图像编码：

```Bash
ros2 topic echo /boostercamera/head/rgb --no-arr
```

重点看 `encoding` 字段。如果编码不是本章代码支持的 `bgr8`、`rgb8`、`mono8`、`nv12`，需要先确认该话题是否适合作为 RGB 图像输入。

如果 `/boostercamera/head/rgb` 编码异常，可以尝试：

```Bash
python3 camera_topic_inspector.py --topic /boostercamera/head/raw/rgb
```

确认 raw 图像是否存在以及编码是什么。

### 10\.9\.6 保存出的 RGB 图片颜色异常

常见原因是颜色通道顺序或编码处理错误。

排查步骤：

1. 查看图像消息中的 `encoding`；

2. 如果是 `nv12`，确认代码走了 `cv2.COLOR_YUV2BGR_NV12`；

3. 如果是 `rgb8`，确认最终转换到 OpenCV BGR；

4. 换一个颜色明显的物体放到画面中，观察红、绿、蓝是否正常。

### 10\.9\.7 图像窗口打不开

窗口打不开通常不是相机问题，而是图形环境问题。先运行无窗口脚本：

```Bash
python3 rgb_image_capture.py --topic /boostercamera/head/rgb --save-on-first-frame
```

如果能保存图片，说明图像流正常。此时可以不使用 `live_image_viewer.py`，继续用保存图片方式完成本章实践。

### 10\.9\.8 深度图全黑或有效深度很少

深度图全黑可能有几类原因：

- 目标距离超出深度相机有效范围；

- 场景中反光、透明或吸光材料较多；

- 深度图话题没有正常发布；

- 深度编码没有正确解释；

- 伪彩色显示范围设置不合适。

可以先保存米制数组：

```Bash
python3 depth_image_capture.py --topic /boostercamera/head/depth --save-on-first-frame
```

再观察终端中的 `valid` 数量和 `range` 范围。如果 `valid` 长期为 0，应优先检查深度话题和相机状态。

### 10\.9\.9 RGB 图和深度图分辨率不一致

RGB 图和深度图分辨率不一致不一定表示错误，但会增加后续像素对应关系的复杂度。进入 Chapter 12 前，应分别查看两类话题：

```Bash
ros2 topic echo /boostercamera/head/rgb --no-arr
ros2 topic echo /boostercamera/head/depth --no-arr
```

重点比较：

- `width`；

- `height`；

- 时间戳是否持续更新；

- 深度图是否与 RGB 图对齐。

如果后续要用检测框读取深度，必须确认使用的是与 RGB 图对齐的深度图。

## 10\.10 本章小结

本章完成了感知系统的输入层搭建。学习者已经从系统角度理解了 K1 相机图像如何通过 ROS2 Topic 进入视觉程序，也能够区分 RGB 图像、深度图和 `camera_info` 的作用。

本章重点讲解了 `sensor_msgs/msg/Image` 消息结构，包括宽、高、编码、步长和原始数据。图像编码是视觉程序中的关键工程细节：`bgr8`、`rgb8`、`mono8` 可以通过 `cv_bridge` 转换，`NV12` 需要手动整理为 YUV 后再转为 BGR，深度图则需要根据 `16UC1` 或 `32FC1` 转换为米制距离。

通过四个实践案例，学习者已经能够：

- 使用命令和脚本检查图像话题；

- 将 ROS2 图像消息转换为 OpenCV BGR 图像；

- 保存彩色图、灰度图和带水印图；

- 保存原始深度图、米制深度数组和伪彩色深度图；

- 在有图形界面的环境中实时显示相机画面；

- 在无图形界面环境中通过保存图片完成调试；

- 针对无图像、编码错误、窗口打不开、深度图无效等问题进行排查。

进入 Chapter 11 后，课程将在本章 RGB 图像流基础上加载 YOLO 足球检测模型。那时，视觉程序不再只保存和显示图像，而是要从图像中输出足球中心点、检测框、置信度和检测状态，为后续空间理解和追球控制提供输入。

