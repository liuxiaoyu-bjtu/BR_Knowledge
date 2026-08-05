# Chapter\_12\_空间理解与感知到控制

# Chapter 12｜空间理解与感知到控制

> Chapter 11 已经让 K1 能够在相机画面中检测足球，并发布足球的像素坐标、检测框和置信度。
> 
> 像素坐标回答的是“足球在图像中的哪里”，但机器人要追球或踢球，还需要知道另一个问题：足球在机器人身体前方多远？在左边还是右边？角度偏了多少？这就是 Chapter 12 的核心任务：把视觉检测结果从图像中的二维位置，转换为机器人所在的空间位置。
> 
> 

本章围绕坐标系、相机模型、单目几何定位、深度增强定位和 Rerun（机器人数据可视化与回放工具）展开。为了让学习者不被公式吓住，本章会把公式拆成几个直观问题：

1. 图像上的一个像素点，如何变成相机前方的一条方向线；

2. 相机坐标系中的方向，如何搬到机器人身体坐标系中；

3. 如果只知道方向，如何通过地面求交估计足球位置；

4. 如果有深度图，如何更直接地估计足球距离；

5. 输出的 `x`、`y`、`distance`、`angle` 如何服务后续追球控制。

本章实践代码放在：

```Plaintext
CourseCode/chapter_12_spatial_ball_localization/
```

本章代码目录自包含，包含与 Chapter 11 功能相同的足球检测节点，但不会跨章节 import Chapter 11 文件。这样做是为了保证多终端运行时路径清晰，学习者只需要进入 Chapter 12 目录即可完成本章实践。

本章程序仍然只做感知和定位，不向机器人发送运动指令。运行时应保持机器人站立稳定，头部相机无遮挡，足球放在机器人前方可见范围内。如果机器人同时运行其他运动程序并出现异常姿态，应立即按下机器人背部 `STAND` 按钮。

> 配图建议：放置一张“相机图像中的足球 \-\> 像素坐标 \-\> 相机射线 \-\> 机器人基座坐标 \-\> 后续追球控制”的总流程图。图中标出本章输出话题 `/vision/ball_position_base`。

## 12\.1 目标位置理解

目标检测给出的结果是图像坐标。例如：

```JSON
{
  "x": 352,
  "y": 218,
  "bbox_xyxy": [310, 180, 394, 256],
  "conf": 0.86,
  "detected": true
}
```

这些字段说明足球在图像中被检测到了，我们有了球的位置信息，但是为了完成机器人的移动，我们还需要得到下面这些信息量：

```JSON
{
  "x": 1.236,
  "y": -0.184,
  "distance": 1.250,
  "angle": -0.148
}
```

这里的含义是：

- 足球在机器人前方约 `1.236 m`；

- 足球在机器人右侧约 `0.184 m`；

- 足球距离机器人约 `1.250 m`；

- 足球相对机器人正前方偏右约 `0.148 rad`。

这组数据就可以作为后续控制输入。比如：

- `distance` 太大，机器人需要向前走；

- `angle` 偏左或偏右，机器人需要转向；

- `x` 接近停止距离，机器人需要减速；

- `y` 偏大，机器人需要横向调整或转身对准。

### 12\.1\.1 像素位置不是空间位置

假设足球在图像中心，不能直接说明足球就在机器人正前方 1 米处。它可能在 0\.8 米处，也可能在 3 米处。二维图像把真实三维世界“压扁”到了一个平面上，距离信息会丢失。

同样，一个足球在画面偏右，也不一定表示它在机器人右侧很多。它可能只是离机器人很近，稍微偏一点就会在图像中偏得很明显；也可能离机器人很远，看起来偏移很小。

因此，从像素坐标到空间坐标必须引入额外信息：

- 相机内参：相机如何把空间投影到图像；

- 相机外参：相机装在机器人头部的什么位置和方向；

- 头部位姿：当前头部相对机器人身体转到了哪里；

- 深度图或地面假设：目标离相机大约多远。

### 12\.1\.2 本章输出的目标位置

本章输出话题是：

```Plaintext
/vision/ball_position_base
```

消息类型仍然使用：

```Plaintext
std_msgs/msg/String
```

字符串内容是 JSON。有效输出示例：

```JSON
{
  "valid": true,
  "x": 1.236,
  "y": -0.184,
  "z": 0.032,
  "distance": 1.25,
  "angle": -0.148,
  "method": "depth_sphere",
  "conf": 0.86,
  "detected": true
}
```

字段说明如下：

|字段|含义|
|---|---|
|`valid`|当前定位结果是否可用|
|`x`|足球相对机器人基座的前向距离，单位米|
|`y`|足球相对机器人基座的左右位置，单位米|
|`z`|足球在机器人基座坐标系中的高度，单位米|
|`distance`|足球在地面平面上的距离|
|`angle`|足球相对机器人正前方的夹角，单位弧度|
|`method`|当前使用的定位方法|
|`conf`|上游检测置信度|
|`detected`|上游检测是否看到了足球|

