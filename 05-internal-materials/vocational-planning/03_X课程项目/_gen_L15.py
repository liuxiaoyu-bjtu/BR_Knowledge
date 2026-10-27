# -*- coding: utf-8 -*-
"""U4-L3 跟住来宾（闭环与视觉伺服）——Notebook 的可执行镜像。
以 notebooks/U4-L3_跟住来宾.ipynb 为源，2026-10-26 反向同步（文字校对；代码未变）；重新运行会覆盖该 Notebook。
现稿 39 cells（28 markdown / 11 code），STEP 01–11。
学生任务：在来宾站定、起点相同的条件下各运行一次开环与反馈接近，
用卷尺实测最终间距减去 1.2 m 得到落点误差，比较本次结果。
三路信息：相机框中心偏差调整方向；里程计 x 近似估计行进量；IMU z 轴角速度参与示例停止分支。
三路对应不同物理量，不能直接相加或求平均为位置；不实现融合定位或动态跟随。
B09 开环/闭环与 B10 视觉伺服在正文解释；B10 位于 §3.4「三类读数分别怎样影响程序」。
角速度相对本次循环前参考值的差超过 0.5 rad/s 时停止；该值是课堂示例，正常转向也可能触发。
不能据此诊断侧倾、打滑或行进不稳，也不能作为安全保护。U2-L3 已通过 get_odom().rpy 观察受支撑侧倾姿态变化，本课不重复。
保留只读格、构造数据分支检查、教师看护和现行准备/收尾操作；不增加外力扰动实验。
状态：P1 修订稿，真机确认②未完成。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U4-L3_跟住来宾.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# U4-L3：跟住来宾（闭环与视觉伺服）
cells.append(md("# U4-L3：跟住来宾（闭环与视觉伺服）\n\n**课程目标**\n\n1. 能以本课程序为例，区分按固定时长运行与读取反馈后调整指令的控制方式。\n2. 能指出相机、里程计和 IMU 读数各参与哪项判断，并用给定角速度数值检查示例停止分支。\n3. 能各运行一次开环接近和带反馈的接近，用卷尺测量最终间距，按“最终间距 − 1.2 米”计算停靠误差，解释正负号与本次结果。\n"))

# 一、本课要解决的问题
cells.append(md("## 一、本课要解决的问题\n\nU4-L1 根据图像偏差调整朝向，U4-L2 根据已知起步间距计算计划行进量，再检查里程计与卷尺的差异。本课把方向调整和行进量判断放入同一个循环。\n\n两次实验都由同一位来宾站在固定标记处。第一次按预先算好的转向和前进时长执行；第二次反复读取图像和里程计，更新方向指令并判断何时停止。IMU 角速度用于演示一个额外的条件分支。\n\n本课“跟住”指在接近过程中持续用画面修正朝向。程序仍依赖事先测量的起步间距，没有持续估计人与机器人间距，不能跟随正在行走的来宾。\n\n> **读取反馈后再调整指令，会怎样影响这一次接近的方向和停靠结果？**\n"))

# 二、开环与闭环
cells.append(md("## 二、开环与闭环\n\n控制程序是否使用实际结果调整后续指令，是区分开环与闭环的依据。本课比较的是学生编写的接近控制程序；机器人内部维持步态和平衡的控制不在这次比较范围内。\n"))

# 2.1 开环
cells.append(md("### 2.1 开环\n\n开环示例先计算转向和前进各需要多长时间，再依次发送速度指令并等待。执行期间不读取图像或里程计来修改这些时长。\n\n若实际速度与设定值不同，或起点、朝向、地面改变，机器人仍会执行原来的时长，因此可能停在不同位置。运行结束后读取里程计用于记录，不会使前面的固定时长控制变成闭环。\n"))

# 2.2 闭环
cells.append(md("### 2.2 闭环\n\n闭环示例每轮取图计算水平偏差，再读取里程计估计已行进量。图像偏差影响下一条转向命令，剩余行进量决定继续前进、减速或停止。\n\nU4-L2 已经使用里程计反馈停止行进，本课增加持续的视觉方向反馈。反馈能否改善结果，取决于读数是否反映目标偏差、更新是否及时以及控制参数是否合适，需用本次实验记录判断。\n"))

# **STEP 01：** 连接机器人，并加载检测模型
cells.append(md("**STEP 01：** 连接机器人，并加载检测模型"))

# import math
cells.append(code("import math\nimport time\n\nfrom boosteros.robots.booster import BoosterRobot\nfrom boosteros.brain import Detection\n\nrobot = BoosterRobot()\ndetector = Detection(model=\"person\")\n\nprint(\"已连接：\", robot.robot_info.model, robot.robot_info.serial_number)\nprint(\"当前模式：\", robot.get_mode())"))

# 2.3 开环脚本的两个时长
cells.append(md("### 2.3 计算固定转向和行进时长\n\n转向时长按“转角绝对值 ÷ 设定角速度大小”计算，转角正负决定左右方向。行进时长按“计划行进量 ÷ 设定前进速度”计算；计划行进量来自卷尺起步间距减去 1.2 米目标间距。\n\n这些计算假设机器人能按给定速度运动。STEP 02 只计算数值，实际转向和行走在 STEP 07 进行；输入的转角和间距须对应本次标记起点。\n"))

# **STEP 02：** 把这两个时长算出来（只算，不发指令）
cells.append(md("**STEP 02：** 把这两个时长算出来（只算，不发指令）"))

# start_gap = float(input("输入卷尺测得的起步间距（米）："))
cells.append(code("start_gap = float(input(\"输入卷尺测得的起步间距（米）：\"))\ntarget_gap = 1.2\ntravel_target = start_gap - target_gap\nif travel_target <= 0:\n    raise ValueError(\"起步间距必须大于目标停靠间距\")\n\nturn_angle = float(input(\"输入 U4-L1 实测的有符号转角（rad，左正右负）：\"))\nturn_speed = 0.4                # 角速度示例值（rad/s），须经教师确认后再用于真机\nturn_yaw_rate = turn_speed if turn_angle >= 0 else -turn_speed\nturn_time = abs(turn_angle) / turn_speed\n\nmove_speed = 0.3                # 前进速度示例值（m/s）\nmove_time = travel_target / move_speed\nprint(f\"开环脚本：转 {turn_time:.1f} 秒，直行 {move_time:.1f} 秒\")\nprint(f\"计划行进量 {travel_target:.2f} m；最终停靠间距需用卷尺核对\")"))

# 三、相机、里程计与 IMU 的分工
cells.append(md("## 三、相机、里程计与 IMU 的分工\n\n闭环每一轮都会读取新的状态，再决定是否继续或调整指令。基础实验中的来宾保持静止。\n"))

# 3.1 视觉与方向
cells.append(md("### 3.1 图像偏差调整方向\n\n检测框中心 x 坐标减去图像宽度的一半，得到水平偏差，单位是像素。偏差为正表示目标在画面右侧，负值表示在左侧。\n\n代码用 `-Kp_yaw × error` 计算转向角速度，并限制其大小。这里发送的是角速度，单位 rad/s；它表示转动快慢，不是下一步要转过的角度。偏差定义与 U4-L1 一致。\n"))

# 3.2 里程计与距离
cells.append(md("### 3.2 里程计估计行进量\n\n`pose_2d` 给出估计位置和朝向。机器人已大致面向来宾、清零后基本直行时，可用 x 的变化近似表示前向位移。\n\n计划行进量来自“卷尺起步间距 − 目标间距”；用它减去 x，得到还需行进多少。持续转弯或明显横向偏离时，x 不能代表沿路径走过的路程，原来的间距推算也会变差。最终间距仍用卷尺核对。\n"))

# 3.3 IMU 读数
cells.append(md("### 3.3 IMU 角速度与示例分支\n\nIMU 返回三轴角速度和线加速度。角速度表示绕各轴转动的快慢，单位 rad/s；线加速度单位 m/s²。本课取 `angular_velocity[2]`，即绕身体 z 轴转动的角速度。机器人直立时，z 轴近似朝向竖直方向。\n\nSTEP 03 在静止时记录一个角速度样本，供 STEP 04 和 STEP 09 解释差值计算。STEP 08 真正运行前重新读取一个参考值，循环中用当前角速度与这个值比较。参考值只是一时的读数，会有波动。\n\n正常转向也会改变 z 轴角速度。差值超过 0.5 rad/s，只表示满足了本课设置的分支条件，不能据此判断侧倾、打滑或安全状态。U2-L3 已观察过受支撑状态下的侧倾姿态，本课不再重复该操作。\n"))

# **STEP 03：** 读一次 IMU，看看静止时读数如何
cells.append(md("**STEP 03：** 读一次 IMU，看看静止时读数如何\n\n<font color=\"red\">提示：这一格只读数据，机器人不需要进入行走模式。让机器人保持静止，记录一组角速度读数作为示例基准。单次读数会波动，不能据此判断机器人是否安全。</font>"))

# imu = robot.get_imu()
cells.append(code("imu = robot.get_imu()\nbase_wz_rest = imu.angular_velocity[2]\nprint(\"IMU 返回值：\", imu)\n\nprint(\"角速度：\", imu.angular_velocity)\nprint(\"加速度：\", imu.linear_acceleration)\nprint(f\"本次静止角速度样本：{base_wz_rest:+.3f} rad/s\")"))

# 3.4 三类信息参与的判断
cells.append(md("### 3.4 三类读数分别怎样影响程序\n\n每轮取到的读数对应以下判断：\n\n| 读数 | 代码怎样使用 | 对下一步的影响 |\n| --- | --- | --- |\n| 检测框水平偏差 | 计算并限制转向角速度 | 调整朝向；未检出目标则结束本次实验 |\n| 清零后的里程计 x | 从计划行进量中减去 x | 剩余量较小时减速，到预计位置后不再前进 |\n| IMU z 轴角速度 | 与本次开始前参考值作差 | 差值超过示例阈值时结束本次演示 |\n\n利用图像中的目标位置等特征作反馈，反复调整运动，称为**视觉伺服**。本课用它修正朝向，再用里程计判断行进进度。三类信息分工参与控制，没有合成为一个新的位置估计。\n\n这里每轮调用 `get_image()`、`get_odom()` 和 `get_imu()`，读取SDK最近缓存的数据。依次调用不保证三份数据来自同一时刻；本课重点是读数如何影响动作，后续U7-L1会专门观察持续接收数据时的条数和时间差。\n"))

# **STEP 04：** 读取三路数据，检查示例分支（只读，不发指令）
cells.append(md("**STEP 04：** 读取三路数据，检查示例分支（只读，不发指令）"))

# 三路各读一次
cells.append(code("# 三路各读一次\nimg = robot.get_image(img_type=\"rgb\")\nresults = detector.detect(img.to_numpy())\nerror = results[0].bbox.center_x - img.width / 2 if results else None\n\nx, y, yaw = robot.get_odom().pose_2d\n\nwz = robot.get_imu().angular_velocity[2]\nprint(f\"方向偏差 {error:+.0f} 像素\" if error is not None else \"画面里没有目标\")\nprint(f\"里程计坐标分量：x={x:.3f} m，y={y:.3f} m；本格未清零，不能据此计算还差多少\")\nprint(f\"角速度 {wz:+.3f} rad/s\")\n\nif error is None:\n    print(\"→ 当前画面没有检测到来宾；运动程序应停止\")\nelif abs(wz - base_wz_rest) > 0.5:\n    print(\"→ 与静止样本的差值超过课堂示例阈值；这不是安全诊断\")\nelse:\n    print(\"→ 本格只读取并解释数据，不发送运动指令\")"))

# 四、实验：开环与闭环各跑一次
cells.append(md("## 四、实验：开环与闭环各跑一次\n\n⚠️ **安全**：本课包含转向和行走，请全程由教师看护。开始前确认路线通畅、场地平整，行走时人员不要站在机器人正前方。准备指令与执行指令分开执行，中间留人工确认的时间。发现碰撞风险、明显侧倾或不受控运动时，由教师立即人工中止，不要等待示例阈值触发。结束时先退回 `prepare`，再由人工扶坐，最后 `damping`。\n\n📌 **前置**：U4-L1 的转向来宾、U4-L2 的走近来宾；U2-L3 的 IMU 读数。\n"))

# 4.1 连接与模式确认
cells.append(md("### 4.1 场地与模式准备\n\n在地面标出机器人起点和来宾站位，测量两者间距。来宾保持站定，转向和行走范围内留出空地，看护人员站在路线侧方。\n\n开环与闭环都从同一标记起点开始。每次重新摆位后，确认输入的间距和转角仍对应当前站位。\n\n**STEP 05：** 让机器人进入准备姿态\n"))

# robot.set_mode("prepare")
cells.append(code("robot.set_mode(\"prepare\")\nprint(\"当前模式：\", robot.get_mode())"))

# <font color="red">确认机器人已经手动拉起、完全站立稳定，身体周围空旷，有教师在旁看护，再运行下…
cells.append(md("<font color=\"red\">确认机器人已经手动拉起、完全站立稳定，身体周围空旷，有教师在旁看护，再运行下一格。</font>"))

# **STEP 06：** 进入行走模式
cells.append(md("**STEP 06：** 进入行走模式"))

# robot.set_mode("walk")
cells.append(code("robot.set_mode(\"walk\")\nprint(\"当前模式：\", robot.get_mode())"))

# 4.2 开环基线
cells.append(md("### 4.2 开环接近\n\nSTEP 07 直接使用 STEP 02 算好的时长。运行前检查机器人仍在原起点，来宾仍在原标记处；如果已经移动，重新测量并计算。\n\n**STEP 07：** 按固定时长转向并前进\n\n<font color=\"red\">提示：本格会先转向再前进。确认旋转范围和两者之间的路线通畅，来宾保持站定，由教师在侧方看护。结束后测量机器人与来宾的实际间距；停止指令发出后，仍需观察是否已停稳。</font>\n"))

# 开环：按事先算好的时长走，中途不读任何结果
cells.append(code("# 开环：按事先算好的时长走，中途不读任何结果\nrobot.set_velocity(0, 0, turn_yaw_rate)\ntime.sleep(turn_time)\nrobot.set_velocity(0, 0, 0)\nprint(f\"转完 {turn_time:.1f} 秒\")\n\n# 转向结束后清零；机器人应基本沿参考坐标 x 轴直行\nrobot.reset_odom()\nrobot.set_velocity(move_speed, 0, 0)\ntime.sleep(move_time)\nrobot.set_velocity(0, 0, 0)\nprint(f\"走完 {move_time:.1f} 秒\")\n\nx, y, yaw = robot.get_odom().pose_2d\nprint(f\"开环结束：里程计 {x:.3f} m，朝向 {yaw:.3f} rad\")"))

# 4.3 闭环接近
cells.append(md("### 4.3 带反馈的接近\n\n恢复到与开环相同的起点和朝向，重新测量起步间距。代码清零时，机器人应已大致面向来宾，后续只作小幅方向修正；如果仍需大角度转向，先完成对准，再测量间距。\n\n循环中，视觉偏差决定转向角速度，里程计估计行进进度。预计行进量达到后，程序不再前进；若图像偏差仍大，则继续原地调整方向。两项条件同时满足，才退出该循环。\n\n**STEP 08：** 根据三类读数调整或停止\n\n<font color=\"red\">提示：本格会短时前进并调整方向。来宾保持站定，路线内不安排其他人员，教师全程看护。目标丢失、角速度差超过示例阈值或达到循环上限时会结束演示。发生异常由教师人工中止，不能等待角速度分支。结束后测量实际间距。</font>\n"))

# target_gap = 1.2
cells.append(code("target_gap = 1.2\nstart_gap = float(input(\"输入卷尺测得的起步间距（米）：\"))\ntravel_target = start_gap - target_gap\nif travel_target <= 0:\n    raise ValueError(\"起步间距必须大于目标停靠间距\")\n\nrobot.reset_odom()               # 机器人应已大致朝向来宾；后续以 x 近似直线行进量\nKp_yaw = 0.001                   # 示例比例系数（rad/s/像素），须经教师监督真机核验\nmax_yaw_rate = 0.2               # 示例角速度上限（rad/s），须经教师监督真机核验\nbase_wz_run = robot.get_imu().angular_velocity[2]\nthreshold = 0.5                  # 仅用于课堂分支示例，不是安全阈值\nreached = False\nx = 0.0\n\nfor i in range(200):\n    img = robot.get_image(img_type=\"rgb\")\n    found = detector.detect(img.to_numpy())\n    if not found:\n        print(\"画面里没有检测到来宾，停止本次实验\")\n        break\n\n    error = found[0].bbox.center_x - img.width / 2\n    x, y, yaw = robot.get_odom().pose_2d\n    remain = travel_target - x\n    wz = robot.get_imu().angular_velocity[2]\n\n    if abs(wz - base_wz_run) > threshold:\n        print(\"角速度读数与本次闭环开始前的参考值相差超过示例阈值；停止本次演示，不代表安全诊断\")\n        break\n\n    if remain <= 0.05 and abs(error) < 20:\n        reached = True\n        print(f\"第 {i + 1} 轮达到停止条件：估计行进 {x:.3f} m，图像偏差 {error:+.0f} px\")\n        break\n\n    yaw_rate = max(-max_yaw_rate, min(max_yaw_rate, -Kp_yaw * error))\n    vx = 0.0 if remain <= 0.05 else (0.15 if remain < 0.3 else 0.3)  # 到预计距离后只允许原地修正方向\n    time.sleep(0.5)\n    robot.set_velocity(vx, 0, yaw_rate)  # vyaw 是角速度（rad/s）\n    time.sleep(0.5)\n    robot.set_velocity(0, 0, 0)\n    print(f\"第 {i + 1} 轮：估计还差 {remain:+.3f} m，图像偏差 {error:+.0f} px\")\n\nrobot.set_velocity(0, 0, 0)\nif not reached:\n    print(\"本次未满足停止条件，已停止；请检查输出并用卷尺记录实际间距\")\nprint(f\"停止时里程计 x 分量 {x:.3f} m；它只是行进量估计，不是来宾间距\")"))

# 4.4 两组数据对照
cells.append(md("### 4.4 记录本次对照结果\n\n完成 STEP 07、08 后，分别记录两次的最终卷尺间距和结束原因。两次应使用相同的起点、朝向、来宾位置和地面条件。\n\n| 实验 | 最终间距（米） | 落点误差（米） | 结束原因 |\n| --- | --- | --- | --- |\n| 固定时长开环 | | | |\n| 带反馈接近 | | | |\n\n落点误差 = 最终间距 − 1.2 米。正值表示停得偏远，负值表示偏近。若目标丢失或循环达到上限，按实际原因记录，不能记作正常到位。\n\n一次对照只能说明这两次结果。换起点、地面或参数时另起记录；要比较重复性，先固定条件多做几次。\n"))

# 4.5 条件分支示例
cells.append(md("### 4.5 条件分支示例\n\n本格使用构造数据演示阈值判断，不推动机器人，也不把该判断当作安全检测。\n\n**STEP 09：** 用示例数值检查程序会走哪个分支"))

# threshold = 0.5                 # 课堂分支示例阈值（rad/s），不是安全阈值
cells.append(code("threshold = 0.5                 # 课堂分支示例阈值（rad/s），不是安全阈值\nsample_wz = base_wz_rest + 0.6   # 构造的示例读数；不是传感器实测值\ndeviation = abs(sample_wz - base_wz_rest)\n\nprint(f\"静止样本 {base_wz_rest:+.3f} rad/s，示例读数 {sample_wz:+.3f} rad/s\")\nif deviation > threshold:\n    print(\"示例分支：读数偏离超过阈值。该分支用于演示程序判断，不是姿态或安全检测。\")\nelse:\n    print(\"示例分支：读数未超过阈值。\")"))

# 4.6 收尾
cells.append(md("### 4.6 收尾\n\n走完先把速度清零，再让机器人退出行走模式、站稳定住。\n\n**STEP 10：** 停止并回到准备姿态"))

# robot.set_velocity(0, 0, 0)
cells.append(code("robot.set_velocity(0, 0, 0)\nrobot.set_mode(\"prepare\")\nprint(\"当前模式：\", robot.get_mode())"))

# <font color="red">由人工扶着让机器人坐下，确认坐稳之后再运行下一格。</font>
cells.append(md("<font color=\"red\">由人工扶着让机器人坐下，确认坐稳之后再运行下一格。</font>"))

# **STEP 11：** 进入软态
cells.append(md("**STEP 11：** 进入软态"))

# robot.set_mode("damping")
cells.append(code("robot.set_mode(\"damping\")\nprint(\"当前模式：\", robot.get_mode())"))

# 五、观察与记录
cells.append(md("## 五、观察与记录\n\n### 5.1 接近结果\n\n将 §4.4 的两次实测结果和结束原因记录在同一份实验记录中。比较时同时看最终间距和图像方向偏差，避免只凭停靠距离评价方向控制。\n\n### 5.2 IMU 示例记录\n\n| 项目 | 记录 |\n| --- | --- |\n| STEP 03 静止角速度样本（rad/s） | |\n| 示例阈值（rad/s） | |\n| STEP 09 构造读数（rad/s） | |\n| 条件分支结果 | |\n\n### 5.3 检查点\n\n- 能否从代码中指出，哪些指令按固定时长执行，哪些指令会被新读数改变。\n- 能否分别解释视觉偏差、里程计 x 和 IMU z 轴角速度的用途。\n- 能否根据结束原因与卷尺记录解释本次结果，避免把示例角速度阈值当作安全判断。\n\n### 5.4 思考题\n\n- 检测和读取数据变慢时，下一条指令依据的画面会落后多少？机器人在等待期间可能已经发生什么变化？\n- 预计行进量已达到，但检测框仍未回到画面中心时，代码会继续前进、原地转向，还是立刻结束？请指出对应条件。\n- 若来宾在途中后退，图像方向反馈还能修正什么？按起步间距计算的计划行进量又会受到什么影响？\n"))

# 六、扩展阅读：闭环控制的耗时与适用条件
cells.append(md("## 六、扩展阅读：反馈更新的间隔\n\n带反馈的程序要取图、运行检测、读取状态并计算指令，循环中的等待也会延长两次更新之间的间隔。本课 STEP 08 每轮有两个 `sleep(0.5)`，仅这两次等待就约为 1 秒，还没有计入检测和通信。\n\n图像是取图时得到的，指令发送时目标或机器人可能已经改变位置。更新越慢，下一条指令所依据的信息就可能越旧。循环耗时应在实际设备上记录，不能由某一次接口调用时间代替。\n\n条件固定、动作重复时，可以使用较简单的固定时长控制；需要根据可测偏差修正动作时，可以加入反馈。反馈是否有效还取决于测量和控制设计。本课视觉只修正方向，里程计只提供行进量估计，移动来宾的实时距离仍未测得。\n"))


nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
