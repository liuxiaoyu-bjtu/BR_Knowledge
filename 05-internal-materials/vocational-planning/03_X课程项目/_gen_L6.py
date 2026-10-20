# -*- coding: utf-8 -*-
"""U2-L2 实训手册生成器（单源，与 notebooks/U2-L2_传感器速览.ipynb 对齐）。
重新运行本脚本将覆盖生成该 ipynb。
内容依据：X课程大纲-v4（U2-L2 传感器速览）。
单元边界（规则 §8.15）：相机在本课**只用 BoosterStudio「图像」组件观察话题在流，不写任何相机代码**；
相机的编程取数（get_image / subscribe_image / 深度图 / 图像编码 / 坐标系）全部归 U3-L1 独占。
编程线：get_imu() / get_odom() / get_joint_states() / get_battery() 快照式 + subscribe_imu() 订阅式对照。
【2026-09-04 回写】以 notebook 现状为准反向重建（含 09-02 用户手动精修 + 09-03 大纲对齐修订，共 33 cells）。
此前版本因格数落后（30 cells）曾标注"过期禁跑"，本次回写后恢复单源。
【2026-10-20 回写】U2 全单元标题与去 AI 表达复审（用户指令）。本课改 28 处，分两类：
  ① 标题：1.1「五类数据与消息类型」、1.2「Studio 中的数据流」、1.3「快照与订阅」、
     2.6「数据的刷新」、2.7「订阅式取数」、二级「二、四类传感器的读数」；
  ② 去 AI 表达：三张字段表去掉全角空格填充对齐（AI 生成痕迹）、
     半角引号改「」、「应用 get_imu() 可以获取」改「调用…拿到」、
     关节名与反引号之间补空格、（1）(2) 加粗体例统一、删「知识库」残句。格数仍 37。
【2026-10-20 P4对照复审回写】补全姿态/位置/关节角目标与11项记录；订正快照、订阅、时间戳与关节字段说明；删除未经核实的安装位置和控制器推断。37格（27 Markdown / 10 code），原10格代码执行逻辑不变。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U2-L2_传感器速览.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# U2-L2：传感器速览
cells.append(md("""# U2-L2：传感器速览

**课程目标**

1. 能说明相机、IMU、里程计、关节、电池五类数据分别测什么，以及常见的 ROS2 消息类型。
2. 能比较快照式与订阅式取数，按属性表读出加速度、角速度、姿态、位置、关节角与电量。
3. 能说明 `subscribe_imu()` 与 `ros2 topic echo` 都会建立订阅并接收消息；能指出 Python 回调、命令行输出和退订方式的差异。"""))

# 课程大纲映射（审核用）
cells.append(md("""## 课程大纲映射（审核用）

| 轻任务 | 对应位置 | 核心概念 | 轻量概念 |
| --- | --- | --- | --- |
| ② 传感器速览：Studio 观察相机流；读取 RPY、位置、电量与关节状态 | 一 1.2、二 2.2–2.5 | 消息类型 | — |
| 快照与订阅对照 | 一 1.3、二 2.6–2.7 | C04 订阅 | E02 回调 |

- 速览只建立“测什么、数据对象是什么、如何读取”的地图；IMU 和里程计的原理在 U2-L3 展开，电池和摔倒状态在 U2-L4 展开。
- 接口覆盖：`get_imu()`、`get_odom()`、`get_joint_states()`、`get_battery()`、`subscribe_imu()`。

> 本映射块用于大纲审核，导出学生 PDF 时移除。"""))

# 一、传感器的数据也在话题上
cells.append(md("""## 一、传感器的数据也在话题上

上一课用 `ros2 topic list` 看到系统里有一堆话题，用 `hz` 测到图像话题一秒出 20 条左右的消息。

### 1.1 五类数据与消息类型

