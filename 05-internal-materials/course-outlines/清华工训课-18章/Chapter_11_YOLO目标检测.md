# Chapter\_11\_YOLO目标检测

# Chapter 11｜YOLO 目标检测

> Chapter 10 已经完成了 K1 相机图像流的读取、保存和显示。
> 
> 进入 Chapter 11 后，视觉系统开始从“读取图像”进入“理解图像”，即从图像中找出后续控制任务需要的目标。
> 
> 

本章以足球检测为主线，使用 YOLO（You Only Look Once，单阶段目标检测模型）识别 K1 头部相机画面中的足球，并把检测结果发布到 ROS2（Robot Operating System 2，机器人操作系统 2）话题：

```Plaintext
/vision_detection/ball
```

这个话题是后续章节的重要感知入口。Chapter 12 会把足球像素坐标转换成机器人基座坐标；Chapter 13 会使用检测结果实现头部追踪和丢球搜索；Chapter 14\-18 会进一步完成稳定追球、行为树组织和视觉踢球。

本章实践代码放在：

```Plaintext
CourseCode/chapter_11_yolo_soccer_detection/
```

本章代码目录是自包含的：检测节点、工具函数、结果打印脚本和足球检测模型都放在同一目录下，不依赖其他章节目录，也不从 `Resources/Code` 导入工具文件。

运行本章代码前，应确认机器人站立稳定、头部相机无遮挡，足球放在机器人前方合适距离。虽然本章程序不会控制机器人运动，但如果机器人同时运行了其他运动程序并出现异常姿态，应立即按下机器人背部 `STAND` 按钮，让机器人回到可控状态。

> 配图建议：放置一张“Chapter 10 相机图像流 \-\> Chapter 11 YOLO 足球检测 \-\> /vision\_detection/ball \-\> 后续定位与控制”的流程图，突出本章在感知链路中的位置。

## 11\.1 足球检测任务

足球检测任务要解决的问题是：在 K1 头部相机画面中，判断足球是否出现；如果出现，给出足球在图像中的位置、检测框和置信度。

从机器人系统角度看，足球检测不是“看一眼画面上有没有球”这么简单。后续控制程序需要的是结构化数据，而不是一张带有足球的图片。因此，本章检测节点不仅要完成模型推理，还要把结果整理成稳定的数据格式。

本章目标可以拆成四步：

1. 订阅 K1 头部 RGB 图像话题；

2. 将 ROS2 图像消息转换为 OpenCV（Open Source Computer Vision Library，开源计算机视觉库）图像；

3. 使用 YOLO 足球检测模型推理；

4. 发布足球中心点、检测框、置信度和相对图像中心的偏差。

对应的数据链路如下：

```Plaintext
/boostercamera/head/rgb
  ↓
soccer_ball_detector.py
  ↓
YOLO 模型推理
  ↓
/vision_detection/ball
```

本章默认使用的输入话题是：

```Plaintext
/boostercamera/head/rgb
```

默认输出话题是：

```Plaintext
/vision_detection/ball
```

输出话题使用 `std_msgs/msg/String` 消息类型，字符串内容是 JSON 格式。这样做的好处是字段可读、调试方便，并且后续节点可以按字段解析，不需要从一段终端日志中提取信息。

### 11\.1\.1 为什么先检测足球

视觉追球和视觉踢球都建立在同一个基础问题上：机器人必须先知道球在哪里。

如果没有足球检测，后续程序无法判断：

- 头部应该向左看还是向右看；

- 球是否已经进入画面中心附近；

- 球的检测框大致有多大；

- 当前是否因为遮挡或光照导致球丢失；

- 空间定位程序应该使用哪个像素点或检测框区域计算距离。

足球检测的结果还不是机器人动作指令。它只是感知层的第一份结构化输出。后续章节会继续把这份输出加工成空间位置、控制误差和行为状态。

### 11\.1\.2 图像中心与目标中心

检测模型输出的足球位置通常用图像坐标表示。图像坐标的原点在左上角，横向为 `x`，纵向为 `y`：

```Plaintext
(0, 0) ------------------> x
  |
  |
  |
  v
  y
```

如果一帧图像宽度为 `640`，高度为 `480`，图像中心点就是：

```Plaintext
image_center = (320, 240)
```

假设足球中心点为：

```Plaintext
ball = (352, 218)
```

则足球相对图像中心的偏差为：

```Plaintext
error_x = 352 - 320 = 32
error_y = 218 - 240 = -22
```

`error_x` 大于 0，表示足球在画面右侧；`error_y` 小于 0，表示足球在画面上方。后续头部追踪会根据这些偏差调整头部 yaw（偏航角）和 pitch（俯仰角）。

本章检测节点会同时发布像素偏差和归一化偏差：

```Plaintext
error_norm_x = error_x / image_center_x
error_norm_y = error_y / image_center_y
```

