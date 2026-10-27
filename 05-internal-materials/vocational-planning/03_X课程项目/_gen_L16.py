# -*- coding: utf-8 -*-
"""U4-L4 接待来宾（多传感器信息联合使用）——Notebook 的可执行镜像。
以 notebooks/U4-L4_接待来宾.ipynb 为源，2026-10-26 反向同步（文字校对；代码未变）；重新运行会覆盖该 Notebook。
现稿 40 cells（29 markdown / 11 code），STEP 01–11。
流程：wait_for_guest → turn_to_guest → approach → 教师确认的 do_action → stop_motion。
只面向一位站定来宾；按卷尺输入起步间距和里程计估计行进量接近，不实现动态目标跟随。
B08 按入门层次讲多路信息联合使用：相机用于检测和方向调整，里程计估计行进量，IMU z 轴角速度参与示例条件分支；
三路各自参与不同判断，不合成统一位置/姿态，也不实现融合算法。里程计是系统的位置估计结果，不是独立物理传感器。
记录检查三路分工、构造数据分支和实际结束原因；距离核查引用 L2 同一次停靠的三项间距记录，
说明交叉核对的作用与局限，不要求自动修正里程计。
IMU z 轴角速度 0.5 rad/s 差值是课堂示例条件，不能诊断侧倾/打滑或承担安全保护。
待核事项在 §4.4 明列：框高触发未按 3 m 标定；5 s 只作讨论条件，不作硬性验收；
1.2 ± 0.2 m 停靠需卷尺和现场观察；当前没有语音问候。一次流程演示不代替验收。
保留准备姿态、人工确认窗口、行走和收尾步骤；不追加打滑、轻推或侧倾实验。
状态：P1 修订稿，真机确认②未完成。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U4-L4_接待来宾.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# U4-L4：接待来宾（多传感器信息联合使用）
cells.append(md("# U4-L4：接待来宾（多传感器信息联合使用）\n\n**课程目标**\n\n1. 能说出「检测 → 转向 → 走近 → 致意」这条链里，每一步在什么条件下开始、什么条件下结束。\n2. 能说明相机、里程计和 IMU 分别参与流程中的什么判断，并说出停止条件的局限；发现异常时由教师人工中止。\n3. 能按验收标准逐条核对一次演示结果，并说明哪一条没达到、下一步改哪里。\n"))

# 一、本课要解决的问题
cells.append(md("## 一、本课要解决的问题\n\n前三课练习了转向、按里程计估计行进量，以及根据新图像修正方向。本课把检测、转向、走近和致意按条件连接，完成一次接待演示。\n\n实验中只有一位来宾，始终站在预先测量的位置。程序先判断检测框是否达到触发比例，再转向、走近；达到设定停止条件后调用致意动作，最后发送零速度指令。一次运行结束后，由教师协助重新摆位，再决定是否进行下一次。\n\n框高触发比例需要标定后才能与约 3 米的距离联系。走近仍按已测起步间距计算行进量，最终是否停在 1.2 ± 0.2 米处，要用卷尺检查。\n\n> **每一步怎样报告结果，程序又怎样根据结果决定继续还是结束？**\n"))

# 二、行为链的程序组织
cells.append(md("## 二、行为链的程序组织\n\n接待流程由几步依次执行。若转向没有完成就开始前进，机器人可能偏离来宾；若走近失败后仍执行致意，动作也没有发生在预期位置。因此，每一步都需要报告结果，后续步骤才能判断是否继续。\n"))

# 2.1 顺序执行
cells.append(md("### 2.1 顺序执行与结果返回\n\n主程序先运行转向函数，得到 `True` 才调用走近函数；走近函数返回“到位”，才调用致意动作。函数在这里既组织了一段操作，也把结果交给主程序。\n\n单独调试时，先确认当前环节的读数和结束条件，再连接后续步骤。循环运行完可能是达到目标，也可能是达到次数上限，不能仅凭函数返回就认为任务成功。\n"))

# 2.2 每一步的开始条件与结束条件
cells.append(md("### 2.2 每一步的开始与结束\n\n| 步骤 | 开始条件 | 结束或继续条件 |\n| --- | --- | --- |\n| 等待来宾 | 运行 `wait_for_guest()` | 15 秒内第一个检测框的框高占比超过 `NEAR_RATIO`，返回该检测结果；否则返回 `None` |\n| 转向 | 等待函数返回了检测结果 | 水平偏差小于 20 像素时返回 `True`；目标丢失或达到 60 轮上限则返回 `False` |\n| 走近 | 转向函数返回 `True` | 预计剩余行进量不超过 0.05 米且图像偏差小于 20 像素，返回“到位”；其他退出原因返回对应文字 |\n| 致意 | 走近返回“到位” | 调用预定义动作，等待任务返回后继续收尾；动作实际结果仍要观察和记录 |\n\n`NEAR_RATIO=0.35` 是待标定的示例比例，不能直接读成“距离 3 米”。“到位”也是程序条件的名称，实际间距仍需测量。发送零速度指令后，教师还需观察机器人是否停稳，确认动作空间合适。\n\n三类信息在流程中各有用途：相机提供触发线索和方向偏差，里程计估计行进量，IMU 角速度参与示例停止分支。里程计是系统的位置估计输出，并非机身上一只独立的物理传感器。本课把信息用于不同判断，没有把读数合成为统一的位置估计。\n\nL2的记录可用于核查估计差异：里程计推算间距依赖起步测量与直行条件，框高估距依赖标定与完整视野，卷尺用于测量实际间距。两项估计不一致时，应先检查这些条件。\n"))

# 2.3 异常分支
cells.append(md("### 2.3 流程提前结束的情况\n\n等待、转向或走近未完成时，当前程序会结束本次演示：\n\n- 15 秒内没有检测框达到触发比例，等待函数返回 `None`，主程序跳过后续步骤。\n- 转向中目标丢失，或 60 轮内仍未对准，转向函数返回 `False`，跳过走近与致意。\n- 走近中目标丢失，或角速度差超过 0.5 rad/s，函数发送零速度并返回原因。\n- 走近达到 200 轮上限仍未满足到位条件，发送零速度并报告循环上限。\n\n轮数上限随检测、通信和等待耗时变化，不能当作固定秒数。正常转向也可能触发角速度分支，它不是侧倾或安全诊断。异常由教师人工中止；程序结束后不会自动返回起点或重新等待来宾。\n"))

# 三、致意动作
cells.append(md("## 三、致意动作\n\n程序判定走近到位后，主程序会调用预定义动作完成致意。\n"))

# 3.1 动作接口的复用
cells.append(md("### 3.1 动作接口的复用\n\nU1-L4 已介绍如何执行预定义动作。本课沿用 `list_actions()` 查看动作库，再用 `do_action(action_id)` 执行动作。执行前确认机器人处于 `walk` 模式、已经站稳，且周围留有安全空间。\n"))

# 3.2 致意动作的选择
cells.append(md("### 3.2 致意动作的选择\n\n点头、挥手等动作的幅度和空间要求不同。结合接待任务选择一种，并由教师确认动作 ID、当前模式和周围空间是否适合执行。当前流程只调用预先选定的动作，没有语音问候功能。\n"))

# **STEP 01：** 连接机器人，查看动作库
cells.append(md("**STEP 01：** 连接机器人，查看动作库"))

# import time
cells.append(code("import time\n\nfrom boosteros.robots.booster import BoosterRobot\nfrom boosteros.brain import Detection\n\nrobot = BoosterRobot()\ndetector = Detection(model=\"person\")\nprint(\"已连接：\", robot.robot_info.model, robot.robot_info.serial_number)\n\nactions = robot.list_actions()\nfor a in actions:\n    print(a.id, a.type, f\"{a.duration:.2f} s\", \"可打断\" if a.interruptible else \"不可打断\")"))

# 3.3 记录动作 ID
cells.append(md("### 3.3 保存动作 ID\n\n在动作列表中找到教师确认可用的 ID，再把它赋给 `GREET_ID`。这一格只保存参数；真正调用动作在完整流程的走近步骤之后。\n\n**STEP 02：** 输入教师确认可用的动作 ID\n"))

# GREET_ID = int(input("输入教师确认可用的动作 ID："))
cells.append(code("GREET_ID = int(input(\"输入教师确认可用的动作 ID：\"))\nprint(\"本次致意动作 ID：\", GREET_ID)"))

# 四、实验：接待来宾流程
cells.append(md("## 四、实验：接待来宾流程\n\n⚠️ **安全**：本课包含连续转向和行走，全程由教师看护。开始前确认场地平整、行进路线清空，人员离开机器人正前方和行进路线。示例阈值不是安全检测；出现异常时由教师立即中止。结束时先退回 `prepare`，确认站稳后由人工扶坐，再进入 `damping`。\n\n📌 **前置**：U4-L1 / L2 / L3 三课；U1-L4 的预定义动作。\n"))

# 4.1 连接与模式确认
cells.append(md("### 4.1 场地与模式准备\n\n机器人已在 STEP 01 连接。在地面标出起点和来宾站位，用卷尺测量间距并固定机身测量参考点。来宾保持站定，两者之间的路线保持通畅，看护人员站在侧方。\n\n先确认画面能稳定检测到这位来宾。框高触发比例的观察需记录拍摄姿态；若与标定时不同，应先重新检查比例，不能直接沿用。\n\n**STEP 03：** 进入准备姿态\n"))

# robot.set_mode("prepare")
cells.append(code("robot.set_mode(\"prepare\")\nprint(\"当前模式：\", robot.get_mode())"))

# <font color="red">确认机器人已经手动拉起、完全站立稳定，身体周围空旷，有教师在旁看护，再运行下…
cells.append(md("<font color=\"red\">确认机器人已经手动拉起、完全站立稳定，身体周围空旷，有教师在旁看护，再运行下一格。</font>"))

# **STEP 04：** 进入行走模式
cells.append(md("**STEP 04：** 进入行走模式"))

# robot.set_mode("walk")
cells.append(code("robot.set_mode(\"walk\")\nprint(\"当前模式：\", robot.get_mode())"))

# 4.2 分步联调
cells.append(md("### 4.2 分步联调\n\nSTEP 05 检查转向，STEP 06 检查走近。每次运行前重新核对起点和来宾站位；前一次动作可能已经改变位置，不能直接把前一次的间距用于下一次。\n\n**STEP 05：** 单独运行转向\n\n<font color=\"red\">提示：来宾站在机器人前方偏一侧并保持站定，教师在侧方看护。保持目标可见，检查检测框水平中心是否进入 20 像素范围。这里用框中心判断方向，不用本格的框高估算距离；需要框高估距时，另按 L2 检查完整视野与标定条件。</font>\n"))

# Kp_yaw = 0.001                  # 示例比例系数（rad/s/像素），须由教师监…
cells.append(code("Kp_yaw = 0.001                  # 示例比例系数（rad/s/像素），须由教师监督核验\nmax_yaw_rate = 0.2              # 示例角速度上限（rad/s），须由教师监督核验\naligned = False\n\nfor i in range(60):\n    img = robot.get_image(img_type=\"rgb\")\n    found = detector.detect(img.to_numpy())\n    if not found:\n        robot.set_velocity(0, 0, 0)\n        print(\"画面里没有检测到来宾，停止本次测试\")\n        break\n    error = found[0].bbox.center_x - img.width / 2\n    if abs(error) < 20:\n        aligned = True\n        print(f\"第 {i + 1} 轮对准：偏差 {error:+.0f} 像素\")\n        break\n    yaw_rate = max(-max_yaw_rate, min(max_yaw_rate, -Kp_yaw * error))\n    time.sleep(0.5)\n    robot.set_velocity(0, 0, yaw_rate)\n    time.sleep(0.5)\n    robot.set_velocity(0, 0, 0)\n    print(f\"第 {i + 1} 轮：偏差 {error:+.0f} 像素\")\n\nrobot.set_velocity(0, 0, 0)\nif not aligned:\n    print(\"未达到对准条件；本次测试已停止\")"))

# **STEP 06：** 单独测试走近
cells.append(md("**STEP 06：** 单独测试走近\n\n<font color=\"red\">提示：来宾站定，机器人恢复到起点标记并大致对准来宾。重新测量起步间距；程序以“起步间距 − 1.2 米”得到计划行进量，清零后的里程计 x 用于估计前向位移。确认路线通畅，由教师看护。结束后用卷尺测最终间距，并记录结束原因。</font>\n"))

# start_gap = float(input("输入卷尺测得的起步间距（米）："))
cells.append(code("start_gap = float(input(\"输入卷尺测得的起步间距（米）：\"))\ntarget_gap = 1.2\ntravel_target = start_gap - target_gap\nif travel_target <= 0:\n    raise ValueError(\"起步间距必须大于目标停靠间距\")\n\nrobot.reset_odom()\nKp_yaw = 0.001                   # 示例比例系数（rad/s/像素），须由教师监督核验\nmax_yaw_rate = 0.2               # 示例角速度上限（rad/s），须由教师监督核验\nbase_wz = robot.get_imu().angular_velocity[2]\nthreshold = 0.5                  # 课堂示例停止条件，不是安全阈值\nreached = False\nx = 0.0\n\nfor i in range(200):\n    img = robot.get_image(img_type=\"rgb\")\n    found = detector.detect(img.to_numpy())\n    if not found:\n        robot.set_velocity(0, 0, 0)\n        print(\"画面里没有检测到来宾，停止本次测试\")\n        break\n\n    error = found[0].bbox.center_x - img.width / 2\n    x, y, yaw = robot.get_odom().pose_2d\n    remain = travel_target - x\n    wz = robot.get_imu().angular_velocity[2]\n\n    if abs(wz - base_wz) > threshold:\n        robot.set_velocity(0, 0, 0)\n        print(\"角速度读数与静止样本差值超过课堂示例阈值；停止演示，这不是安全诊断\")\n        break\n\n    if remain <= 0.05 and abs(error) < 20:\n        reached = True\n        robot.set_velocity(0, 0, 0)\n        print(f\"第 {i + 1} 轮达到停止条件：估计行进 {x:.3f} m，图像偏差 {error:+.0f} px\")\n        break\n\n    yaw_rate = max(-max_yaw_rate, min(max_yaw_rate, -Kp_yaw * error))\n    vx = 0.0 if remain <= 0.05 else (0.15 if remain < 0.3 else 0.3)\n    time.sleep(0.5)\n    robot.set_velocity(vx, 0, yaw_rate)  # vyaw 是角速度（rad/s）\n    time.sleep(0.5)\n    robot.set_velocity(0, 0, 0)\n    print(f\"第 {i + 1} 轮：估计还需行进 {remain:+.3f} m，图像偏差 {error:+.0f} px\")\n\nrobot.set_velocity(0, 0, 0)\nif not reached:\n    print(\"未达到停止条件；本次测试已停止\")\nprint(f\"清零后的里程计 x 分量：{x:.3f} m（仅作行进量估计）\")"))

# 4.3 完整行为链
cells.append(md("### 4.3 用函数连接完整流程\n\n单项测试完成后，先恢复起点和来宾站位，再运行完整流程。下面一格只定义函数，不会立即执行其中的转向或行走；STEP 08 才会调用这些函数。\n\n`wait_for_guest()` 返回检测结果或 `None`，`turn_to_guest()` 返回是否对准，`approach()` 返回结束原因，`stop_motion()` 发送零速度指令。主程序据这些返回值决定后续步骤。\n\n**STEP 07：** 定义等待、转向、走近和停止函数\n"))

# NEAR_RATIO = 0.35               # 粗略触发比例，不是测距值
cells.append(code("NEAR_RATIO = 0.35               # 粗略触发比例，不是测距值\n                                # 须在目标身形、相机位置和拍摄条件相近时由教师标定\n\ndef wait_for_guest(timeout=15.0):\n    \"\"\"返回第一个达到框高比例条件的检测框；超时返回 None。\"\"\"\n    t0 = time.time()\n    while time.time() - t0 < timeout:\n        img = robot.get_image(img_type=\"rgb\")\n        found = detector.detect(img.to_numpy())\n        if found and found[0].bbox.height / img.height > NEAR_RATIO:\n            return found[0]\n        time.sleep(0.2)\n    return None\n\n\ndef turn_to_guest(near=20, limit=60):\n    \"\"\"逐轮读取画面；第一个检测框的水平偏差小于 near 像素时返回 True。\"\"\"\n    Kp_yaw = 0.001\n    max_yaw_rate = 0.2\n    for _ in range(limit):\n        img = robot.get_image(img_type=\"rgb\")\n        found = detector.detect(img.to_numpy())\n        if not found:\n            robot.set_velocity(0, 0, 0)\n            return False\n        error = found[0].bbox.center_x - img.width / 2\n        if abs(error) < near:\n            robot.set_velocity(0, 0, 0)\n            return True\n        yaw_rate = max(-max_yaw_rate, min(max_yaw_rate, -Kp_yaw * error))\n        time.sleep(0.5)\n        robot.set_velocity(0, 0, yaw_rate)\n        time.sleep(0.5)\n        robot.set_velocity(0, 0, 0)\n    robot.set_velocity(0, 0, 0)\n    return False\n\n\ndef approach(travel_target, base_wz, limit=200):\n    \"\"\"按计划行进量接近并返回停止原因；最终间距仍须用卷尺测量。\"\"\"\n    robot.reset_odom()\n    Kp_yaw = 0.001\n    max_yaw_rate = 0.2\n    threshold = 0.5               # 课堂示例停止条件，不是安全阈值\n    for _ in range(limit):\n        img = robot.get_image(img_type=\"rgb\")\n        found = detector.detect(img.to_numpy())\n\n        if not found:\n            robot.set_velocity(0, 0, 0)\n            return \"来宾不在画面里，停止本次流程\"\n        if abs(robot.get_imu().angular_velocity[2] - base_wz) > threshold:\n            robot.set_velocity(0, 0, 0)\n            return \"角速度读数超过课堂示例阈值，停止演示；这不是安全诊断\"\n\n        error = found[0].bbox.center_x - img.width / 2\n        x, y, yaw = robot.get_odom().pose_2d\n\n        remain = travel_target - x\n        if remain <= 0.05 and abs(error) < 20:\n            robot.set_velocity(0, 0, 0)\n            return \"到位\"\n        yaw_rate = max(-max_yaw_rate, min(max_yaw_rate, -Kp_yaw * error))\n        vx = 0.0 if remain <= 0.05 else (0.15 if remain < 0.3 else 0.3)\n        time.sleep(0.5)\n        robot.set_velocity(vx, 0, yaw_rate)\n        time.sleep(0.5)\n        robot.set_velocity(0, 0, 0)\n    robot.set_velocity(0, 0, 0)\n    return \"达到循环上限，已停止\"\n\n\ndef stop_motion():\n    \"\"\"发送零速度指令；不会返回起点或等待下一位来宾\"\"\"\n    robot.set_velocity(0, 0, 0)\n    print(\"已发送零速度指令\")"))

# **STEP 08：** 跑一遍完整流程：检测 → 转向 → 走近 → 致意 → 停止
cells.append(md("**STEP 08：** 运行检测 → 转向 → 走近 → 致意 → 停止\n\n<font color=\"red\">提示：本格会实际转向和行走。重新测量起点到来宾的间距，确认来宾站定、路线通畅和致意动作空间合适，由教师全程看护。各步骤的返回值会决定继续或结束；出现异常由教师人工中止。</font>\n"))

# start_gap = float(input("输入卷尺测得的起点到来宾站位间距（米）："))
cells.append(code("start_gap = float(input(\"输入卷尺测得的起点到来宾站位间距（米）：\"))\ntarget_gap = 1.2\ntravel_target = start_gap - target_gap\nif travel_target <= 0:\n    raise ValueError(\"起步间距必须大于目标停靠间距\")\n\nguest = wait_for_guest()\nprint(\"检测到来宾\" if guest is not None else \"等待超时，未达到粗略触发条件\")\n\nif guest is not None:\n    turned = turn_to_guest()\n    print(\"转向：\", \"完成\" if turned else \"未完成\")\n\n    if turned:\n        base_wz = robot.get_imu().angular_velocity[2]\n        approach_result = approach(travel_target, base_wz)\n        print(\"走近：\", approach_result)\n\n        if approach_result == \"到位\":\n            handle = robot.do_action(GREET_ID)\n            handle.wait()\n            print(\"致意动作执行结束\")\n        else:\n            print(\"走近未到位，跳过致意动作\")\n    else:\n        print(\"转向未完成，跳过走近和致意\")\n\nstop_motion()"))

# 4.4 验收标准核对
cells.append(md("### 4.4 检查本次演示结果\n\n按照本次实际实现填写记录。程序流程运行结束，只表示到达了退出位置；是否满足距离与动作要求，还要有测量或观察依据。\n\n| 检查内容 | 使用的依据 | 记录要求 |\n| --- | --- | --- |\n| 来宾触发与转向 | 框高触发比例、水平偏差、实际触发位置 | 比例 0.35 尚未与 3 米对应，未标定时记录“距离条件待核实”；记录转向实际用时，不以 5 秒作达标条件 |\n| 最终停靠间距 | 卷尺测量，与 1.2 ± 0.2 米比较 | 分开记录程序结束原因、实际间距及是否停稳 |\n| 致意动作 | 选定动作 ID、任务状态及现场观察 | 当前调用的是预定义动作，没有语音问候；不能凭“等待返回”认定动作成功 |\n| 三类信息与停止分支 | 相机、里程计、IMU 在代码中的用途；STEP 09 示例输出 | 构造数值与真机读数分开记录；示例阈值不作安全判断 |\n| 距离估计的核查 | L2 同一次停靠的两项估计及卷尺数据 | 条件有效时比较差异；若身体不完整或拍摄姿态改变，标明估距条件不成立 |\n\n5 秒可用于讨论“希望更快完成转向时，应怎样逐步调整并检查结果”，不作为本课硬性验收目标。约 3 米的触发条件仍需现场标定；语音能力在 U5 学习，本课记录为未覆盖，不提前加入语音接口。\n"))

# 4.5 用构造数据检查停止分支
cells.append(md("### 4.5 用构造数据检查停止分支\n\n**STEP 09：** 用示例读数检查条件判断\n\n本格只用变量模拟条件判断，不读取传感器或发送运动指令。示例输出用于理解程序分支。"))

# base_wz_example = 0.0
cells.append(code("base_wz_example = 0.0\nthreshold_example = 0.5\nexamples = [\n    (\"未检测到来宾\", False, 0.0),\n    (\"角速度差超过示例阈值\", True, 0.6),\n    (\"角速度差未超过示例阈值\", True, 0.2),\n]\n\nfor label, guest_detected, sample_wz in examples:\n    print(f\"示例：{label}\")\n    if not guest_detected:\n        print(\"→ 当前流程停止，跳过致意动作\")\n    elif abs(sample_wz - base_wz_example) > threshold_example:\n        print(\"→ 角速度差超过示例阈值，当前流程停止\")\n    else:\n        print(\"→ 这两个示例条件均未触发\")"))

# 4.6 收尾
cells.append(md("### 4.6 收尾\n\n完整流程结束后，先发送零速度指令，再切回 `prepare`。确认机器人已稳定站立，再按下一步的人工扶坐要求收尾。\n\n**STEP 10：** 停止并回到准备姿态"))

# robot.set_velocity(0, 0, 0)
cells.append(code("robot.set_velocity(0, 0, 0)\nrobot.set_mode(\"prepare\")\nprint(\"当前模式：\", robot.get_mode())"))

# <font color="red">由人工扶着让机器人坐下，确认坐稳之后再运行下一格。</font>
cells.append(md("<font color=\"red\">由人工扶着让机器人坐下，确认坐稳之后再运行下一格。</font>"))

# **STEP 11：** 进入软态
cells.append(md("**STEP 11：** 进入软态"))

# robot.set_mode("damping")
cells.append(code("robot.set_mode(\"damping\")\nprint(\"当前模式：\", robot.get_mode())"))

# 五、进一步设计
cells.append(md("## 五、进一步设计\n\n当前实验限定为一位站定的来宾。以下两项是后续设计问题，当前代码尚未实现。\n"))

# 5.1 多人场景中的目标选择
cells.append(md("### 5.1 多人场景中的目标选择\n\n当前代码每轮使用检测列表中的第一个框，没有按距离排序，也没有持续跟踪某个人。多人场景需要先明确选择规则。例如，框较大可以作为距离较近的线索，但还会受身高、姿势和遮挡影响，不能保证选中最近的人。后续每轮还要确认检测到的仍是同一位来宾。\n"))

# 5.2 移动目标的跟踪
cells.append(md("### 5.2 移动目标的跟踪\n\n走近时程序会重新读取画面并调整方向，但前进量仍按起步时测得的间距计算。来宾移动后，原计划行进量可能不再合适。跟随移动目标还需要持续匹配同一个人、更新距离估计，并重新设计停止条件；仅仅把转向和走近放进循环还不够。\n"))

# 六、观察与记录
cells.append(md("## 六、观察与记录\n\n### 6.1 逐项检查结果\n\n| 检查内容 | 观察或测量依据 | 本次结果 |\n| --- | --- | --- |\n| 来宾触发及转向 | 触发位置、比例是否标定、最终水平偏差 | |\n| 最终间距与停稳 | 卷尺间距；与 1.2 ± 0.2 米比较；现场观察 | |\n| 致意动作 | 动作 ID、等待后的任务状态、实际动作表现 | |\n| 三类信息的用途 | 分别参与的判断、本次实际结束原因 | |\n| L2 距离核查 | 引用有效的标定、估计与卷尺记录 | |\n\n未标定的距离条件填写“待核实”。动作未执行、失败或无法确认时如实填写，不能仅根据打印“执行结束”判为成功。语音问候未在本课实现，单独注明“未覆盖”。\n\n引用 L2 的同一次停靠记录，无须再走一次：\n\n| 里程计推算间距（米） | 框高估距（米） | 卷尺实测（米） | 测量条件是否有效 |\n| --- | --- | --- | --- |\n| | | | |\n\n说明两项估计相差多少，复核后应检查哪些条件。没有有效框高或卷尺数据时，写明缺失项，不补造数值。\n\n### 6.2 各步骤用时\n\n| 步骤 | 实际用时（秒） | 计时方式及是否执行 |\n| --- | --- | --- |\n| 从调用等待函数到返回 | | |\n| 转向函数 | | |\n| 走近函数 | | |\n| 致意任务等待 | | |\n| 本次完整流程 | | |\n\n当前程序没有自动输出这些分段时间，可由同组同学用秒表记录近似用时，并注明人工计时。未执行的步骤填“未执行”；数据用于讨论流程耗时，不据此判定是否满足固定时限。\n\n### 6.3 构造数据分支记录\n\n| 构造情景 | 程序输出 | 是否与条件相符 |\n| --- | --- | --- |\n| 未检测到来宾 | | |\n| z 轴角速度差超过示例阈值 | | |\n| 两个示例条件均未触发 | | |\n\n### 6.4 检查点\n\n- 能否根据函数返回值解释流程为何继续或结束。\n- 能否用程序结束原因和现场记录区分“运行结束”与“任务要求达到”。\n- 能否说明本次流程结束后，重新演示前需要检查和恢复哪些条件。\n\n### 6.5 思考题\n\n- 本次哪一项没有达到预期？测量或输出提供了什么证据，下一次先检查什么？\n- 如果连续演示三次，每次开始前需要怎样恢复站位、重新测量并检查状态？\n- 三类信息分别影响哪些指令？如果其中一路数据无效，当前流程的哪个判断会失去依据？\n"))

# 七、扩展阅读：接待流程的重复测试
cells.append(md("## 七、扩展阅读：接待流程的重复测试\n\n同一段程序运行两次，停靠位置和用时可能不同。检测框会抖动，里程计存在估计误差，来宾的身高、站姿和光线也会影响检测结果。一次成功不足以说明换人或换位置后仍能达到相同效果。\n\n继续测试时，先固定来宾、机器人起点、站位、光线和地面，重复运行并记录触发位置、最终停靠间距、各步骤用时和停止原因。之后每次只改变一个条件，例如更换来宾或调整站位，再与原记录比较。距离用卷尺测量，每次运行前都由教师确认场地和机器人状态。\n\n当前流程遇到目标丢失等停止条件后会结束，不会自动恢复或等待下一位来宾。多人选择、移动目标跟踪和异常诊断都需要另外设计并验证。测试记录应写明本次条件、停止原因和未达到的要求，修改后按相同条件复测，才能比较改动是否有效。\n"))


nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