| 传感器 | 测的是什么 | 话题上的消息类型 | SDK 里读到的对象 |
| --- | --- | --- | --- |
| 相机 | 图像画面（本课设备约 20 帧/秒，以实测为准） | `sensor_msgs/msg/Image` | `Image` |
| IMU | 自身的加速度、转动快慢 | `sensor_msgs/msg/Imu` | `IMUState` |
| 里程计 | 相对参考系的位置与朝向 | `nav_msgs/msg/Odometry` | `OdomState` |
| 关节 | 名称、角度等状态（速度和力矩字段以实际可用值为准） | `sensor_msgs/msg/JointState` | `JointStates` |
| 电池 | 剩余电量、电压、充放电状态 | `sensor_msgs/msg/BatteryState` | `BatteryState` |

命令行消息与 SDK 对象常能找到同名字段，例如 `linear_acceleration`、`angular_velocity`。SDK 还可能把消息整理成属性或提供派生字段；具体以当前 SDK 文档和返回对象为准。"""))

# 1.2 Studio 中的数据流
cells.append(md("""### 1.2 Studio 中的数据流

在 Booster Studio 的“组件”中选择“图像”，在图像话题处选择 `/boostercamera/head/rgb`；若本机话题名不同，以 `ros2 topic list` 的实际输出为准。

<font color="red">你会发现：</font>订阅之后，画面会持续更新。这说明该话题上有发布者，Studio 组件正在接收消息；换一个话题或发布者停止时，画面可能停住。

IMU、里程计、关节和电池也可能以持续发布的话题提供数据，但频率、话题名和是否有缓存要以设备配置为准。"""))

# 1.3 快照与订阅
cells.append(md("""### 1.3 快照与订阅

**快照式**：调用一次 `get_imu()`、`get_odom()` 这类接口，取回当时可用的一份数据，本次调用返回后，调用方不会因此持续收到数据。适合单次检查、状态面板刷新或代码主动采集。

**订阅式**：注册回调，数据到达时由 SDK 调用回调，直到退订或订阅失效。适合持续采集、统计频率或对每条消息处理。

`subscribe_imu()` 和 `ros2 topic echo` 都是订阅入口，但处理位置不同：前者把消息交给 Python 回调，后者在命令行打印；两者还可能使用不同的通信配置，例如控制消息可靠性与留存方式的 QoS（服务质量配置）。不能仅凭入口名称断言它们收到的消息完全相同。

快照与订阅都可能读取同一类数据，选择取决于是否需要持续处理、允许多大延迟以及接口是否提供。"""))

# 二、四类数据的读数
cells.append(md("""## 二、四类数据的读数

**实验名称**：传感器速览

**实验目标**：依次读出 IMU 的加速度与角速度、里程计的位置与姿态、关节的名称与位置、电池的剩余电量；再订阅 2 秒 IMU，记录收到的条数。

⚠️ **安全**：本课只读取数据，不发送运动或动作指令。机器人保持原有的坐姿、趴姿或准备模式（PREP）站姿；若要比较拖动前后读数，先由教师确认支撑和操作空间，学生不把机器人抬离地面。

**前置准备**：K1 已开机并建立连接（见 U1-L1）；已完成 U2-L1。

### 2.1 连接机器人"""))

# from boosteros.robots.booster import BoosterRobot
cells.append(code("""from boosteros.robots.booster import BoosterRobot

robot = BoosterRobot()
print("已连接 K1")"""))