`valid=false` 时，消息示例为：

```JSON
{
  "valid": false,
  "reason": "no_head_pose",
  "stamp": 1710000000.123
}
```

无效原因同样很重要。它能帮助判断问题发生在检测、头部位姿、深度图还是坐标计算。

## 12\.2 图像坐标与机器人坐标

学习空间定位前，必须先理解“坐标系”。坐标系可以理解为一套尺子和方向约定。只说“足球在 \(1\.2, 0\.3\)”没有意义，必须说明这个 `(1.2, 0.3)` 是相对哪套尺子量出来的。

机器人视觉任务中常见坐标系包括：

- 图像坐标系；

- 相机坐标系；

- 头部坐标系；

- 机器人基座坐标系；

- 世界坐标系。

### 12\.2\.1 图像坐标系

图像坐标系是最容易看到的坐标系。它的原点在图像左上角：

```Plaintext
(0, 0) --------------------> u
  |
  |
  |
  |
  v
```

为了避免和空间坐标里的 `x/y/z` 混淆，图像坐标常用`u, v`，其中：

- `u` 表示横向像素位置，向右增加；

- `v` 表示纵向像素位置，向下增加。

例如图像宽度为 `640`，高度为 `480`，中心点就是`u = 320``, ``v = 240`，如果足球中心点 `u=352, v=218` 表示：足球中心点在图像中心右侧、上方。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Nzc3MDMyYzUzN2FmZDk5N2JlNGNmNjRiMGE5MDcwMDZfMGExMjRkNGJiYjI0MjZkMTZiY2JjN2U2ZTg5YjkzNGZfSUQ6NzY2ODI0MTIyMTUyOTU1NDE3MV8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

### 12\.2\.2 相机坐标系

相机坐标系是以相机为中心的三维坐标系。可以把它理解成相机自己拿着的一套尺子：

- `Z_C` 指向相机前方；

- `X_C` 和 `Y_C` 表示相机画面横向和纵向对应的空间方向；

- 原点在相机光心附近。

一张图像上的一个像素点，并不直接等于相机坐标系中的一个点。更准确地说，一个像素点对应相机前方的一条方向线。

原因是：同一个像素位置上可能有不同距离的物体。比如相机画面中心的一点，可能是 1 米处的足球，也可能是 3 米处的墙面。只看像素，无法知道具体距离。

### 12\.2\.3 机器人基座坐标系

机器人基座坐标系固定在机器人身体上。后续追球控制主要使用这个坐标系。

本章采用下面的直观约定：

```Plaintext
X_B：机器人正前方
Y_B：机器人左侧
Z_B：机器人上方
```

如果足球位置为：

```Plaintext
x = 1.2
y = 0.3
z = 0.0
```

可以理解为：足球在机器人前方 1\.2 米、左侧 0\.3 米、接近地面高度。

如果：

```Plaintext
y = -0.3
```

则表示足球在机器人右侧。

> 配图建议：画一张机器人俯视图，机器人身体在原点，`X_B` 向前，`Y_B` 向左，足球点分别放在左前方和右前方。

### 12\.2\.4 世界坐标系

世界坐标系是固定在环境中的坐标系。例如，一个球场可以定义自己的世界坐标系：场地中心是原点，球门方向是 `X` 轴。

世界坐标系和机器人基座坐标系的区别是：

- 世界坐标系固定在环境中；

- 机器人基座坐标系跟着机器人移动和转动。

本章不要求直接输出全局世界坐标，因为追球和踢球的第一阶段更需要“足球相对机器人在哪里”。因此，本章输出的是机器人基座坐标系下的位置。

后续如果要做完整球场定位或多机器人协同，才需要把基座坐标进一步转换到世界坐标系。

### 12\.2\.5 坐标转换链路

本章的坐标转换链路可以写成：

```Plaintext
图像坐标 (u, v)
  ↓ 相机内参
相机坐标系下的射线或三维点
  ↓ 相机到头部外参
头部坐标系
  ↓ 头部位姿
机器人基座坐标系
```

代码中对应的关键矩阵是：

```Plaintext
T_base_camera = T_head_to_base @ T_compensation @ T_cam_to_head
```

可以暂时把它理解成三次“搬家”：

1. `T_cam_to_head`：把相机坐标搬到头部坐标；

2. `T_compensation`：补偿相机安装的小误差；

3. `T_head_to_base`：把头部坐标搬到机器人身体坐标。

矩阵乘法的完整数学推导可以很复杂，但在本章中只需要记住：矩阵用于表达坐标系之间的位置和方向关系。

## 12\.3 单目几何定位

单目几何定位只使用一张 RGB 图像和相机位姿，不使用深度图。它的思想是：

```Plaintext
一个像素点
  ↓
相机前方的一条射线
  ↓
这条射线与地面 z=0 的交点
  ↓
估计足球在地面上的位置
```