归一化偏差的范围更稳定，不会强依赖图像分辨率。比如 640x480 和 1280x720 的图像都可以使用相似的控制增益。

> 配图建议：放置一张图像坐标示意图，标出图像左上角原点、图像中心点、足球中心点、检测框，以及 `error_x/error_y` 的方向。

## 11\.2 YOLO 目标检测模型

YOLO 是一种目标检测模型。理解 YOLO 前，先要理解“目标检测”到底是什么。

在视觉任务中，常见任务可以分成几类：

|任务|输入|输出|举例|
|---|---|---|---|
|图像分类|一张图像|这张图像属于什么类别|判断整张图是“足球场景”还是“非足球场景”|
|目标检测|一张图像|图像中有哪些目标，每个目标在哪里|找出足球，并给出足球检测框|
|图像分割|一张图像|每个像素属于什么区域|把足球占据的像素区域完整描出来|
|姿态估计|一张图像|关键点位置|检测人体肩、肘、膝等关键点|

本章做的是目标检测，不是图像分类。分类只回答“这张图里大概是什么”，而目标检测要回答两个更具体的问题：

- 图像中有哪些目标；

- 每个目标位于图像的什么位置。

例如，机器人看到一张相机图像后，不能只知道“画面里有足球”。它还必须知道足球在画面的哪个位置，检测框有多大，置信度是多少。只有这样，后续程序才能继续计算足球相对机器人身体的位置。

### 11\.2\.1 YOLO 的名字是什么意思

YOLO 是 `You Only Look Once` 的缩写，直译是“只看一次”。

这个名字表达的是它的基本思路：模型不反复扫描图像，也不先找一堆候选区域再逐个判断，而是把整张图像输入神经网络，通过一次前向推理同时输出目标类别、检测框和置信度。

可以用一个直观对比理解：

```Plaintext
两阶段检测思路：
先找可能有目标的区域 -> 再判断每个区域是什么

YOLO 思路：
整张图输入模型 -> 一次输出目标类别、位置和置信度
```

这就是 YOLO 适合机器人实时视觉任务的重要原因。机器人追球时，相机画面一直变化，足球也可能滚动。如果检测速度太慢，机器人看到的是“过去的球”，后续控制就会滞后。

### 11\.2\.2 YOLO 的主要特点

YOLO 系列模型常见特点包括：

- 推理速度快，适合实时检测；

- 输出结构清晰，通常包含类别、检测框和置信度；

- 可以使用通用预训练权重快速上手；

- 也可以用自己的数据重新训练，变成专门识别某类目标的模型；

- 对光照、遮挡、相机角度和训练数据质量比较敏感。

对 K1 足球检测来说，速度和稳定性都很重要。检测太慢，追球会滞后；误检太多，机器人可能把地面纹理、鞋子或其他圆形物体当成足球；漏检太多，机器人会频繁进入找球状态。

> 配图建议：放置一张“图像输入 \-\> YOLO 模型 \-\> 检测框、类别、置信度”的示意图。图中不要画复杂神经网络结构，只突出输入和输出。

### 11\.2\.3 YOLO 默认能识别多少种目标

YOLO 本身不是“固定只能识别多少种目标”的算法。能识别多少种，取决于使用的模型权重是用什么数据训练出来的。

常见的通用 YOLO 预训练检测模型通常使用 COCO（Common Objects in Context，常见物体数据集）训练。COCO 目标检测数据集中常用的是 80 个类别，因此这类通用权重通常能识别 80 类常见物体，例如人、车、椅子、瓶子、狗、猫等。

这里要区分两件事：

```Plaintext
YOLO 算法
  是一种目标检测方法

YOLO 模型权重
  是某一次训练得到的具体模型文件，决定能识别哪些类别
```

也就是说，“80 类”不是 YOLO 算法的上限，而是常用 COCO 预训练权重的类别数。如果用 1 个类别的数据训练，它就可以只识别 1 类；如果用 5 个类别的数据训练，它就识别 5 类；如果用更多类别训练，也可以识别更多类别。

通用 COCO 模型中通常有 `sports ball` 这类目标，但它不是“专门识别足球”的模型。`sports ball` 可能覆盖篮球、网球、棒球、足球等球类。对于 K1 追球和射门任务，通用球类检测不够精确：机器人需要稳定识别课程中使用的足球，而不是把所有圆形运动球都当成同一个目标。

本课程使用的是自训练足球检测模型：

```Plaintext
models/soccer_yolo.pt
```

它的任务更明确：识别 K1 足球实践中使用的足球。这个模型不是为了识别 COCO 的 80 个通用类别，而是为了在机器人相机视角下稳定检测足球。

### 11\.2\.4 通用预训练模型与自训练模型

通用预训练模型适合做快速体验。例如，学习者可以用官方常见 YOLO 权重观察“模型如何输出检测框”。但正式机器人任务不能只看模型能不能“偶尔识别到球”，还要看它在真实任务中是否稳定。

两类模型的区别如下：