# 2.2 IMU：加速度与角速度
cells.append(md("""### 2.2 IMU：加速度与角速度

<font color="red">需要比较读数变化时，只在教师确认支撑安全后做小幅、缓慢的姿态变化；不抬离支撑面。</font>

**（1）IMU 是什么**

IMU（Inertial Measurement Unit，惯性测量单元）是 K1 上用于测量加速度与角速度的模块，类比人类内耳中的前庭系统 —— 人闭眼能感知身体倾斜，靠的是前庭；K1 能感知自身倾斜，靠的是 IMU。

本课按 K1 文档中的 6 轴 IMU 介绍：「6 轴」指的是它能同时感知 6 个物理量，由两个核心元件组成：

| 元件 | 测量什么 | 类比 |
| --- | --- | --- |
| 加速度计（Accelerometer） | 三个轴 (x, y, z) 上的加速度（含重力） | 感受颠簸、倾斜的重力方向 |
| 陀螺仪（Gyroscope） | 绕三个轴 (x, y, z) 的旋转角速度 | 感受转弯、翻滚的旋转快慢 |


部分 IMU 还含第三种元件 —— 磁力计（含地磁方向），称为 9 轴 IMU；本课使用的 6 轴 IMU 不含磁力计；仅靠加速度计和陀螺仪不能直接得到地磁绝对航向，系统的 yaw 输出还取决于整机姿态估计。

**（2）IMU 的功能与作用**

① 姿态与平衡相关数据

人形机器人需要持续了解身体的倾斜和转动。IMU 可为姿态估计、平衡控制和摔倒判断提供输入；控制器如何使用这些输入属于设备实现。
- 姿态估计：加速度和角速度可用于估计倾斜与转动。
- 平衡与保护：控制系统可能结合 IMU 和关节等信息进行稳定控制、摔倒判断；本课不展开内部阈值和控制算法。

>类比：想象闭眼单脚站立 —— 之所以能坚持不倒，是因为内耳前庭在不断感知身体偏移，并把纠正信号送出去。K1 的 IMU 对应内耳前庭，控制系统对应大脑。

② 运动状态与位置估计

IMU 数据可以与里程计等信息结合，支持运动状态估计，用于：
- 移动中的姿态补偿
- 运动状态监控
- 位置估计中的辅助信息

③ 传感器校准与诊断

读取 IMU 可帮助观察倾斜、转动等状态；具体异常判定需要结合设备阈值和其他数据。

**（3）获取 IMU 数据**

调用 `get_imu()` 可以拿到 IMU 数据。"""))

# imu = robot.get_imu()
cells.append(code("""imu = robot.get_imu()

print("获取IMU的返回值：", imu)"""))

# `get_imu()` 的返回值是 `IMUState` 类型，包含如下信息：
cells.append(md("""`get_imu()` 的返回值是 `IMUState` 类型，包含如下信息：
| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `header` | `Header` | IMU 元数据头 |
| `linear_acceleration` | `np.ndarray` | 线加速度 [x, y, z]，单位 m/s² |
| `angular_velocity` | `np.ndarray` | 角速度 [x, y, z]，单位 rad/s |
| `orientation` | `np.ndarray` or `None` | 四元数 [x, y, z, w] |
| `timestamp` | `float` | 秒级时间戳 |
| `frame_id` | `str` | 坐标系 ID |
| `rpy` | `np.ndarray` or `None` | 欧拉角 [roll, pitch, yaw]，单位 rad；由 orientation 计算得到 |

获取 `frame_id`、`linear_acceleration`、`angular_velocity`、`timestamp` 查看。"""))

# print("坐标系：", imu.frame_id)
cells.append(code("""print("坐标系：", imu.frame_id)
print("线加速度 (m/s²)：", imu.linear_acceleration)
print("角速度 (rad/s)：", imu.angular_velocity)
print("时间戳：", round(imu.timestamp, 3))"""))

# 机器人静止时，加速度的合成大小通常接近 9.8 m/s²，但不保证某一个轴恰好等于 9.8。改变姿态后，重力分量…
cells.append(md("""机器人静止时，加速度的合成大小通常接近 9.8 m/s²，但不保证某一个轴恰好等于 9.8。改变姿态后，重力分量会在三个轴之间重新分配；转动时角速度可能明显变化。

`frame_id` 标出这组数据使用的坐标系。先确认坐标系再解释 x、y、z 的方向；不同接口的坐标约定以返回值和设备文档为准。"""))

