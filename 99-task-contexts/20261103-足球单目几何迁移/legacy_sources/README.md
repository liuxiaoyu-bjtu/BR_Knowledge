# Chapter 12 Spatial Ball Localization

本目录对应 `Chapter 12｜空间理解与感知 → 控制`。

本章代码在 K1 真机上运行，用足球检测结果、头部位姿和深度图估计足球在机器人基座坐标系下的位置。代码目录自包含，不依赖其他章节目录。

## 文件说明

| 文件 | 作用 |
|---|---|
| `soccer_ball_detector.py` | 订阅 K1 头部 RGB 图像，检测足球并发布 `/vision_detection/ball` |
| `soccer_detection_utils.py` | 足球检测相关工具函数 |
| `ball_localization_utils.py` | 空间定位公共函数：JSON 解析、相机模型、位姿矩阵、射线、深度解码、球面拟合 |
| `ball_position_geometry_node.py` | 单目几何定位：像素点转射线，再与地面求交 |
| `ball_position_depth_node.py` | 深度增强定位：优先球面拟合，再用深度中位数，最后回退到单目几何 |
| `print_ball_position.py` | 订阅 `/vision/ball_position_base` 并打印足球基座坐标 |
| `rerun_ball_localization_viewer.py` | 使用 Rerun 可视化图像、检测框和足球基座坐标 |
| `models/soccer_yolo.pt` | 足球检测模型文件 |

## 基础运行准备

建议将本目录复制到 K1 的工作目录：

```bash
/home/booster/Workspace/chapter_12_spatial_ball_localization/
```

进入目录并加载 ROS2 环境：

```bash
cd /home/booster/Workspace/chapter_12_spatial_ball_localization
source /opt/ros/humble/setup.bash
```

确认关键话题存在：

```bash
ros2 topic info /boostercamera/head/rgb
ros2 topic info /boostercamera/head/depth
ros2 topic info /boostercamera/head/rgb/camera_info
ros2 topic info /head_pose
```

如果当前系统发布的是 `/head_pose_stamped`，定位节点也会自动订阅：

```text
/head_pose_stamped
```

## 推荐运行方式

终端 1：启动足球检测。

```bash
python3 soccer_ball_detector.py
```

终端 2：启动深度增强定位。

```bash
python3 ball_position_depth_node.py
```

终端 3：打印足球基座坐标。

```bash
python3 print_ball_position.py
```

终端 4，可选：启动 Rerun 可视化。

```bash
python3 rerun_ball_localization_viewer.py
```

如果只想观察单目几何定位，可以将终端 2 换成：

```bash
python3 ball_position_geometry_node.py
```

## 输出字段

`/vision/ball_position_base` 使用 `std_msgs/msg/String`，内容为 JSON 字符串。有效定位示例：

```json
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

字段含义：

| 字段 | 含义 |
|---|---|
| `valid` | 当前定位结果是否可用 |
| `x` | 足球相对机器人基座的前向距离，单位米 |
| `y` | 足球相对机器人基座的左右位置，正值通常表示左侧，单位米 |
| `z` | 足球在基座坐标系下的高度，单位米 |
| `distance` | 平面距离，约等于 `sqrt(x*x + y*y)` |
| `angle` | 足球相对机器人正前方的角度，单位弧度 |
| `method` | 当前使用的定位方法：`depth_sphere`、`depth_median` 或 `geometry` |

无效定位示例：

```json
{
  "valid": false,
  "reason": "no_head_pose"
}
```

## 常用参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `ball_det_topic` | `/vision_detection/ball` | 足球检测输入话题 |
| `head_pose_topic` | `/head_pose` | 头部位姿输入话题 |
| `depth_topic` | `/boostercamera/head/depth` | 深度图输入话题 |
| `camera_info_topic` | `/boostercamera/head/rgb/camera_info` | 相机内参输入话题 |
| `base_pos_topic` | `/vision/ball_position_base` | 足球基座坐标输出话题 |
| `ball_radius_m` | `0.091` | 足球半径，单位米 |
| `min_conf` | `0.5` | 检测置信度下限 |
| `depth_min_m` | `0.15` | 有效深度下限 |
| `depth_max_m` | `6.0` | 有效深度上限 |
| `enable_filter` | `true` | 是否对输出坐标做低通滤波 |

## Rerun 可视化

Rerun 是机器人数据可视化与回放工具。本章使用它观察：

- 相机 RGB 图像；
- 足球检测框；
- 足球图像中心点；
- 足球在机器人基座坐标系下的 2D/3D 位置。

如果当前环境没有安装 Rerun：

```bash
python3 -m pip install rerun-sdk
```

启动后，Rerun Viewer 中应能看到相机画面和足球位置点。Rerun 只用于观察和排查，不向机器人发送运动指令。

## 常见问题

如果 `print_ball_position.py` 持续显示 `no_head_pose`，说明定位节点没有收到头部位姿。先检查：

```bash
ros2 topic list | grep head_pose
```

如果持续显示 `not_detected`，说明足球检测节点没有看到足球。先回到终端 1 查看检测输出。

如果持续显示 `all_estimators_failed`，通常表示深度图不可用且几何射线没有与地面正常相交。重点检查：

- `/boostercamera/head/depth` 是否有发布者；
- `/boostercamera/head/rgb/camera_info` 是否有发布者；
- `/head_pose` 是否连续发布；
- 足球是否位于相机可见范围内；
- 相机外参或补偿参数是否明显不合理。