|模型类型|优点|局限|适合用途|
|---|---|---|---|
|通用预训练模型|下载即可试用，能识别多种常见物体|不一定有专门足球类别，容易受场地和球外观影响|理解目标检测、快速测试|
|自训练足球模型|目标明确，更贴合 K1 相机视角和课程足球|需要采集和标注数据，换环境后可能要补数据|正式足球检测、追球和射门|

本章代码中的默认模型是自训练模型。程序加载它后，类别名称通常是：

```Plaintext
Ball
```

如果换成其他模型，必须确认新模型的类别名称或类别 ID。否则程序可能能正常推理，但后处理阶段筛不出足球。

### 11\.2\.5 检测模型输出了什么

对本章足球检测任务来说，YOLO 模型的核心输出包括：

|输出|含义|
|---|---|
|`cls_id`|目标类别编号|
|`label`|目标类别名称，例如 `Ball`|
|`conf`|置信度，表示模型对该检测结果的确信程度|
|`bbox_xyxy`|检测框左上角和右下角坐标|
|`bbox_center`|检测框中心点|

检测框常用 `[x1, y1, x2, y2]` 表示：

```Plaintext
[left, top, right, bottom]
```

其中：

- `left/top` 是检测框左上角；

- `right/bottom` 是检测框右下角；

- 中心点是 `((left + right) / 2, (top + bottom) / 2)`。

本章使用的足球检测模型文件是：

```Plaintext
CourseCode/chapter_11_yolo_soccer_detection/models/soccer_yolo.pt
```

`.pt` 是 PyTorch 模型文件格式。程序会通过 `ultralytics` 加载该模型，并对相机图像进行推理。

### 11\.2\.6 置信度阈值

目标检测模型可能在一帧图像中输出多个候选框。每个候选框都有一个置信度。置信度越高，表示模型越确信该框中存在对应目标。

本章检测节点使用两个阈值：

```Plaintext
predict_conf_threshold = 0.01
conf_threshold = 0.50
```

`predict_conf_threshold` 是传给 YOLO 推理阶段的较低阈值，允许模型先输出更多候选框；`conf_threshold` 是最终发布阶段的阈值，只有置信度达到该值的足球框才会作为有效结果发布。

这样处理的原因是：推理阶段先保留候选，后处理阶段再根据类别、面积和置信度统一筛选，便于调试不同模型和不同光照环境下的检测表现。

### 11\.2\.7 类别名称与类别 ID

不同训练数据得到的模型，类别名称可能不完全一致。有的模型类别名是 `Ball`，有的可能是 `soccer_ball`，也可能只有一个类别并使用类别 ID `0`。

本章检测节点提供两个参数：

```Plaintext
ball_class_name = "Ball"
ball_class_id = -1
```

当 `ball_class_id >= 0` 时，程序按类别 ID 筛选；当 `ball_class_id = -1` 时，程序按类别名称筛选。

如果模型中足球类别 ID 是 `0`，可以这样运行：

```Bash
python3 soccer_ball_detector.py --ros-args -p ball_class_id:=0
```

如果模型类别名称不是 `Ball`，可以这样运行：

```Bash
python3 soccer_ball_detector.py --ros-args -p ball_class_name:=soccer_ball
```

## 11\.3 检测结果字段

检测节点发布到 `/vision_detection/ball` 的消息是 JSON 字符串。检测到足球时，消息结构类似：

```JSON
{
  "stamp": {
    "sec": 1710000000,
    "nanosec": 123000000
  },
  "frame_id": "camera_color_optical_frame",
  "image_width": 640,
  "image_height": 480,
  "image_center": [320, 240],
  "x": 352,
  "y": 218,
  "conf": 0.86,
  "label": "Ball",
  "cls_id": 0,
  "bbox_xyxy": [310, 180, 394, 256],
  "bbox_center": [352, 218],
  "bbox_width": 84,
  "bbox_height": 76,
  "bbox_area": 6384,
  "detected": true,
  "stale": false,
  "age_sec": 0.0,
  "error_x": 32,
  "error_y": -22,
  "error_norm_x": 0.1,
  "error_norm_y": -0.0917
}
```

未检测到足球时，节点仍可以发布一条结构一致的消息：

```JSON
{
  "image_width": 640,
  "image_height": 480,
  "image_center": [320, 240],
  "x": 320,
  "y": 240,
  "conf": 0.0,
  "detected": false,
  "stale": false,
  "age_sec": 0.0,
  "error_x": 0,
  "error_y": 0,
  "error_norm_x": 0.0,
  "error_norm_y": 0.0
}
```

这样设计可以让后续节点更容易处理“有球”和“无球”两种情况。节点不需要猜测“没有收到消息”到底表示程序停止、网络异常，还是模型暂时没有检测到足球。

### 11\.3\.1 常用字段说明