# 2.3 里程计：位置与朝向
cells.append(md("""### 2.3 里程计：位置与朝向

**（1）什么是里程计**

里程计（Odometry）是对机器人相对运动的估计：系统根据可用的关节、足部接触、惯性等信息，估计位置和朝向。具体数据来源与算法取决于设备实现；本课不把它简化成单靠某一类传感器。

它通常以某个参考时刻为原点，累积后续运动得到相对位姿，因此可能随运动时间和距离产生漂移。重置原点只改变参考，不会让估计自动变准。

**（2）功能与作用**

里程计可用于运动状态反馈、闭环控制中的误差计算、导航系统的输入等。它提供相对位姿，不能单独替代长期稳定的全局定位；本课只观察返回数据，不展开导航算法。

**（3）获取里程计数据**

调用 `get_odom()` 可以拿到里程计数据，返回机器人在参考坐标系中的位置和朝向等状态；位置不是已走路径的总长。"""))

# odom = robot.get_odom()
cells.append(code("""odom = robot.get_odom()

print("获取的返回值：", odom)"""))

# `get_odom()` 的返回值是 `OdomState` 类型，包含如下信息：
cells.append(md("""`get_odom()` 的返回值是 `OdomState` 类型，包含如下信息：
| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `header` | `Header` | 里程计元数据头 |
| `position` | `np.ndarray` | 位置 [x, y, z]，单位 m |
| `orientation` | `np.ndarray` | 四元数 [x, y, z, w] |
| `linear_velocity` | `np.ndarray` or `None` | 线速度 [x, y, z]，单位 m/s |
| `angular_velocity` | `np.ndarray` or `None` | 角速度 [x, y, z]，单位 rad/s |
| `timestamp` | `float` | 秒级时间戳 |
| `frame_id` | `str` | 参考坐标系 |
| `child_frame_id` | `str` | 子坐标系 |
| `rpy` | `np.ndarray` | 欧拉角 [roll, pitch, yaw]，单位 rad；由 orientation 计算得到 |
| `pose_2d` | `np.ndarray` | 平面位姿 [x, y, yaw] |

获取 `position`、`rpy`、`pose_2d` 查看。
- `position` 是 x、y、z 三个方向的位移，单位是米；
- `rpy` 把姿态换算成横滚（roll）、俯仰（pitch）、航向（yaw）三个角度，单位是弧度，下面通过数学变换换成度来读。"""))

# import math
cells.append(code("""import math

roll, pitch, yaw = odom.rpy
print("位置 x, y (m)：", round(odom.position[0], 3), round(odom.position[1], 3))
print("姿态 roll, pitch, yaw (度)：",
      round(math.degrees(roll), 1),
      round(math.degrees(pitch), 1),
      round(math.degrees(yaw), 1))
print("二维位姿 [x, y, yaw]：", odom.pose_2d)"""))

# 若要比较拖动前后读数，先由教师确认机器人姿势、支撑面和空间。保持原有姿势，在支撑面上做小幅、缓慢移动；不抬离地面…
cells.append(md("""若要比较拖动前后读数，先由教师确认机器人姿势、支撑面和空间。保持原有姿势，在支撑面上做小幅、缓慢移动；不抬离地面，不让机器人失去支撑。记录前后数值，不预设一定会发生变化。"""))

# odom = robot.get_odom()
cells.append(code("""odom = robot.get_odom()
roll, pitch, yaw = odom.rpy

print("位置 x, y (m)：", round(odom.position[0], 3), round(odom.position[1], 3))
print("姿态 roll, pitch, yaw (度)：",
      round(math.degrees(roll), 1),
      round(math.degrees(pitch), 1),
      round(math.degrees(yaw), 1))
print("二维位姿 [x, y, yaw]：", odom.pose_2d)"""))

# `pose_2d` 把平面位姿打包成 `[x, y, yaw]`：x、y 的单位为米，yaw 的单位仍为弧度。它…
cells.append(md("""`pose_2d` 把平面位姿打包成 `[x, y, yaw]`：x、y 的单位为米，yaw 的单位仍为弧度。它描述相对参考系的位置和朝向，不等于已经走过的路径总长。后面的距离与坐标实验会进一步比较它们。"""))