这种方法非常适合讲清坐标转换的原理，但在真实机器人上会受到头部角度误差、相机安装误差和地面假设的影响。

### 12\.3\.1 从像素到相机射线

相机内参中最重要的四个数是：

```Plaintext
fx, fy, cx, cy
```

它们可以这样理解：

- `cx, cy`：图像中心点在像素坐标中的位置；

- `fx, fy`：相机焦距换算到像素单位后的数值。

如果足球像素点是：

```Plaintext
u = 352
v = 218
```

相机中心是：

```Plaintext
cx = 320
cy = 240
```

先计算它相对图像中心偏了多少：

```Plaintext
u - cx = 352 - 320 = 32
v - cy = 218 - 240 = -22
```

再除以焦距：

```Plaintext
x_norm = (u - cx) / fx
y_norm = (v - cy) / fy
```

于是得到相机前方的一条方向：

```Plaintext
ray_camera = [x_norm, y_norm, 1]
```

这里最后的 `1` 可以理解为：这条线朝相机前方走 1 份，同时横向和纵向偏移 `x_norm/y_norm` 份。

如果 `x_norm` 是正数，说明射线偏向图像右侧；如果 `y_norm` 是负数，说明射线偏向图像上方。

代码对应函数在：

```Plaintext
ball_localization_utils.py
```

函数名是：

```Python
pixel_to_ray_camera(u, v, model)
```

> 配图建议：画一张针孔相机模型图。左侧是相机光心，右侧是图像平面，像素点连回相机光心形成一条射线。

### 12\.3\.2 从相机射线到基座射线

像素反投影得到的是相机坐标系下的射线，但机器人控制需要基座坐标系下的方向。

代码中使用：

```Python
T_base_camera = T_head_to_base @ T_compensation @ T_cam_to_head
```

然后把相机射线转换到基座坐标系：

```Python
direction_base = T_base_camera[:3, :3] @ ray_camera
origin_base = T_base_camera[:3, 3]
```

这两行可以这样理解：

- `origin_base`：相机在机器人基座坐标系中的位置；

- `direction_base`：相机看到足球方向在机器人基座坐标系中的方向。

于是，足球可能位于下面这条线上：

```Plaintext
point = origin_base + scale * direction_base
```

`scale` 表示沿着这条线走多远。

### 12\.3\.3 射线与地面求交

足球在地面上，地面的高度可以近似看作：

```Plaintext
z = 0
```

射线上的点可以写成：

```Plaintext
point = origin + scale * direction
```

只看 `z` 方向：

```Plaintext
point_z = origin_z + scale * direction_z
```

希望它落在地面上，也就是：

```Plaintext
point_z = 0
```

代入：

```Plaintext
0 = origin_z + scale * direction_z
```

把 `origin_z` 移到左边：

```Plaintext
-origin_z = scale * direction_z
```

所以：

```Plaintext
scale = -origin_z / direction_z
```

这就是单目几何定位中最核心的地面求交公式。它的含义很直观：

- 相机离地面越高，`origin_z` 越大；

- 射线越向下，`direction_z` 越明显；

- 根据这两个量，就能算出射线走多远会碰到地面。

代码对应函数是：

```Python
ray_to_ground_base(...)
```

### 12\.3\.4 为什么常用检测框底部中心

足球检测框中心点通常接近球心在图像上的投影。但单目几何用的是“射线与地面求交”，所以更希望使用接近足球接地点的位置。

因此，单目几何节点默认使用检测框底部中心上移一点的像素：

```Plaintext
u = (x1 + x2) / 2
v = y2 - offset * bbox_height
```

其中 `offset` 默认是：

```Plaintext
0.10
```

这样可以避免直接使用检测框最底部，因为最底部可能包含阴影、草地或检测框边缘误差。

> 配图建议：画一个足球检测框，标出框中心点和底部中心上移点，并说明单目几何为什么更偏向使用接地点附近的像素。

### 12\.3\.5 单目几何的优点和局限

单目几何定位的优点：

- 原理清晰；

- 不依赖深度图；

- 只要相机内参、外参和头部位姿可信，就能输出位置；

- 可作为深度失效时的兜底方法。

局限也很明显：

- 头部俯仰角有一点误差，远处距离可能差很多；

- 相机外参不准会导致整体偏移；

- 地面不平整会引入误差；

- 足球不在地面上时，地面求交假设不成立；

- 足球距离很远时，射线几乎贴近地面，误差会被放大。

因此，本章还会引入深度增强定位。

## 12\.4 深度增强定位

深度图直接提供图像中每个像素对应的大致距离。它可以理解为一张“距离图片”：普通 RGB 图像记录颜色，深度图记录距离。

如果足球检测框内有可靠深度，定位就不需要只靠“射线碰地面”的假设，而可以直接根据深度估计足球在相机坐标系中的三维位置。

### 12\.4\.1 深度图是什么

K1 头部深度图默认话题是：