|字段|含义|后续用途|
|---|---|---|
|`detected`|当前帧是否检测到足球|判断是否进入追踪或搜索|
|`x/y`|足球中心点像素坐标|头部追踪、空间定位|
|`conf`|置信度|过滤不可靠检测|
|`bbox_xyxy`|检测框坐标|深度区域采样、可视化|
|`image_width/image_height`|图像尺寸|计算归一化误差|
|`image_center`|图像中心点|计算目标偏差|
|`error_x/error_y`|像素偏差|解释目标相对画面中心的位置|
|`error_norm_x/error_norm_y`|归一化偏差|后续控制输入|

### 11\.3\.2 为什么要发布 `detected=false`

在机器人系统中，“没有球”也是一种重要状态。比如：

- 机器人正在找球；

- 足球被遮挡；

- 足球滚出画面；

- 光照变化导致模型暂时失效；

- 相机画面中只有地面和背景。

如果检测节点只在检测到足球时发布消息，后续节点会面临一个问题：长时间没有消息时，无法判断是“没有球”，还是检测节点已经停止。

因此，本章默认：

```Plaintext
publish_no_ball = true
```

当没有检测到足球时，节点仍发布 `detected=false`。这样后续节点可以清楚知道检测节点仍在运行，只是当前画面没有可靠足球目标。

## 11\.4 足球检测节点

本章核心程序是：

```Plaintext
CourseCode/chapter_11_yolo_soccer_detection/soccer_ball_detector.py
```

辅助工具函数放在：

```Plaintext
CourseCode/chapter_11_yolo_soccer_detection/soccer_detection_utils.py
```

结果打印脚本是：

```Plaintext
CourseCode/chapter_11_yolo_soccer_detection/print_soccer_detection.py
```

检测节点的结构如下：

```Plaintext
SoccerBallDetector
  ├── 读取 ROS2 参数
  ├── 加载 YOLO 模型
  ├── 订阅 /boostercamera/head/rgb
  ├── 转换图像编码
  ├── 模型推理
  ├── 筛选最可信的足球框
  ├── 发布 /vision_detection/ball
  └── 可选保存带检测框的图片
```

> 配图建议：放置一张检测节点内部结构图，展示“参数读取、图像订阅、图像转换、YOLO 推理、结果筛选、话题发布”的顺序。

### 11\.4\.1 图像订阅

检测节点通过下面的方式订阅图像话题：

```Python
self.create_subscription(Image, self.image_topic, self.on_image, 10)
```

其中：

- `Image` 表示消息类型是 `sensor_msgs/msg/Image`；

- `self.image_topic` 默认是 `/boostercamera/head/rgb`；

- `self.on_image` 是收到图像后的回调函数；

- `10` 是队列深度。

每当相机发布一帧图像，`on_image()` 就会被调用一次。足球检测的主要计算都发生在这个回调函数中。

### 11\.4\.2 图像编码转换

YOLO 模型不能直接使用 ROS2 图像消息。程序需要先把消息转换成 OpenCV BGR 图像：

```Python
frame = ros_image_to_bgr(msg, self.bridge)
```

`ros_image_to_bgr()` 支持 K1 常见编码：

|编码|处理方式|
|---|---|
|`bgr8`|直接转换为 BGR|
|`rgb8`|转换为 BGR|
|`mono8`|转换为 BGR 灰度图|
|`nv12`|按 NV12 YUV 格式转换为 BGR|
|`bgra8/rgba8`|去掉透明通道后转换为 BGR|

如果编码不在支持范围内，程序会抛出明确错误：

```Plaintext
unsupported image encoding
```

这类错误通常表示当前订阅的话题不是预期的 RGB 图像话题，或者相机驱动输出格式与程序处理逻辑不匹配。

### 11\.4\.3 模型推理

检测节点加载模型后，通过下面的方式推理：

```Python
predictions = self.model.predict(
    source=frame,
    conf=self.predict_conf_threshold,
    iou=self.iou_threshold,
    imgsz=self.image_size,
    max_det=self.max_det,
    verbose=False,
)
```

关键参数含义如下：

|参数|含义|
|---|---|
|`source`|输入图像|
|`conf`|推理阶段候选框置信度阈值|
|`iou`|检测框重叠抑制阈值|
|`imgsz`|模型输入尺寸|
|`max_det`|单帧最多保留的检测框数量|
|`verbose`|是否输出 YOLO 详细日志|

`iou` 用于 NMS（Non\-Maximum Suppression，非极大值抑制）。当多个检测框重叠在同一个目标附近时，NMS 会保留更可信的框，减少重复检测。

### 11\.4\.4 选择最可信足球框

YOLO 一帧图像可能输出多个检测框。足球检测节点通过 `select_best_ball()` 选择最可信的足球框：

```Python
best = select_best_ball(
    result=result,
    names=self.names,
    ball_class_name=self.ball_class_name,
    ball_class_id=self.ball_class_id,
    conf_threshold=self.conf_threshold,
    min_box_area=self.min_box_area,
)
```

