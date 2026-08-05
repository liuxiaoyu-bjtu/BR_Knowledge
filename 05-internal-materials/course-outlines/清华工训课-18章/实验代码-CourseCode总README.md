# Booster K1 CourseCode

本目录存放手册中需要实际运行的正式代码。

目录按 Chapter 组织，而不是按课时组织。每个章节代码放在独立目录中，目录命名格式为：

```text
chapter_xx_topic/
```

其中 `xx` 为章节编号，`topic` 为英文小写下划线形式的章节主题缩写。

当前目录：

| 目录 | 对应章节 | 说明 |
|---|---|---|
| `chapter_03_robot_control/` | Chapter 03｜机器人控制基础与 SDK | 基础 SDK 控制与 Hello Robot 示例 |
| `chapter_04_ros2_control/` | Chapter 04｜ROS2 通信与控制接口 | ROS2 节点、话题、服务、图像话题与控制请求示例 |
| `chapter_05_teach_and_replay/` | Chapter 05｜示教与动作生成（上半身动作） | 上半身动作示教录制与回放示例 |
| `chapter_06_motion_data/` | Chapter 06｜动作表达与数据结构 | K1 动作 CSV/NPZ 数据结构检查示例 |
| `chapter_07_beyondmimic_training/` | Chapter 07｜BeyondMimic 训练流程 | MJ 动作训练工作区、环境检查与短训练示例 |
| `chapter_08_model_deployment/` | Chapter 08｜模型部署与执行 | MJ 动作部署资源检查与 MuJoCo 运行指引 |
| `chapter_09_end_to_end_motion_learning/` | Chapter 09｜动作学习综合项目：从动作数据到 K1 部署 | 从已重定向 K1 CSV 到 NPZ、训练、导出、MuJoCo 和真机部署的完整项目 |
| `chapter_10_camera_vision_flow/` | Chapter 10｜相机与视觉数据流 | 相机图像话题检查、RGB 图像保存、深度图保存与实时显示示例 |
| `chapter_11_yolo_soccer_detection/` | Chapter 11｜YOLO 目标检测 | 足球检测节点、检测结果发布、检测结果打印与模型文件 |
| `chapter_12_spatial_ball_localization/` | Chapter 12｜空间理解与感知到控制 | 足球空间定位、单目几何、深度增强定位、Rerun 可视化与定位结果打印 |
| `chapter_13_head_tracking_fsm/` | Chapter 13｜行为逻辑与有限状态机 | 足球头部跟随、丢球后头部搜索、可选身体原地搜索与 FSM 控制示例 |
| `chapter_14_stable_ball_chasing/` | Chapter 14｜稳定追球控制 | 足球检测、深度增强定位、足球基座坐标打印与 K1 真机稳定追球控制 |
| `chapter_15_behavior_tree_football_decision/` | Chapter 15｜行为树：把复杂行为拆成可组合动作 | 最小行为树原理演示、足球行为树叶子节点、BT 版搜索追球与停稳控制 |
| `chapter_16_visual_kick_strategy/` | Chapter 16｜VisualKick 与视觉踢球策略控制 | 视觉踢球接口、/kick_ball 数据发布、踢前对齐、kV1/kV2 和 power 力度选择 |
| `chapter_17_autonomous_chase_system/` | Chapter 17｜综合项目：自主追球 | 标准 ROS2 包、检测定位追球整合、一键启动自主追球系统 |
| `chapter_18_visual_kick_project/` | Chapter 18｜综合项目：视觉踢球 | ROS2 双包工作区、brain/Kick 消息、视觉踢球系统一键启动 |

代码文件命名使用小写下划线，例如 `hello_robot.py`。如果某章需要多个脚本，应优先保持“一个脚本解决一个明确任务”，避免把多个不相关功能塞进同一个文件。