```Plaintext
/boostercamera/head/depth
```

常见深度编码包括：

|编码|含义|
|---|---|
|`16UC1`|16 位无符号整数，通常单位是毫米|
|`32FC1`|32 位浮点数，通常单位是米|

代码中会统一转换成“米”：

```Python
if encoding in ("16UC1", "mono16", "z16"):
    depth_m = raw_depth * 0.001
```

如果深度值是 `1200` 毫米，转换后就是：

```Plaintext
1.2 m
```

### 12\.4\.2 深度点反投影

如果某个像素点 `(u, v)` 的深度是 `Z`，它在相机坐标系中的三维位置可以写成：

```Plaintext
X = (u - cx) / fx * Z
Y = (v - cy) / fy * Z
Z = depth
```

这个公式和前面的像素射线公式很像。区别是：

- 单目几何只有方向 `[x_norm, y_norm, 1]`；

- 深度定位知道距离 `Z`，所以能得到具体三维点。

可以把它理解成：先知道像素点朝哪个方向，再知道沿这个方向大约走多远。

配图建议：画一张图，左边是图像中的足球检测框，右边是检测框内多个深度点反投影成相机前方的一小片三维点。

### 12\.4\.3 方法一：球面拟合

足球是一个球体。如果检测框内有很多深度点，这些点应该大致落在一个球面上。

深度增强节点优先使用：

```Plaintext
depth_sphere
```

它的思路是：

1. 在足球检测框内取一批有效深度点；

2. 把这些点从像素坐标反投影到相机三维坐标；

3. 用这些三维点拟合一个球；

4. 如果拟合半径接近真实足球半径，就接受球心作为足球位置。

本章默认足球半径是：

```Plaintext
0.091 m
```

球面拟合的完整数学推导比较长，但可以先这样理解：程序在许多深度点中寻找一个“最像足球”的球面。如果这个球面的半径与真实足球半径差得不多，就认为结果可信。

代码中对应函数是：

```Python
fit_sphere(points)
```

### 12\.4\.4 方法二：深度中位数

如果球面拟合失败，节点会回退到：

```Plaintext
depth_median
```

中位数是把一组数字从小到大排序后位于中间的那个数。它比平均值更不容易被极端值影响。

例如检测框内深度值大致是：

```Plaintext
1.18, 1.19, 1.20, 1.21, 4.80
```

`4.80` 可能是背景误差。如果求平均值，会被它明显拉大；如果取中位数，结果是：

```Plaintext
1.20
```

这更接近足球真实距离。

因此，当球面拟合不可靠时，深度中位数仍然能给出一个较稳定的距离估计。

### 12\.4\.5 方法三：几何兜底

如果深度图没有发布、深度时间太旧、检测框内有效深度点太少，节点会回退到：

```Plaintext
geometry
```

也就是前面讲过的单目几何地面求交。

本章深度增强节点的定位优先级是：

```Plaintext
depth_sphere
  ↓ 失败
depth_median
  ↓ 失败
geometry
```

输出中的 `method` 字段会告诉当前使用了哪种方法。

## 12\.5 足球位置数据

本章输出 `/vision/ball_position_base`，后续追球控制主要使用以下字段：

```Plaintext
x
y
distance
angle
valid
method
```

### 12\.5\.1 `x` 和 `y`

`x` 是足球在机器人前方的距离：

```Plaintext
x > 0：足球在机器人前方
x 越大：足球越远
```

`y` 是足球在机器人左右方向的位置：

```Plaintext
y > 0：足球在机器人左侧
y < 0：足球在机器人右侧
```

例如：

```Plaintext
x = 1.2
y = 0.3
```

表示足球在机器人左前方。

```Plaintext
x = 1.2
y = -0.3
```

表示足球在机器人右前方。

### 12\.5\.2 `distance`

`distance` 表示足球到机器人基座原点的平面距离：

```Plaintext
distance = sqrt(x^2 + y^2)
```

这里的 `sqrt` 表示平方根。

可以用一个直角三角形理解：`x` 是前后方向的边，`y` 是左右方向的边，`distance` 是斜边。

例如：

```Plaintext
x = 1.2
y = 0.5
```

那么：

```Plaintext
distance = sqrt(1.2^2 + 0.5^2)
         = sqrt(1.44 + 0.25)
         = sqrt(1.69)
         = 1.3
```

所以足球距离机器人约 1\.3 米。

配图建议：画一个俯视直角三角形，前向边是 `x`，横向边是 `y`，斜边是 `distance`。

### 12\.5\.3 `angle`

`angle` 表示足球相对机器人正前方的角度：

```Plaintext
angle = atan2(y, x)
```

`atan2` 可以理解为“根据前方距离和左右偏移，算出偏转角”。如果数学基础不熟，可以先记住判断规则：

```Plaintext
angle > 0：足球偏左
angle < 0：足球偏右
angle 接近 0：足球接近正前方
```

角度单位是弧度。常见近似关系：