筛选逻辑包括：

1. 检查是否存在检测框；

2. 根据类别 ID 或类别名称筛选足球；

3. 根据置信度阈值过滤低可信结果；

4. 根据检测框面积过滤过小目标；

5. 在剩余候选中选择置信度最高的框。

对于追球任务来说，通常只需要当前最可信的足球目标。如果画面中出现多个球，应先保证检测链路稳定，再根据任务需求扩展“选择最近球”“选择最大框”“选择指定颜色区域附近的球”等策略。

### 11\.4\.5 发布检测结果

检测结果会被整理成字典，再序列化为 JSON 字符串：

```Python
payload = build_ball_payload(msg, frame.shape, best)
self.publisher.publish(String(data=json.dumps(payload, ensure_ascii=False)))
```

`build_ball_payload()` 会根据图像尺寸自动计算：

- 图像中心点；

- 足球中心点；

- 像素偏差；

- 归一化偏差；

- 检测框宽度、高度和面积。

这样后续节点不需要重复计算这些基础字段，只要订阅 `/vision_detection/ball` 并解析 JSON 即可。

## 11\.5 程序案例：模型加载与推理

本章代码目录结构如下：

```Plaintext
chapter_11_yolo_soccer_detection/
  soccer_ball_detector.py
  soccer_detection_utils.py
  print_soccer_detection.py
  models/
    soccer_yolo.pt
  README.md
```

### 11\.5\.1 模型路径查找

模型路径查找函数位于 `soccer_detection_utils.py`：

```Python
def resolve_model_path(model_path: str, script_file: str) -> str:
    ...
```

它会依次查找：

1. 参数传入的绝对路径；

2. 当前工作目录下的相对路径；

3. 脚本所在目录下的相对路径；

4. 本章默认模型路径 `models/soccer_yolo.pt`。

这样做是为了减少运行路径带来的错误。学习者只要进入本章代码目录运行：

```Bash
python3 soccer_ball_detector.py
```

程序就能找到：

```Plaintext
models/soccer_yolo.pt
```

如果模型文件不存在，YOLO 加载阶段会报出明确的路径错误。

### 11\.5\.2 图像转换函数

图像转换函数位于：

```Python
def ros_image_to_bgr(msg: Any, bridge: Any) -> np.ndarray:
    ...
```

它的任务不是“增强图像”，而是把不同编码统一成模型能处理的 BGR 图像。

对于普通 `bgr8/rgb8/mono8`，程序使用 `cv_bridge` 转换。对于 `nv12`，程序先把原始字节解释成 YUV 数据，再调用 OpenCV：

```Python
cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_NV12)
```

如果检测节点启动后一直提示图像编码不支持，应先查看当前话题的实际编码：

```Bash
ros2 topic echo /boostercamera/head/rgb --no-arr
```

重点查看：

```Plaintext
encoding
width
height
```

### 11\.5\.3 结果封装函数

结果封装函数是：

```Python
def build_ball_payload(msg, frame_shape, detection):
    ...
```

它把模型输出转换成后续控制节点更容易使用的结构。这个函数的重要性在于统一字段，而不是简单地把 YOLO 原始输出原样发布出去。

如果后续章节需要知道足球是否可见，只看：

```Plaintext
detected
```

如果要做头部追踪，可以使用：

```Plaintext
error_norm_x
error_norm_y
```

如果要做空间定位，可以使用：

```Plaintext
x
y
bbox_xyxy
image_width
image_height
```

如果要做调试显示，可以使用：

```Plaintext
bbox_xyxy
bbox_center
conf
label
```

## 11\.6 实践案例：检测足球并发布结果

本节在 K1 真机上运行足球检测。运行前，将足球放在机器人前方相机可见范围内。建议起始距离为 1\-3 米，并避免足球被桌腿、人体或强反光物体遮挡。

### 11\.6\.1 启动前检查

进入本章代码目录：

```Bash
cd /home/booster/Workspace/chapter_11_yolo_soccer_detection
source /opt/ros/humble/setup.bash
```

确认图像话题存在：

```Bash
ros2 topic info /boostercamera/head/rgb
```

正常输出中应看到：

```Plaintext
Type: sensor_msgs/msg/Image
Publisher count: 1
```

如果 `Publisher count` 为 0，说明当前没有节点发布该图像话题。此时应先排查相机服务或相机话题名称，不要直接启动检测程序。

确认模型文件存在：

