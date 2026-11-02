---
title: BoosterOS SDK：K1信息与状态接口实测补充
module: 07-tech-platform
status: partial-verification
updated: "2026-11-02"
sdk_version: "1.2.2"
---

# BoosterOS SDK：K1 信息与状态接口实测补充

本文补充本台K1实际返回的名称、字段和状态，供代码选参、课程编写及SDK查阅使用。范围为八项信息与状态接口；未测试动作执行、模式/步态切换或任意两帧之间的坐标变换。

## 1. 来源与适用条件

| 项目 | 本次记录 |
| --- | --- |
| 采集时间 | 2026-11-02T15:44:03.105495+08:00 至 2026-11-02T15:44:14.826397+08:00 |
| 测试人 | xy |
| 机型 | 用户说明为K1；本次robot_info失败，未从本轮返回重新核实型号、序列号 |
| BoosterOS SDK | 1.2.2 |
| Python / 平台 | Python 3.10.12；Linux 5.15.148-rt-tegra，aarch64 |
| 固件 | 本次未取得；不将历史记录中的固件版本填作本轮返回 |
| 现场备注 | 未填写 |
| 连接 | 新建BoosterRobot，连接成功 |
| 完整性 | 总JSON与8份分接口JSON一致；运行脚本哈希与记录一致；ZIP内12份文件与目录内容一致 |

[原始JSON](../../04-shared/sdk-tests/K1信息状态测试结果/K1信息状态_20261102_154403_101875/原始记录.json)、[原始汇总](../../04-shared/sdk-tests/K1信息状态测试结果/K1信息状态_20261102_154403_101875/采集汇总.md)、[本机接口与类型定义](../../04-shared/sdk-tests/K1信息状态测试结果/K1信息状态_20261102_154403_101875/SDK接口定义.txt)、[运行说明](../../04-shared/sdk-tests/K1信息与状态接口_采集说明.md)。原始13个文件保持原样；本页为回读整理。后续更换机器人、SDK或配置时，重新查询对应清单。

## 2. 八项结果

| 接口 | 实际结果 | 本次结论 |
| --- | --- | --- |
| robot_info（属性） | RuntimeError: API call failed, code = 100 | 本次未取得身份/固件等元信息；保留错误 |
| get_mode() | `walk` | 公开模式名称，本次未读取底层原始模式 |
| list_gaits() | `['default', 'soccer']` | 本版本在当前模型下列出的步态，未执行切换 |
| get_gait() | `default` | SDK缓存的配置值，非实际步态测量 |
| list_frames() | 28项 | 本次可见的坐标系名称，完整列于下文 |
| list_joints() | 22项 | 关节静态元信息与本机返回顺序 |
| list_sensors() | 2项 | 本接口返回的IMU与相机元信息 |
| list_actions() | 10项 | 内置动作元信息；执行与取消未测 |

八项各调用一次；七项返回，robot_info报错。返回项没有字段导出提示。`completed=true`表示采集流程已走完，不表示八项均成功。

### robot_info 的错误

堆栈定位到 `BoosterRobot.robot_info → self.loco_client.GetRobotInfo()`，随后抛出code=100。本机定义表明该属性会构造RobotInfo，但本次没有取得该对象。当前材料没有给出code=100的含义，不能据此判断为不支持、超时、初始化未完成或设备故障。

此前[足球完整测试回读](../../05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球SDK完整测试_回读与U7课程边界.md)曾取得K1身份/固件信息，可作独立历史记录查阅；它不能替代本轮失败的返回。本次已有的七项结果可继续用于整理，不要求重跑整套。若需要补齐身份，只需在现有连接中单独重读robot_info并保存新结果及时间。

## 3. 模式与步态怎样使用

`get_mode()`本次返回walk。本机实现先取得原始模式再转换为公开名称，因此公开名称不能独立证明底层处于普通行走。此前足球测试出现过公开walk、原始kSoccer的情况；本轮没有采集原始模式，不将该历史状态写成本轮状态。