```Plaintext
0.17 rad ≈ 10°
0.52 rad ≈ 30°
1.57 rad ≈ 90°
```

后续追球控制中，如果 `angle` 很大，机器人应先转向；如果 `angle` 很小，可以更放心地向前走。

### 12\.5\.4 `valid` 和 `reason`

空间定位不是每一帧都能成功。因此必须显式发布 `valid`。

当 `valid=true` 时，后续控制节点可以使用 `x/y/distance/angle`。

当 `valid=false` 时，后续控制节点不应继续使用旧坐标，而应根据 `reason` 判断是否停止、搜索或等待。

常见无效原因包括：

|reason|含义|
|---|---|
|`no_ball_payload`|没收到足球检测消息|
|`ball_timeout`|检测消息太久未更新|
|`not_detected`|当前画面没有检测到足球|
|`low_conf`|检测置信度过低|
|`no_head_pose`|没收到头部位姿|
|`all_estimators_failed`|深度和几何定位都失败|
|`out_of_safe_range`|结果超出允许范围|

## 12\.6 程序案例：目标位置计算

本章代码目录结构如下：

```Plaintext
chapter_12_spatial_ball_localization/
  soccer_ball_detector.py
  soccer_detection_utils.py
  ball_localization_utils.py
  ball_position_geometry_node.py
  ball_position_depth_node.py
  print_ball_position.py
  rerun_ball_localization_viewer.py
  models/
    soccer_yolo.pt
  README.md
```

### 12\.6\.1 公共工具文件

`ball_localization_utils.py` 提供空间定位基础函数。

像素到射线：

```Python
pixel_to_ray_camera(u, v, model)
```

射线与地面求交：

```Python
ray_to_ground_base(...)
```

深度图解码：

```Python
decode_depth_image(msg)
```

球面拟合：

```Python
fit_sphere(points)
```

头部位姿转矩阵：

```Python
pose_to_matrix(pose)
```

这些函数和正文公式一一对应。阅读代码时，可以先从 `pixel_to_ray_camera()` 和 `ray_to_ground_base()` 开始，因为它们是本章最核心的几何链路。

### 12\.6\.2 单目几何节点

单目几何节点是：

```Plaintext
ball_position_geometry_node.py
```

它订阅：

```Plaintext
/vision_detection/ball
/head_pose
/head_pose_stamped
```

发布：

```Plaintext
/vision/ball_position_base
```

主要流程是：

```Plaintext
读取足球检测结果
  ↓
选择检测框底部中心附近像素
  ↓
像素反投影为相机射线
  ↓
相机射线转换到基座坐标系
  ↓
与地面 z=0 求交
  ↓
发布 x/y/z/distance/angle
```

单目几何节点适合用来理解公式，也可以作为深度不可用时的定位备选。

### 12\.6\.3 深度增强节点

深度增强节点是：

```Plaintext
ball_position_depth_node.py
```

它比单目几何节点多订阅：

```Plaintext
/boostercamera/head/depth
/boostercamera/head/rgb/camera_info
```

定位优先级是：

```Plaintext
检测框内深度点球面拟合
  ↓
深度中位数
  ↓
单目几何
```

在真机实践中，推荐优先运行深度增强节点，因为它通常比纯几何定位更稳定。

### 12\.6\.4 打印定位结果

定位结果打印脚本是：

```Plaintext
print_ball_position.py
```

它订阅：

```Plaintext
/vision/ball_position_base
```

输出示例：

```Plaintext
x=1.236m y=-0.184m z=0.032m distance=1.250m angle=-0.148rad method=depth_sphere
```

如果定位无效，输出类似：

```Plaintext
invalid reason=no_head_pose
```

这比直接看原始 JSON 更适合运行过程观察。

## 12\.7 运行方式：定位结果与控制输入

本章实践在 K1 真机上完成。运行前放置足球，保证足球处于头部相机视野内，建议起始距离为 1\-3 米。

### 12\.7\.1 启动前检查

进入本章代码目录：

```Bash
cd /home/booster/Workspace/chapter_12_spatial_ball_localization
source /opt/ros/humble/setup.bash
```

检查 RGB 图像：

```Bash
ros2 topic info /boostercamera/head/rgb
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZGNmZTA2NDU2OTUxOTJjNTUxNzc3NjBlYzU4NzVkNjdfNTZmNGRmYWFjMmUyNTg4NmQwODMxNWU3OWViNTc3NDVfSUQ6NzY2MjY2ODMxODcyNTQ0MjUwMl8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

检查深度图：

```Bash
ros2 topic info /boostercamera/head/depth
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZjI2ZjE1ZTU0OTRkYTI4ZTY0Y2UzNDZhYzc5MmJkOTdfMzEzZTExZTQ5Y2M2Yzc0NzEyMDQzMmQzMTRkZmZlNTlfSUQ6NzY2MjY2ODQ0NzY4MDE4NzY3OF8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

检查相机内参：