```Bash
ls -lh models/soccer_yolo.pt
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MWMwNWNlOGE0NDg1ZGNjNzJiYmIwMDAyM2QzYWE3MTdfZmI3MDMyZWVjNDE1NjNkZDViMDAzZTI0YWZhZDJmMGJfSUQ6NzY2MjYyOTE1MjE1MTM1ODY3MV8xNzg1ODM5NDk5OjE3ODU5MjU4OTlfVjM)

确认 Python 能导入 YOLO：

```Bash
python3 -c "from ultralytics import YOLO; print('YOLO import ok')"
```

如果导入失败，需要在 K1 当前 Python 环境中安装或切换到包含 `ultralytics` 的环境。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTU0MDM4Y2Y2Y2IwN2YxODI3OTBkZDgyZTQ5ZWEwYzNfYWZlMzA1MWQzMmQ5OWYxZmFiMzU3OThjZTE5ZTlmOTRfSUQ6NzY2MjYyOTI5NDEwMzE4NjQxM18xNzg1ODM5NDk5OjE3ODU5MjU4OTlfVjM)

### 11\.6\.2 启动检测节点

终端 1 启动检测节点：

```Bash
python3 soccer_ball_detector.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDgxMjlmNjYwOTQxMDFhOTBkOTQ5ZTYzMzRlYTViZjlfYzg2ZGY2MzZmYzAwZjYwNGY1OWNhN2E0M2VlYTQyMTlfSUQ6NzY2MjYyOTU1NTI3ODcxMjA4M18xNzg1ODM5NDk5OjE3ODU5MjU4OTlfVjM)

正常启动后，终端会显示：

```Plaintext
Chapter 11 足球检测节点已启动。
订阅图像话题：/boostercamera/head/rgb
发布检测话题：/vision_detection/ball
YOLO 模型路径：...
```

首次收到图像时，程序会打印图像编码和尺寸，例如：

```Plaintext
收到图像：encoding=bgr8, width=640, height=480, frame_id=...
```

当足球出现在画面中时，终端会周期性输出：

```Plaintext
ball=(352,218) conf=0.86 error=(32,-22) norm=(0.100,-0.092) bbox=[310,180,394,256]
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YTkyZmJmODJlYjQ0ZTU2NzcxMjIzZTg4MTc1M2ZmMzRfZDU2Yjk3MTQ5MzVkNDk3MTViZjI2ZjJhZmRkM2NjM2RfSUQ6NzY2MjYzMDUyMDk3NDY5MTUyOF8xNzg1ODM5NDk5OjE3ODU5MjU4OTlfVjM)

### 11\.6\.3 观察检测话题

终端 2 启动检测结果打印脚本：

```Bash
python3 print_soccer_detection.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDg3ZTE5YTBkMTRlOTgyMDQ2NDZiZTI5NGJlZWNjNThfNzZlMjkwMmJlNzUwY2RkODc3MmE2ODM5MTQzYjg4MjJfSUQ6NzY2MjYzMDkzMTcxMTgwNjQwMF8xNzg1ODM5NDk5OjE3ODU5MjU4OTlfVjM)

这个脚本会订阅：

```Plaintext
/vision_detection/ball
```

并打印更容易阅读的检测摘要。

也可以直接查看 JSON：