`list_gaits()`返回default和soccer。`get_gait()`本机实现只有`return self._gait`，读取SDK对象的配置缓存。因此本次default不能证明机器人没有进入足球相关控制，也不能将它当作运动状态传感器。本轮没有调用set_gait验证两项切换。

## 4. 坐标系：完整28项

下面逐行保留本次返回名称和顺序。带aa前缀的名称没有删改；代码必须使用真实字符串，不能将aahead_pitch_link替换为文档示例中的head_pitch_link。

```text
aahead_pitch_link
aahead_yaw_link
aaleft_shoulder_pitch_link
aaright_shoulder_pitch_link
camera_optical_frame
head_booster_stereo_rgb_link
head_color_optical_frame
head_point
head_realsense_rgb_link
left_ankle_pitch_link
left_ankle_roll_link
left_elbow_pitch_link
left_elbow_yaw_link
left_hip_pitch_link
left_hip_roll_link
left_hip_yaw_link
left_knee_pitch_link
left_shoulder_roll_link
right_ankle_pitch_link
right_ankle_roll_link
right_elbow_pitch_link
right_elbow_yaw_link
right_hip_pitch_link
right_hip_roll_link
right_hip_yaw_link
right_knee_pitch_link
right_shoulder_roll_link
trunk
```

按名称可辨认头部/相机、躯干和左右肢体相关条目，但名称本身不提供轴向、原点、父子关系或变换矩阵。`head_realsense_rgb_link`、`head_booster_stereo_rgb_link`同时出现，不能证明两种实体相机都已安装；硬件元信息见list_sensors。

本次没有直接出现名为球位、足球场、world或odom的坐标系。这只能描述本次可见列表；不否定get_odom接口，也不证明所有潜在坐标系都不存在。这些名称可用于选择get_transform的查询参数，但任意两项是否连通、变换方向和时间是否有效仍取决于实际变换查询。

## 5. 关节：完整22项及字段

保留下表顺序，序号为本次列表的位置。位置限位按通用SDK文档以rad表示；显示保留六位小数，完整精度见原始JSON。max_torque、max_velocity为接口原值，本机保存的JointInfo定义未标注这两列单位，本文不增加单位结论。这些是静态元信息，不是本次测得的关节角度、实际最大力矩或安全教学动作范围。所有关节extra均为{}。

| 序号 | name | limits.min（rad） | limits.max（rad） | max_torque原值 | max_velocity原值 |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | `aahead_yaw_joint` | -1.029700 | 1.029700 | 6 | 20 |
| 2 | `aahead_pitch_joint` | -0.296700 | 0.750500 | 6 | 20 |
| 3 | `aaleft_shoulder_pitch_joint` | -2.949500 | 1.204200 | 14 | 20 |
| 4 | `left_shoulder_roll_joint` | -1.727800 | 1.553300 | 14 | 20 |
| 5 | `left_elbow_pitch_joint` | -1.902400 | 1.902400 | 14 | 20 |
| 6 | `left_elbow_yaw_joint` | -2.251400 | 0.680700 | 14 | 20 |
| 7 | `aaright_shoulder_pitch_joint` | -2.949500 | 1.204200 | 14 | 20 |
| 8 | `right_shoulder_roll_joint` | -1.727800 | 1.553300 | 14 | 20 |
| 9 | `right_elbow_pitch_joint` | -1.902400 | 1.902400 | 14 | 20 |
| 10 | `right_elbow_yaw_joint` | -0.680700 | 2.251400 | 14 | 20 |
| 11 | `left_hip_pitch_joint` | -2.984400 | 2.199100 | 68 | 25 |
| 12 | `left_hip_roll_joint` | -0.384000 | 1.553300 | 43 | 25 |
| 13 | `left_hip_yaw_joint` | -1.029700 | 1.029700 | 38.3 | 25 |
| 14 | `left_knee_pitch_joint` | -0.017500 | 2.216500 | 112 | 25 |
| 15 | `left_ankle_pitch_joint` | -0.296700 | 0.663200 | 38.3 | 25 |
| 16 | `left_ankle_roll_joint` | -0.279300 | 0.715600 | 38.3 | 25 |
| 17 | `right_hip_pitch_joint` | -2.984400 | 2.199100 | 68 | 25 |
| 18 | `right_hip_roll_joint` | -1.553300 | 0.384000 | 43 | 25 |
| 19 | `right_hip_yaw_joint` | -1.012300 | 1.012300 | 38.3 | 25 |
| 20 | `right_knee_pitch_joint` | -0.017500 | 2.304000 | 112 | 25 |
| 21 | `right_ankle_pitch_joint` | -0.296700 | 0.663200 | 38.3 | 25 |
| 22 | `right_ankle_roll_joint` | -0.279300 | 0.715600 | 38.3 | 25 |