```Bash
ros2 topic info /boostercamera/head/rgb/camera_info
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZjhjNmM5MmRiYjJhZWJkZmM5OTQwYWYyNWVlOGZlNzJfMzU3MGMxYzVkMGFkOWNmZmRmMjRkYzAxYmMzMWQwYTNfSUQ6NzY2MjY2ODU3NjY5ODM1NDk2N18xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

检查头部位姿：

```Bash
ros2 topic list | grep head_pose
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MWJhOGMxYWQ2NTI5MTllNjdmMDJlODRiODk0NjE5ZDRfZmRmMWY1YmExMTk3YmY3YTdlOTc2ZDg0MjQ5Y2YyZmZfSUQ6NzY2MjY2ODczNzU3MzA0NzI3MF8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

如果没有 `/head_pose` 或 `/head_pose_stamped`，定位节点无法知道相机当前朝向，输出会停在：

```Plaintext
invalid reason=no_head_pose
```

### 12\.7\.2 启动足球检测

终端 1：

```Bash
python3 soccer_ball_detector.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YmJjNGYyMTc4NTlmZDc1MjFjMzI2NTM5ZmEwY2Q0MGRfMzA5MmYwZTgwNzQ2YTRlNWM0NzQ1YjBmYjQzZjljZjFfSUQ6NzY2MjY2OTQ4NDQ2MTA5OTk4M18xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

检测正常时，应看到类似输出：

```Plaintext
ball=(352,218) conf=0.86 error=(32,-22) norm=(0.100,-0.092) bbox=[310,180,394,256]
```

### 12\.7\.3 启动深度增强定位

终端 2：

```Bash
python3 ball_position_depth_node.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YjliNTIyMmY4OWIzNTRkYzc2Y2UwYjdkMzY5MDQwYWJfOWI2ZjIyY2FlNjIyNjYyZTQzNjczMTYwMDEwMzQyZTlfSUQ6NzY2MjY2OTYzMTk3ODkwMDQzMl8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

如果只观察单目几何，可以运行：

```Bash
python3 ball_position_geometry_node.py
```

定位节点启动后，会订阅检测结果、深度图、相机内参和头部位姿，并发布：

```Plaintext
/vision/ball_position_base
```

### 12\.7\.4 打印定位结果

终端 3：

```Bash
python3 print_ball_position.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MmM2MTg1ZDlkMTdjOGRmMDM4NTVkNjAxNGQzODJkZDhfY2I3ZmZlYjNlZjg3NTA1MWQ4OWFmMGUyZDhmM2QyNjNfSUQ6NzY2MjY2OTgyMzc0NjY4OTk3N18xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

正常输出类似：

```Plaintext
x=1.236m y=-0.184m z=0.032m distance=1.250m angle=-0.148rad method=depth_sphere
```

移动足球后，应观察到：

- 足球向机器人靠近时，`x` 和 `distance` 变小；

- 足球远离机器人时，`x` 和 `distance` 变大；

- 足球移动到机器人左侧时，`y` 变为正值；

- 足球移动到机器人右侧时，`y` 变为负值；

- 足球接近正前方时，`angle` 接近 0。

这些变化就是后续追球控制的输入基础。

### 12\.7\.5 定位结果如何服务控制

后续追球控制可以直接使用：

```Plaintext
distance
angle
```

一个最简单的控制思路是：

```Plaintext
如果 valid=false：不追球，等待或搜索
如果 distance 太大：向前走
如果 angle 偏左：向左转
如果 angle 偏右：向右转
如果 distance 接近停止距离：减速并停止
```

Chapter 14 会正式实现稳定追球控制。本章只负责让位置数据可信。

## 12\.8 Rerun 可视化

终端输出能看到数值，但很难直观看出坐标转换哪里错了。Rerun 可以把图像、检测框和空间点同时显示出来。

本章 Rerun 脚本是：

```Plaintext
rerun_ball_localization_viewer.py
```

它订阅：

```Plaintext
/boostercamera/head/rgb
/vision_detection/ball
/vision/ball_position_base
```

可视化内容包括：

- 相机 RGB 图像；

- 足球检测框；

- 足球像素中心点；

- 基座坐标系下的足球 2D 点；

- 基座坐标系下的足球 3D 点；

- 检测和定位日志。

### 12\.8\.1 安装与启动

如果当前环境没有安装 Rerun：

```Bash
python3 -m pip install rerun-sdk
```

如果遇到如下报错说明默认安装rerun\-sdk版本与psutil版本冲突：

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=M2FiMzBmMjQ4YzBhYTM4OTQ5M2Y4NWNhOTg2M2E0N2RfYmJhYmYyYmJjYjgwODViNDQ4M2E1MDYzZGIxZGNmNGJfSUQ6NzY2Mjk0NjQ1OTY3MTU3OTg2OF8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

解决办法：

先确认`numpy, psutil`准确版本：

```Plain Text
python3 -c "import numpy, psutil; print('numpy =', numpy.**version**); print('psutil =', psutil.**version**)"
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZWE4NWU3ZTczZjA1ODhlZGE4MjBmOWUzZWE2MGIwOTVfMTM0YTlmMzc1ODg3YjE1NzhkMGJmNmZjODk4MmZkNDZfSUQ6NzY2Mjk0NjUzNDM5MjcyODUxNl8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