```Bash
ros2 topic echo /vision_detection/ball
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZjE0ZDFjNWNiMjdkZDk5NjdhYjkxODA1YjRmODNlYmZfYjdhNzIyYTZjMjI3ZmY0NGFjOTkzZGVlMzlhY2QwYzZfSUQ6NzY2MjYzMTMyNzU0NzU1ODg4NF8xNzg1ODM5NDk5OjE3ODU5MjU4OTlfVjM)

如果终端 1 有检测输出，但终端 2 没有任何消息，应检查两个终端是否都加载了同一个 ROS2 环境，以及话题名称是否一致。

### 11\.6\.4 保存检测结果图片

为了后续报告或配图，可以保存带检测框的图片：

```Bash
python3 soccer_ball_detector.py --ros-args -p save_annotated_every_n:=30
```

程序会在 `outputs/` 目录下保存图片：

```Plaintext
outputs/soccer_detection_000030.jpg
outputs/soccer_detection_000060.jpg
```

图片上会标出：

- 足球检测框；

- 足球中心点；

- 图像中心点；

- 足球中心点与图像中心点之间的误差线。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MWE0ODQxZTM3ZGYxNmNhMTIzZjNiZjRhY2JlYWRiNTRfYWRiMDA5NzY4MWZjNDEzMDkyOGUyMTAwY2ZjMTVlZmVfSUQ6NzY2MjYzNzUxOTUyMzM1MTU0MF8xNzg1ODM5NDk5OjE3ODU5MjU4OTlfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZWRjMjc1NGM4ZWIxOGViMjliZWEyNjhlNTc1ZmJiZjFfMTNmMWVmYTg0M2E3NWNkNTI4NmQ0Mzk2YmYyYzhkZDNfSUQ6NzY2MjYzNzY0NDA2NTA0OTc4OF8xNzg1ODM5NDk5OjE3ODU5MjU4OTlfVjM)

> 配图建议：使用 `outputs/` 中保存的带框图片作为本章效果图。图注说明应包含检测框、中心点、图像中心点和误差线的含义。

### 11\.6\.5 效果说明

本章实践完成后，应能观察到三类效果。

第一，检测节点能够连续接收图像。终端中应出现图像编码、宽度和高度信息。

第二，当足球出现在画面中时，终端输出的 `detected` 状态应为 true，`conf` 应高于阈值，`bbox` 应覆盖足球主体。

第三，当移动足球位置时，`x/y` 和 `error_x/error_y` 应随之变化。例如足球移动到画面右侧时，`error_x` 应变为正值；足球移动到画面左侧时，`error_x` 应变为负值。

如果足球从画面中移开，节点应继续发布 `detected=false` 的消息。这样可以确认检测节点仍在运行，只是当前没有可靠足球目标。

## 11\.7 扩展任务：寻找、训练与替换模型

本章使用已有足球检测模型完成推理。实际部署中，模型效果会受到环境影响，例如光照、足球颜色、地面材质、相机高度和图像清晰度。

当模型在当前环境中表现不稳定时，可以考虑寻找已有模型、重新训练模型或在已有模型基础上微调。

### 11\.7\.1 模型从哪里来

YOLO 模型文件通常有三类来源。

第一类是通用预训练模型。它们通常由工具或开源社区提供，适合快速体验目标检测。例如常见 COCO 预训练模型可以识别人、车、椅子、瓶子等常见物体。它们的优点是容易获取，缺点是不一定适合 K1 足球任务。

第二类是公开的专用模型。比如有人已经训练过“足球检测”“球类检测”“机器人足球检测”模型。使用这类模型前，必须检查它的类别、训练场景、输入尺寸和授权方式。

第三类是自训练模型。也就是用本课程场地、本课程足球和 K1 相机视角采集数据，再训练得到模型。本章默认使用的 `soccer_yolo.pt` 就属于这种思路：它不是通用 80 类模型，而是面向足球检测任务的模型。

### 11\.7\.2 寻找模型时先看什么

寻找模型时，不应只看文件名里有没有 `soccer` 或 `ball`，而要检查以下信息：

|检查项|为什么重要|
|---|---|
|任务类型|必须是 detection（目标检测）模型，而不是分类、分割或姿态估计模型|
|框架格式|本章代码使用 `ultralytics` 加载 `.pt` 权重|
|类别列表|必须知道模型输出类别名或类别 ID|
|训练场景|室内、室外、草地、地胶、光照不同都会影响效果|
|目标外观|足球颜色、大小、纹理与课程使用的足球是否接近|
|输入尺寸|常见如 640，但不同模型可能有不同推荐尺寸|
|授权方式|公开模型不代表可以随意用于正式交付|

如果找到了一个公开模型，应先在单独检测节点中试运行，不要直接接入追球和踢球。

可以按下面顺序验证：

1. 将模型放入 `models/`；

2. 使用 `model_path` 指定模型路径；

3. 打印模型类别名称；

4. 调整 `ball_class_name` 或 `ball_class_id`；

5. 只观察 `/vision_detection/ball`；

6. 保存带框图片，确认检测框确实覆盖足球；

7. 移动足球、遮挡足球、移开足球，观察是否误检或漏检。

### 11\.7\.3 为什么本课程使用自训练足球模型

K1 足球任务不是普通图片识别任务。机器人相机看到的画面有自己的特点：

- 相机安装在头部，视角偏低；

- 足球常出现在地面上；

- 机器人运动时图像可能轻微抖动；

- 场地、地面和光照相对固定；

- 后续控制对检测稳定性要求高。

通用模型可能能识别“球”，但不一定能稳定服务追球和射门。比如：

- 把其他圆形物体误认为足球；

- 足球距离稍远时漏检；

- 低角度视角下检测框不稳定；

- 检测类别是 `sports ball`，不区分具体足球。

自训练模型的目标更窄，只服务本课程的足球检测任务。目标越明确，模型越容易在指定场景中稳定工作。

### 11\.7\.4 什么时候需要替换模型

出现以下现象时，可以考虑替换或重新训练模型：

- 足球经常漏检；

- 地面纹理、鞋子或其他圆形物体经常被误检为足球；

- 置信度长期偏低；

- 换场地后检测效果明显下降；

- 足球尺寸较小或距离较远时无法稳定检测。

模型替换前，应先排除图像输入问题。比如图像颜色是否正常、是否使用了正确 RGB 话题、相机是否对焦、足球是否被遮挡。模型问题和图像链路问题不要混在一起判断。

### 11\.7\.5 数据采集建议

训练足球检测模型需要采集多样化图像。数据应覆盖：

- 不同距离的足球；

- 不同方向和画面位置的足球；

- 足球部分遮挡；

- 不同光照条件；

- 不同地面背景；

- 没有足球的负样本画面。

负样本同样重要。如果数据集中只有“有球”图片，模型容易把圆形或高亮物体误认为足球。

### 11\.7\.6 标注与训练

目标检测训练需要标注检测框。每张包含足球的图片都应标出足球外接框。标注框应尽量贴近足球边缘，不要包含过多背景。

训练得到新的 `.pt` 模型后，可以替换：

```Plaintext
models/soccer_yolo.pt
```

也可以通过参数指定新模型路径：

```Bash
python3 soccer_ball_detector.py --ros-args -p model_path:=models/new_soccer_yolo.pt
```

如果新模型的类别名称不是 `Ball`，需要同步调整：

```Bash
python3 soccer_ball_detector.py --ros-args -p ball_class_name:=soccer_ball
```

或者按类别 ID 筛选：

```Bash
python3 soccer_ball_detector.py --ros-args -p ball_class_id:=0
```

### 11\.7\.7 替换模型后的检查顺序

替换模型后，不要直接进入追球或踢球任务。应先按本章方式单独检查检测效果：

1. 启动 `soccer_ball_detector.py`；

2. 观察终端输出的 `conf`、`bbox` 和 `error`；

3. 使用 `print_soccer_detection.py` 检查 `/vision_detection/ball`；

4. 保存带框图片，确认检测框覆盖足球；

5. 移动足球到画面不同位置，确认中心点和偏差变化合理；

6. 移开足球，确认节点发布 `detected=false`。

只有当检测结果稳定，后续空间定位和控制章节才有可靠输入。

## 11\.8 常见问题排查

### 11\.8\.1 程序提示找不到模型文件

现象：

```Plaintext
No such file or directory: models/soccer_yolo.pt
```

处理步骤：

1. 确认当前目录是 `chapter_11_yolo_soccer_detection`；

2. 执行 `ls -lh models/soccer_yolo.pt`；

3. 如果模型文件不在该目录，将模型复制到 `models/`；

4. 或使用 `model_path` 参数指定绝对路径。

### 11\.8\.2 程序没有收到图像

先检查话题：

```Bash
ros2 topic info /boostercamera/head/rgb
```

如果没有发布者，优先排查相机服务。如果话题存在但程序没有输出，检查运行终端是否执行了：

```Bash
source /opt/ros/humble/setup.bash
```

还可以尝试切换 raw 图像话题：

```Bash
python3 soccer_ball_detector.py --ros-args -p image_topic:=/boostercamera/head/raw/rgb
```

### 11\.8\.3 图像编码不支持

现象：

```Plaintext
unsupported image encoding
```

先查看图像编码：

```Bash
ros2 topic echo /boostercamera/head/rgb --no-arr
```

如果编码不是 `bgr8`、`rgb8`、`mono8`、`nv12`、`bgra8` 或 `rgba8`，需要在图像转换函数中增加对应编码处理，或切换到合适的 RGB 图像话题。

### 11\.8\.4 能看到足球但检测不到

可能原因包括：

- 足球距离太远，画面中尺寸太小；

- 足球被遮挡；

- 光照过暗或强反光；

- 当前模型类别名称与参数不一致；

- 置信度阈值过高；

- 模型不是当前场地或足球外观训练得到的模型。

可以先降低发布阈值观察：

```Bash
python3 soccer_ball_detector.py --ros-args -p conf_threshold:=0.30
```

如果降低阈值后出现大量误检，说明模型对当前环境区分度不足，应优先补充数据重新训练或微调模型。

### 11\.8\.5 检测框抖动明显

检测框抖动可能来自：

- 足球边缘模糊；

- 相机曝光变化；

- 模型对球体边缘不稳定；

- 机器人头部或机身轻微晃动；

- 图像帧率低或延迟大。

本章只负责发布原始检测结果，不在检测层做复杂滤波。后续头部追踪和追球控制会在控制层加入低通滤波、丢球超时和状态机逻辑。检测层应尽量保持结果真实，避免过早隐藏问题。

### 11\.8\.6 检测结果有输出，但后续节点收不到

检查话题名称是否一致：

```Bash
ros2 topic list | grep vision_detection
```

确认检测节点发布的是：

```Plaintext
/vision_detection/ball
```

后续节点订阅的话题也应是同一个名称。如果多个终端中 ROS2 环境不同，或者使用了不同的 `ROS_DOMAIN_ID`，也会导致话题互相不可见。

## 11\.9 本章小结

本章完成了从 K1 相机图像到足球检测结果的第一条感知链路。学习者应掌握：

- YOLO 目标检测模型的基本输入和输出；

- 足球检测框、中心点、置信度和类别字段的含义；

- 图像中心点与足球中心点偏差的计算方式；

- `/vision_detection/ball` 的 JSON 数据结构；

- 检测节点的图像订阅、模型推理、结果筛选和话题发布流程；

- 如何在 K1 真机上运行足球检测并观察效果；

- 如何根据终端输出、话题消息和带框图片排查检测问题。

完成本章后，机器人已经具备“看见足球并发布结构化检测结果”的能力。下一章将在此基础上进一步回答：足球不只是在图像中的某个像素点，它相对机器人身体到底位于什么方向、什么距离。