前10项为头部2项及左右臂各4项，其后为左右腿各6项。左右关节的限位不一定相同，表中保留原值；不能为形式对称改写符号或范围。需要按顺序组织关节数据时，用实际list_joints返回顺序，不能改成按名称排序。

## 6. 传感器：完整2项

| id | sensor_type | model | extra |
| --- | --- | --- | --- |
| `imu_main_1` | `imu` | `IMU_MODEL_HI13R4N` | `{}` |
| `head` | `camera` | `CAMERA_Model_BOOSTER_MIPI` | `{}` |

本机SensorInfo的sensor_type定义为camera或imu，list_sensors实现通过IMU与相机RPC获取元信息。因此这里只能作为该接口覆盖的清单，不能写成K1只有两种传感器、没有麦克风、里程计或其他硬件。

相机标识head可以用于SDK相机接口的camera_id选参；imu_main_1是本次IMU元信息标识，不能不查方法签名就把它传给无传感器ID参数的读取函数。CAMERA_Model_BOOSTER_MIPI是返回的型号字符串，不能单凭此字符串确定深度单位、配准方式或所有物理规格。

## 7. 内置动作：完整10项

| id | type | duration原值（秒） | interruptible |
| --- | --- | ---: | --- |
| `hand_shake` | `upper_body` | -1.0 | `true` |
| `hand_wave` | `upper_body` | -1.0 | `true` |
| `dance_new_year` | `upper_body` | -1.0 | `true` |
| `dance_rock_rolling` | `upper_body` | -1.0 | `true` |
| `dance_towards_future` | `upper_body` | -1.0 | `true` |
| `gesture_dabing` | `upper_body` | -1.0 | `true` |
| `gesture_ultraman` | `upper_body` | -1.0 | `true` |
| `bow` | `upper_body` | -1.0 | `true` |
| `cheer` | `upper_body` | -1.0 | `true` |
| `lucky_cat` | `upper_body` | -1.0 | `true` |

十项均标为upper_body、duration=-1、interruptible=true。本机ActionInfo注释说明：type用于展示/分类，不直接决定运行逻辑；duration=-1表示预期时长不确定；interruptible是语义标记，实际可中断性还取决于实现。不能据此给动作安排固定sleep时间，也不能将true写成本轮取消成功。

动作id可用于do_action的资源选择；本次没有执行do_action，不给上述十项补上执行成功、模式条件或终态结论。自录轨迹和动作工坊导出资源不属于本次内置动作列表；列表没有它们不代表其它调用入口不可用。

## 8. 对足球定位与课程的影响

本次补齐了相机标识、坐标系名称和关节/动作选项，可减少使用文档示例字符串造成的选参错误。例如相机元信息id为head，实际可见帧包含head_color_optical_frame与trunk。

本次八项没有返回足球的位置、球场定位、深度单位或RGB/深度配准结果。因此update_ball所需的实时机身米制x/y仍未建立，不能仅凭列表中有相机帧和trunk就宣布坐标转换完成。后续定位工作可以使用这些真实名称，但仍需核实变换含义、深度语义及控制参考原点。

现有学生Notebook、生成器、ball_position.py及足球控制附件本轮未改。本页记录信息查询事实，不代表U7/U8整课真机确认或自动踢球通过。