然后选择对应版本的rerun\-sdk：

```Plain Text
python3 -m pip install --user "rerun-sdk==0.22.1"
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=M2RmNDgwNTU5MDI5MmU5YjE2N2IxMzQ3MDFjOTQ3MDBfNzZkZDkyZThjOGI4ZWMyZTI4Y2ZlYzllODU3NGM2MmVfSUQ6NzY2Mjk0NjYyODM4Mzk4NDg2NV8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

看到Successfully installed rerun\-sdk\-0\.22\.1即为安装成功。

安装成功后修复 Rerun Viewer 的 PATH：

```Plain Text
export PATH="$$HOME/.local/bin:$$PATH"
```

检查是否存在 ：

```Plain Text
ls -l ~/.local/bin/rerun 
```

```Plain Text
rerun --version
```

永久保存PATH ：

```Plain Text
grep -qxF 'export PATH="$$HOME/.local/bin:$$PATH"' ~/.bashrc || \ echo 'export PATH="$$HOME/.local/bin:$$PATH"' >> ~/.bashrc
```

如果此时直接启动可视化：

```Bash
python3 rerun_ball_localization_viewer.py
```

会报错`neither WAYLAND_DISPLAY nor WAYLAND_SOCKET nor DISPLAY is set`，原因是通过ssh远程连接机器人，当前终端没有图形显示环境。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YzY5ZGEyMWVkODkzNDMxZDBhYWU1ZGM4MGNkYTMxMmRfNDk4NGY5ZmU3YmEwYTI4NzJkMmY5OTkwMTk0YTI1MWNfSUQ6NzY2Mjk4MDYzMzkwMzU0OTQxOV8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

解决办法是让机器人提供 Web Viewer，然后在你的电脑浏览器中查看。

第一步：将第77行附近的`rr.init("chapter_12_ball_localization", spawn=self.spawn_viewer)`更改为：

```Plain Text
rr.init("chapter_12_ball_localization", spawn=False)
rr.serve_web(
    open_browser=False,
    web_port=9091,
    ws_port=9878,
)
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDFlMzlhMDkwMjNjOGFhYTYzOWJlM2NmOGRiODY1NzRfMDJhYmZmYmViMTA2M2E4NDZlZmZmMjcwNjJiNzlkODNfSUQ6NzY2Mjk2NTY5MjUyNTkzOTkxNF8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

第二步：在你自己的 Windows 电脑上打开 PowerShell，建立端口转发：

```Plain Text
ssh -L 9091:127.0.0.1:9091 -L 9878:127.0.0.1:9878 booster@机器人IP
```

第三步：不要关闭这个 SSH 窗口，在机器人端开三个终端按顺序运行：

```Plain Text
python3 soccer_ball_detector.py
python3 ball_position_depth_node.py
python3 rerun_ball_localization_viewer.py
```

第四步：在 Windows 浏览器中打开：

http://127\.0\.0\.1:9091/?url=ws://127\.0\.0\.1:987

此时已经可以看到Rerun可视化界面：

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YTg5ZDViNGFlZTBmYjkzZGFkZjFmYTA2ODU4ZGZiNWZfNzA5MzBkZWRmODZiNThkMTc5ZmM5ODc3MmMzODNjZGZfSUQ6NzY2Mjk4MzUyNjY2NDY1Mzc5Ml8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

如果画面更新延迟过大，原因是图像数据过大，传输和浏览器处理不过来，可以压缩图像，将第193行附近原来的`rr.log("camera/rgb", rr.Image(frame_rgb))`，更改为：