# 2.4 关节状态
cells.append(md("""### 2.4 关节状态

`get_joint_states()` 一次取回当前可用的关节状态。返回对象包含关节列表；本课先查看数量、名称和位置。不同固件或机型的关节名称、顺序可能不同，以实际输出为准。

如果要改变姿势，只在教师确认安全时由教师操作；学生不按猜测的关节名发运动指令。"""))

# js = robot.get_joint_states()
cells.append(code("""js = robot.get_joint_states()

print("关节数量：", len(js))
print("时间戳：", round(js.timestamp, 3))
print()

for j in js.joints[:6]:
    pos = "—" if j.position is None else round(j.position, 3)
    print(f"{j.name:<16} 角度 {pos}")"""))

# 每个关节对象可能包含 `name`、`position`、`velocity`、`effort` 等字段；字段是…
cells.append(md("""每个关节对象可能包含 `name`、`position`、`velocity`、`effort` 等字段；字段是否有值、单位和含义以当前 SDK 返回对象为准。本课只读取 `name` 与 `position`，位置通常以弧度表示。需要查单个关节时，先从实际输出复制名称，再使用 `js.get_joint("关节名")`。"""))

# 2.5 电池
cells.append(md("""### 2.5 电池

`percentage` 是剩余电量百分比，`voltage` 是电压，`power_supply_status` 说明当前在充电还是放电。
"""))

# bat = robot.get_battery()
cells.append(code("""bat = robot.get_battery()
print("电量：", round(bat.percentage, 1), "%")
print("电压：", bat.voltage, "V")
print("状态：", bat.power_supply_status)"""))

# 这些读数可用于上电后的状态检查。电量是否足够要结合本次任务和设备要求判断，电压单次读数不能直接诊断电池健康。
cells.append(md("""这些读数可用于上电后的状态检查。电量是否足够要结合本次任务和设备要求判断，电压单次读数不能直接诊断电池健康。"""))

# 2.6 数据的刷新
cells.append(md("""### 2.6 数据的刷新

同一个接口连着调两次，中间隔一秒，看看拿到的还是不是同一份数据。
"""))

# import time
cells.append(code("""import time

t1 = robot.get_odom().timestamp
time.sleep(1)
t2 = robot.get_odom().timestamp

print("第一次采集：", round(t1, 3))
print("第二次采集：", round(t2, 3))
print("中间隔了：", round(t2 - t1, 3), "秒")"""))

# 两次调用的时间戳通常不同，说明接口返回的记录时间不同。快照接口取的是当前可用数据；它不等于每次调用都直接从传感器…
cells.append(md("""两次调用的时间戳通常不同，说明接口返回的记录时间不同。快照接口取的是当前可用数据；它不等于每次调用都直接从传感器硬件同步读取。"""))

# 2.7 订阅式取数
cells.append(md("""### 2.7 订阅式取数

前面几节都是「调一次、取一次」。既然数据一直在刷新，就换个办法：注册一个回调，让 IMU 数据自己送过来。
"""))

# import time
cells.append(code('''import time

counts = []


def on_imu(imu):
    """每收到一条 IMU 数据就跑一次，这里只记下它自带的时间戳。"""
    counts.append(imu.timestamp)


sub = robot.subscribe_imu(on_imu)
print("已订阅 IMU，等 2 秒……")
time.sleep(2)
sub.unsubscribe()

print("2 秒内收到", len(counts), "条")
print("平均每秒：", round(len(counts) / 2, 1), "条")'''))

# `subscribe_imu()` 会注册回调并持续接收 IMU 消息；`ros2 topic echo` 也会…
cells.append(md("""`subscribe_imu()` 会注册回调并持续接收 IMU 消息；`ros2 topic echo` 也会订阅并输出消息。二者的代码入口和处理方式不同，实际消息频率与内容还受话题、通信配置和设备状态影响。

实验结束要退订，避免回调继续运行。"""))