```Plain Text
rr.log(
    "camera/rgb",
    rr.Image(frame_rgb).compress(jpeg_quality=75),
)
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NWUyMmMyZWUxZDcyNTc4ZmZhZTM1YTgzOGY0NWViZmVfNmE4ZGQ3N2VhMzBlYmU0NzQwYjczYTNlMzFkYzc3MjNfSUQ6NzY2Mjk4MjgyOTM2OTc4OTY4MF8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

此时画面流畅，可以观察结果。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NmJjOTk4NDU0MWYzNDlmMjYxYmY1MGNlOTMyZDNiZTNfNDc0NjMwZDQ0OGY0ZTBmNjg4MmQ2MmFiOWQ4MGYyMTlfSUQ6NzY2Mjk2OTEwOTQzMjMzOTM4OF8xNzg1ODM5ODAwOjE3ODU5MjYyMDBfVjM)

它不会控制机器人，只负责显示数据。

> 配图建议：放置一张 Rerun Viewer 截图，左侧显示相机画面和检测框，右侧显示基座坐标系下的足球点。

### 12\.8\.2 用 Rerun 判断问题

Rerun 的价值在于把问题分层。

如果相机画面中检测框就不准，问题在足球检测层。应回到 Chapter 11 的检测阈值、模型和图像输入排查。

如果检测框正确，但空间点左右方向明显反了，可能是坐标轴方向或外参矩阵有问题。

如果足球实际在正前方，但 Rerun 中 `y` 长期偏左或偏右，可能是相机安装 yaw 补偿或外参有偏差。

如果足球点飘在空中或落到地面以下，可能是深度值、相机高度、头部位姿或地面求交假设有问题。

如果 `method` 经常从 `depth_sphere` 退回 `geometry`，说明深度框内有效点不足或球面拟合不稳定，需要检查深度图是否对齐、深度范围是否合理、足球是否太远或反光。

### 12\.8\.3 Rerun 与参数调试

调试时不要同时改很多参数。可以按下面顺序：

1. 先确认检测框准确；

2. 再确认深度图有有效值；

3. 再确认头部位姿话题存在；

4. 再观察 `method` 是否优先使用 `depth_sphere`；

5. 最后再微调 `pitch_compensation_deg`、`yaw_compensation_deg` 或 `z_compensation`。

每次只调整一个参数，然后观察 Rerun 中足球点的变化。

## 12\.9 常见问题排查

### 12\.9\.1 `no_ball_payload`

定位节点没有收到足球检测结果。检查检测节点是否正在运行：

```Bash
python3 soccer_ball_detector.py
```

也可以查看话题：

```Bash
ros2 topic echo /vision_detection/ball
```

### 12\.9\.2 `not_detected`

检测节点运行正常，但当前画面没有检测到足球。检查：

- 足球是否在相机视野内；

- 足球是否被遮挡；

- 光照是否过暗或过曝；

- 检测阈值是否过高；

- 模型类别名称或类别 ID 是否正确。

### 12\.9\.3 `no_head_pose`

定位节点没有收到头部位姿。检查：

```Bash
ros2 topic list | grep head_pose
```

如果系统发布的是 `/head_pose_stamped`，本章节点会自动订阅默认话题名加 `_stamped` 的形式。

如果话题名称不同，可以通过参数修改：

```Bash
python3 ball_position_depth_node.py --ros-args -p head_pose_topic:=/your_head_pose_topic
```

### 12\.9\.4 `all_estimators_failed`

深度和几何定位都失败。常见原因：

- 深度图没有发布；

- 深度图与 RGB 图像没有对齐；

- 检测框太小，框内有效深度点不足；

- 头部位姿异常；

- 相机射线没有与地面正常相交；

- 足球离机器人太近或太远，超出有效范围。

可以先查看深度话题：

```Bash
ros2 topic info /boostercamera/head/depth
```

再查看定位节点输出中的 `method`。如果偶尔成功但经常失败，优先检查深度图质量和检测框稳定性。

### 12\.9\.5 `out_of_safe_range`

定位结果超出允许范围。默认范围是：

```Plaintext
min_x = 0.0
max_x = 10.0
max_abs_y = 5.0
```

如果足球实际就在近处，但结果超范围，说明坐标转换可能出现明显错误。重点检查：

- 相机内参；

- 相机外参；

- 头部位姿；

- 深度单位是否从毫米正确转换到米；

- 坐标轴方向是否理解反了。

### 12\.9\.6 定位结果抖动

轻微抖动是正常现象，因为检测框、深度值和头部位姿都在实时变化。

本章深度增强节点默认开启低通滤波：

```Plaintext
enable_filter = true
filter_alpha = 0.4
```

`filter_alpha` 越小，输出越平滑，但反应更慢；`filter_alpha` 越大，反应更快，但更容易抖动。

如果后续追球时机器人动作抖动明显，不应只在定位层解决，还需要在控制层设计减速区、角速度限幅和状态机。

## 12\.10 本章小结

本章完成了从足球检测结果到机器人可用空间位置的转换。学习者应掌握：

- 图像坐标系、相机坐标系、机器人基座坐标系和世界坐标系的区别；

- 为什么像素坐标不能直接用于机器人控制；

- 如何用 `(u - cx) / fx` 和 `(v - cy) / fy` 将像素点变成相机射线；

- 如何用射线与地面 `z=0` 求交估计足球位置；

- 深度图如何把像素点变成三维点；

- `depth_sphere`、`depth_median` 和 `geometry` 三种定位方法的关系；

- `/vision/ball_position_base` 中 `x/y/distance/angle` 的含义；

- 如何用 Rerun 观察检测框和空间点，判断误差来源。

完成本章后，系统已经能把“画面中看到一个足球”转换为“足球在机器人前方多远、偏左还是偏右”。这一步是从感知走向控制的关键桥梁。后续章节将在这个位置数据基础上，实现头部追踪、丢球搜索、稳定追球和视觉踢球。