# 三、观察与记录
cells.append(md("""## 三、观察与记录

随操作填写。拖动或姿态变化未执行时，记录“未执行”，不补造读数。

| 观察项 | 你的记录 | 说明 |
| --- | --- | --- |
| Studio 图像 |  | 实际话题名，画面是否持续更新 |
| IMU 静止基准 |  | 三轴加速度、角速度、frame_id |
| 姿态变化后的 IMU |  | 与基准比较；未执行时注明 |
| 里程计 position |  | x、y，单位米 |
| 里程计 rpy、pose_2d |  | RPY（换成度）；pose_2d 中 yaw 仍为弧度 |
| 拖动前后里程计 |  | 数值是否变化；不预设变化方向 |
| 关节数量与前六个名称 |  | 按实际输出记录，不猜名称 |
| 一个关节的位置 |  | 名称与 position（弧度），有 None 则照实记录 |
| 电池 |  | 电量、电压、充放电状态 |
| 时间戳差 |  | 两次返回记录的时间差 |
| 订阅结果 |  | 2 秒内条数、估算每秒条数，确认已退订 |"""))

# 四、检查点、思考题与学习评价
cells.append(md("""## 四、检查点、思考题与学习评价
"""))

# 4.1 分步检查点
cells.append(md("""### 4.1 分步检查点
- [__] Studio 图像组件能显示实际话题的画面；话题名与本机输出一致。
- [__] `get_imu()`、`get_odom()`、`get_joint_states()`、`get_battery()` 都读出过返回值。
- [__] 能根据属性表读出 IMU 加速度与角速度、里程计位置与姿态、关节名称/位置和电量。
- [__] 间隔一段时间读取两次，记录时间戳差并说明它代表什么。
- [__] `subscribe_imu()` 订阅 2 秒，记录收到的条数并调用 `unsubscribe()`。
- [__] 能说明五类数据与常见 ROS2 消息类型的对应关系，同时知道 SDK 可能整理字段。"""))

# 4.2 思考题
cells.append(md("""### 4.2 思考题

课堂完成第 1、4 题；第 2、3 题课后完成。

1. `subscribe_imu()` 和 `ros2 topic echo` 都会订阅消息，但处理位置有什么不同？还可能受哪些配置影响？
2. 要写“电量低于 20% 就告警”，轮询快照和持续订阅各有什么优缺点？请结合允许的延迟、接口和资源回答。
3. 五类数据中，哪些在静止时也可能持续更新？哪些字段在短时间内可能基本不变？请用时间戳和现场记录说明。
4. 拖动或改变姿态时，里程计与 IMU 都可能变化；它们测量或估计的对象有什么不同？"""))

# 4.3 学习评价
cells.append(md("""### 4.3 学习评价

1. 快照式取数需要主动调用；订阅式注册回调后由消息到达触发处理。（判断）
2. 相机、IMU、里程计、关节、电池常见的消息类型依次为 `sensor_msgs/msg/Image`、______、`nav_msgs/msg/Odometry`、______、`sensor_msgs/msg/BatteryState`。
3. 某接口没有提供电池订阅，但任务要求每 1 秒检查一次电量；你会选轮询还是订阅？写出选择依据。若接口提供订阅且要求尽快响应，你会如何调整？

> 参考答案（教师留存，导出学生 PDF 时移除）：
> 1. √。2. `sensor_msgs/msg/Imu`；`sensor_msgs/msg/JointState`。3. 题设接口无订阅时选轮询；提供订阅且要求低延迟时可选订阅，同时考虑退订、资源与实现可靠性。"""))

# 五、扩展阅读：上电自检都看什么
cells.append(md("""## 五、扩展阅读：上电自检都看什么

展厅和工厂里的机器人，每天开机都要做一遍上电自检。运维人员按顺序确认：相机有没有出图、IMU 读数正不正常、里程计参考原点是否符合任务要求、电量是否够用、关节状态有无异常。发现异常时，先由教师或运维人员按设备文档排查，确认后再开始任务。

这五项里，相机、IMU、里程计、电量、关节各占一项，可以作为本课五类数据的自检清单 —— 相机那一项目前是用 Studio 看的，用代码读图像是后面单元的事。能按设备文档读取并判断这些数据，是应用开发和运维中的基础工作。"""))


nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
