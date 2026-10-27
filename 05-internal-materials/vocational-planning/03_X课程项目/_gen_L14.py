# -*- coding: utf-8 -*-
"""U4-L2 走近来宾（距离估计与核对）——Notebook 的可执行镜像。
以 notebooks/U4-L2_走近来宾.ipynb 为源，2026-10-26 反向同步（文字校对；代码未变）；重新运行会覆盖该 Notebook。
现稿 41 cells（30 markdown / 11 code），STEP 01–11。
学生任务：区分行进量与来宾间距；在 walk 模式清零里程计并按计划行进量停止；
用同一位来宾在 1.2 m 处的框高占比粗略估距，在 1.5 m 处检查；全身视野及拍摄姿态须一致，
条件不满足时停止估距并记录原因；实验结构与控制代码待按复评方案另行调整。
把同一次停靠的里程计推算间距、框高估距、卷尺实测并列比较，提出下一次运行前应检查的条件。
教学层次：标定(B11)、传感局限(B12)；单次偏差与持续漂移分开说明，
不要求优化里程计、实现融合定位或根据视觉结果自动补走。
代码条件：get_odom().pose_2d 的 x 只在清零后基本直行时近似表示行进量；
Detection(model="person") 只安排一位站定来宾，传入 to_numpy() 的结果。
运行与收尾保留 prepare → 人工拉起确认 → walk；零速度 → prepare → 人工扶坐 → damping。
状态：P1 修订稿，真机确认②未完成。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U4-L2_走近来宾.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# U4-L2：走近来宾（距离估计与核对）
cells.append(md("# U4-L2：走近来宾（距离估计与核对）\n\n**课程目标**\n\n1. 能区分里程计估计的行进量与机器人到来宾的间距，并说明两者为什么不能直接等同。\n2. 能在 `walk` 模式下清零里程计、控制一段行进量，并用卷尺核对最终停靠间距。\n3. 能用同一位来宾的框高占比粗略估距，与里程计推算间距、卷尺实测对照，说明增加一条感知线索能帮助核查什么。\n"))

# 一、本课要解决的问题
cells.append(md("## 一、本课要解决的问题\n\n上节课用图像中的目标位置调整朝向。对准以后，还需要决定向前走多远。本课中来宾保持站定，先用卷尺测起步间距，再计算计划行进量。\n\n目标停靠间距设为 1.2 米，允许误差为 0.2 米。这是本次课堂任务的检查范围。机器人按里程计读数停止后，还要用卷尺测量实际停靠间距。\n\n> **里程计记录的行进量，与机器人实际走过的距离相差多少？图像还能提供什么距离线索？**\n"))

# 二、里程计里的距离
cells.append(md("## 二、里程计里的距离\n\n要控制行进量，先读取机器人在里程计坐标中的位置估计。BoosterOS SDK 通过里程计接口返回位置和朝向；这些值是系统估算结果，不是卷尺测量值。\n"))

# 2.1 里程计的数
cells.append(md("### 2.1 里程计中的位置\n\n`pose_2d` 返回里程计参考坐标中的 x、y 和朝向角，单位分别是米、米和弧度。x、y 表示估计位置，朝向角表示机器人面向哪个方向。\n\n清零后，机器人基本沿参考坐标的 x 轴直行时，x 的变化可近似作为前向位移。转弯或明显偏航时，x 只是这个方向上的位置变化，不能代表整段路程。\n\n要检查读数是否接近实际位移，需要在地面标记起点和终点，并用卷尺测量。两次测量应选择机身同一个参考点，避免把起止点选择的差异算成里程计误差。\n"))

# **STEP 01：** 连接机器人，读一次里程计
cells.append(md("**STEP 01：** 连接机器人，读一次里程计"))

# from boosteros.robots.booster import BoosterRobot
cells.append(code("from boosteros.robots.booster import BoosterRobot\n\nrobot = BoosterRobot()\n\nprint(\"已连接：\", robot.robot_info.model, robot.robot_info.serial_number)\nprint(\"当前模式：\", robot.get_mode())\n\nodom = robot.get_odom()\nprint(\"里程计返回值：\", odom)\n\nx, y, yaw = odom.pose_2d\nprint(f\"位置：x = {x:.3f} m，y = {y:.3f} m\")\nprint(f\"方向：{yaw:.3f} rad\")"))

# 2.2 清零与累计
cells.append(md("### 2.2 清零与累计\n\n`reset_odom()` 把当前位置和朝向设为里程计的参考零位，机器人本身不会移动。清零以后的位置读数，都相对于这个参考位姿表示。\n\nSDK 要求在 `walk` 模式下清零。本课实际运动和清零在第五节进行；STEP 02 使用假设数值，先练习计算计划行进量。\n"))

# 2.3 还差多少
cells.append(md("### 2.3 还差多少\n\n里程计行进量和来宾间距是两个不同的量。假设机器人起步时离来宾 2.0 米，目标停在 1.2 米处，计划行进量约为 `2.0 - 1.2 = 0.8` 米。\n\n如果计划行进量是 0.8 米、当前里程计估计走了 0.35 米，那么还差 `0.8 - 0.35 = 0.45` 米。这个计算用于控制行进量；最终是否停在目标间距，仍要用卷尺实测。\n\n```\n还差多少 = 计划行进量 − 里程计估计的已行进量\n```\n\n计划行进量要根据起步间距和目标停靠间距计算，不能把「停在来宾前 1.2 米」直接写成「机器人走 1.2 米」。\n"))

# **STEP 02：** 先只算一次「还差多少」，不发指令
cells.append(md("**STEP 02：** 先只算一次「还差多少」，不发指令"))

# start_gap = 2.0                 # 示例输入：假设卷尺测得起步间距为 2.0 m
cells.append(code("start_gap = 2.0                 # 示例输入：假设卷尺测得起步间距为 2.0 m\ntarget_gap = 1.2                 # 目标停靠间距（米）\ntravel_target = start_gap - target_gap\ncurrent_travel = 0.35            # 假设示例：里程计估计的行进量（米）\nremain = travel_target - current_travel\nprint(f\"计划行进 {travel_target:.2f} m，已估计行进 {current_travel:.2f} m，还差 {remain:.2f} m\")"))

# 三、里程计读数偏差与漂移
cells.append(md("## 三、里程计读数偏差与漂移\n\n里程计提供的是估计值。它和实际位移之间可能有偏差，需要用卷尺测量结果核对。\n"))

# 3.1 里程计误差如何形成
cells.append(md("### 3.1 读数偏差与漂移\n\n第五节会让机器人实际走一段。停下后，把里程计估计的前向位移与卷尺测得的实际位移比较，两者之差是本次读数偏差。\n\n如果位置估计的误差在运动中不断累积，估计位置会逐渐偏离实际位置，这种现象通常称为漂移。一次停靠的差值只能描述这次结果；要观察误差是否随行进距离增加，还需在不同距离下重复测量。\n\n地面、运动速度、行进方向及测量参考点都会影响比较结果。记录时保留这些条件，不能只凭一次偏差给所有行走任务加上同一个修正值。\n"))

# 3.2 读数偏差怎么记录
cells.append(md("### 3.2 读数偏差怎么记录\n\n比较时，用里程计估计的行进量减去卷尺测得的实际行进量，记录差值及正负。单次差值描述这次的偏差；多次实验可以比较偏差的大小和方向。要判断漂移是否随行进距离增加，还需在不同距离下重复测量。\n"))

# 四、框大小的距离标定
cells.append(md("## 四、框大小的距离标定\n\n除了里程计估计，图像中的目标大小也能提供一条距离线索。\n"))

# 4.1 框大小与距离
cells.append(md("### 4.1 框高与距离\n\n同一位来宾保持站姿、相机位置和朝向不变时，距离变近，完整人形在画面中的高度通常增大。本课用“检测框高度 ÷ 图像高度”表示框高占比。\n\nU3-L4 用框大小区分近、中、远。本课加入卷尺测得的距离，尝试把框高占比换算为米。\n\n这一换算需要检测框始终对应相同的身体范围。靠近后若头部或脚部离开画面，检测框不再表示相同范围，框高可能接近画面高度却不再随距离正常变化。此时应记录“目标不完整，估距条件不成立”，停止使用该次框高估距。\n"))

# 4.2 已知距离上的标定
cells.append(md("### 4.2 已知距离上的标定\n\n标定是在已知条件下建立读数与实际量之间的对应。本实验先用卷尺量出 1.2 米间距，记录这时的框高占比；随后在 1.5 米处检查换算结果。\n\n这两个位置都必须能看到同一位来宾的完整身体。如果 1.2 米处无法满足这一条件，先记录画面情况并交教师调整实验距离，不继续套用下面固定为 1.2 米的换算代码。\n\n取图时记录机器人是坐姿还是站姿、头部朝向及图像尺寸。后续行走实验若改变相机高度或头部角度，需要在新的拍摄姿态下重新标定。\n"))

# **STEP 03：** 在已知距离上读一次框
cells.append(md("**STEP 03：** 在已知距离上记录框高占比\n\n<font color=\"red\">提示：本格只取图，不发送运动指令。画面中只安排同一位站定的来宾，用卷尺测量至 1.2 米处。先检查图像能否容纳来宾完整身体；条件不满足时记录原因，交教师调整。后面的 1.5 米检查保持站姿、遮挡和拍摄姿态一致。</font>\n"))

# from boosteros.brain import Detection
cells.append(code("from boosteros.brain import Detection\nimport matplotlib.pyplot as plt\n\ndetector = Detection(model=\"person\")\n\nimg = robot.get_image(img_type=\"rgb\")\nimg_array = img.to_numpy()\nprint(\"画面尺寸：\", img.width, \"×\", img.height)\n\nresults = detector.detect(img_array)\nprint(\"检测到\", len(results), \"个目标\")\nh_ratio_1m2 = None\n\nif results:\n    r = results[0]  # 本实验只安排一位来宾；代码取第一个检测框，不识别来宾身份\n    h_ratio = r.bbox.height / img.height\n    if r.bbox.height > 0 and h_ratio > 0:\n        h_ratio_1m2 = h_ratio\n        print(f\"{r.class_name}  置信度 {r.confidence:.2f}\")\n        print(f\"框高 {r.bbox.height} 像素，占画面高度 {h_ratio:.3f}\")\n    else:\n        print(\"检测框高度无效，请检查画面后重新取图\")\nelse:\n    print(\"没有检测到来宾，请调整位置后重新取图\")\n\nplt.imshow(img_array)               # get_image(img_type=\"rgb\") 已返回 RGB 图像\nplt.show()"))

# 4.3 占比与距离的对应
cells.append(md("### 4.3 从框高占比估算距离\n\n把已知距离记为 `d0`，对应框高占比记为 `r0`，当前框高占比记为 `r`。同一位来宾在完整可见、拍摄条件相近时，可作近似换算：\n\n```\n估计距离 = d0 × r0 ÷ r\n```\n\n例如，标定距离为 1.2 米，当前框高占比是标定时的一半，则估计距离为 2.4 米。这是用于解释公式的假设数据。当前占比增大时，估计距离会减小，符合近大远小的变化方向。\n\n这里使用高度占比，没有使用检测框面积。身高、站姿、遮挡、透视和检测框抖动都会影响结果，必须与卷尺读数核对。目标不完整时，前面的近似关系不成立。\n"))

# **STEP 04：** 用第二个已知距离检查估算（只读图，不发指令）
cells.append(md("**STEP 04：** 用第二个已知距离检查估算（只读图，不发指令）\n\n<font color=\"red\">提示：画面中仍只保留同一位来宾。把他移到离机器人 1.5 米的位置，重新用卷尺测量并取图。不要复用 1.2 米处的旧画面；估算值与卷尺实测值一起记录。</font>"))

# if h_ratio_1m2 is None:
cells.append(code("if h_ratio_1m2 is None:\n    print(\"没有有效的 1.2 m 标定值，请先重新运行 STEP 03\")\nelse:\n    img_check = robot.get_image(img_type=\"rgb\")\n    results_check = detector.detect(img_check.to_numpy())\n    if not results_check:\n        print(\"画面里没有目标，无法估算；请调整位置后重新取图\")\n    else:\n        box_height = results_check[0].bbox.height\n        h_ratio_now = box_height / img_check.height\n        if box_height <= 0 or h_ratio_now <= 0:\n            print(\"检测框高度无效，无法估算距离\")\n        else:\n            actual_gap = float(input(\"输入卷尺测得的当前间距（米）：\"))\n            distance_est = 1.2 * (h_ratio_1m2 / h_ratio_now)\n            error = distance_est - actual_gap\n            print(f\"框高估算 {distance_est:.2f} m，卷尺实测 {actual_gap:.2f} m\")\n            print(f\"本次估算误差 {error:+.2f} m\")"))

# 4.4 更换来宾后重新标定
cells.append(md("### 4.4 重新标定的条件\n\n本课使用 `Detection(model=\"person\")`，检测对象是人。更换来宾、明显改变站姿、相机高度或头部朝向后，原来的框高比例可能不再适用，需要重新标定。\n\n更换成其他目标类别时，检测模型和标定数据都要重新检查。人形的标定值不能直接用于瓶子等其他目标。\n"))

# 五、实验：走近来宾并核对间距
cells.append(md("## 五、实验：走近来宾并核对间距\n\n⚠️ **安全**：本课有连续行走，请在平整、无障碍的场地上进行。机器人起步前确认前方无人，走的过程中人员不要站在正前方。准备指令与执行指令分开执行，中间留人工确认的时间。结束时先退回 `prepare`，再由人工扶坐，最后 `damping`。\n\n📌 **前置**：U4-L1 的转向来宾；U2-L3 的里程计读数与清零。\n"))

# 5.1 连接与模式确认
cells.append(md("### 5.1 场地与模式准备\n\n在地面标出机器人起点和来宾站位，来宾全程站定。用卷尺测量两者间距，并记录机器人机身的测量参考点；行走后仍用同一参考点测量。两点之间留出通畅路线，看护人员站在路线侧方。\n\n**STEP 05：** 让机器人进入准备姿态\n"))

# robot.set_mode("prepare")
cells.append(code("robot.set_mode(\"prepare\")\nprint(\"当前模式：\", robot.get_mode())"))

# <font color="red">确认机器人已经手动拉起、完全站立稳定，身体周围空旷，有教师在旁看护，再运行下…
cells.append(md("<font color=\"red\">确认机器人已经手动拉起、完全站立稳定，身体周围空旷，有教师在旁看护，再运行下一格。</font>"))

# **STEP 06：** 进入行走模式
cells.append(md("**STEP 06：** 进入行走模式"))

# robot.set_mode("walk")
cells.append(code("robot.set_mode(\"walk\")\nprint(\"当前模式：\", robot.get_mode())"))

# 5.2 按里程计行进量控制
cells.append(md("### 5.2 按里程计估计行进量停止\n\n进入 `walk` 后清零里程计。卷尺测得起步间距为 `start_gap`，目标间距为 1.2 米，两者相减得到计划行进量 `target_travel`。\n\n程序每轮读取里程计 x 分量，计算还需行进多少，再发送前进速度；读数接近计划值时发送零速度指令。这是按里程计估计值停止，实际位移和最终间距仍需测量。\n\n**STEP 07：** 实际行走，并记录停止位置\n\n<font color=\"red\">提示：本格会让机器人前进。先测起步间距，确认来宾站定、两者之间无人经过，并由教师在侧方看护。停下后测量起止标记之间的实际前向位移，以及机器人与来宾的最终间距。</font>\n"))

# import time
cells.append(code("import time\n\nstart_gap = float(input(\"输入卷尺测得的起步间距（米）：\"))\ntarget_gap = 1.2                 # 目标停靠间距（米）\ntarget_travel = start_gap - target_gap\nif target_travel <= 0:\n    raise ValueError(\"起步间距必须大于 1.2 米目标间距\")\n\nrobot.reset_odom()               # SDK 要求在 walk 模式调用\n\nreached = False\nx = 0.0\n\nfor i in range(200):\n    x, y, yaw = robot.get_odom().pose_2d\n    remain = target_travel - x\n    if remain <= 0.02:\n        reached = True\n        print(f\"第 {i + 1} 轮接近计划行进量：里程计估计 {x:.3f} m\")\n        break\n    robot.set_velocity(0.3, 0, 0)\n    print(f\"第 {i + 1} 轮：已走 {x:.3f} m，还差 {remain:.3f} m\")\n    time.sleep(0.2)\n\nrobot.set_velocity(0, 0, 0)\nif not reached:\n    print(\"达到循环上限，已停止；请检查场地和里程计读数\")\nprint(f\"已停止。里程计估计行进量 {x:.3f} m；最终间距请用卷尺测量\")"))

# 5.3 里程计行进后用框估算作对照
cells.append(md("### 5.3 重复行进并保留同一次停靠的数据\n\n第二次实验保持相同起点、来宾站位和行进方向。由教师协助恢复到地面标记处，再用卷尺重新测量起步间距；`reset_odom()` 只清零读数，不会让机器人回到起点。\n\n这次停靠后保留三项数据：卷尺起步间距、停稳后的里程计行进量、停稳后的图像。下一步用它们推算间距，再与卷尺实测比较。\n\n**STEP 08：** 按计划行进量停止，保留本次停靠位置\n"))

# start_gap_compare = float(input("输入第二次实验卷尺测得的起步间距（米）："))
cells.append(code("start_gap_compare = float(input(\"输入第二次实验卷尺测得的起步间距（米）：\"))\ntarget_gap = 1.2\ntarget_travel = start_gap_compare - target_gap\nif target_travel <= 0:\n    raise ValueError(\"起步间距必须大于 1.2 米目标间距\")\n\nrobot.reset_odom()\nreached = False\nx = 0.0\n\nfor i in range(200):\n    x, y, yaw = robot.get_odom().pose_2d\n    if target_travel - x <= 0.02:\n        reached = True\n        print(f\"第 {i + 1} 轮：里程计估计行进量 {x:.3f} m\")\n        break\n    robot.set_velocity(0.3, 0, 0)\n    time.sleep(0.2)\n\nrobot.set_velocity(0, 0, 0)\nif not reached:\n    print(\"达到循环上限，已停止；本次未确认到达计划行进量\")\nprint(f\"已停下。里程计估计行进量 {x:.3f} m；最终间距请用卷尺测量\")"))

# 5.4 用框高估算作对照
cells.append(md("### 5.4 比较同一次停靠的间距估计\n\n来宾站定、机器人基本直行时，用“起步间距 − 里程计估计行进量”推算当前间距。另一项估计来自停稳后新取的画面，使用第四节的框高比例换算。\n\n运行前确认标定与当前拍摄的机身姿态、相机朝向一致，且来宾完整可见；若姿态改变，先在当前姿态下重做 STEP 03、04。目标被裁切或明显偏航时，记录条件不满足，不把下面输出的数值当作有效估距结果。\n\n**STEP 09：** 比较里程计推算间距、框高估距和卷尺实测\n\n运行后分别看两项差值：正值表示估计间距偏大，负值表示估计间距偏小。本格只计算和打印结果，不发送运动指令，也不会根据视觉估计自动补走。\n"))

# x_stop, y_stop, yaw_stop = robot.get_odom().pose_2d
cells.append(code("x_stop, y_stop, yaw_stop = robot.get_odom().pose_2d\nodom_gap_est = start_gap_compare - x_stop\nprint(f\"停稳后里程计 x={x_stop:.3f} m，推算剩余间距 {odom_gap_est:.2f} m\")\n\nimg = robot.get_image(img_type=\"rgb\")\nresults = detector.detect(img.to_numpy())\n\nif h_ratio_1m2 is None:\n    print(\"没有有效的 1.2 m 标定值，无法估算\")\nelif results:\n    box_height = results[0].bbox.height\n    h_ratio_now = box_height / img.height\n    if box_height > 0 and h_ratio_now > 0:\n        distance_est = 1.2 * (h_ratio_1m2 / h_ratio_now)\n        actual_gap_after = float(input(\"输入卷尺测得的当前停靠间距（米）：\"))\n        print(f\"里程计推算间距 {odom_gap_est:.2f} m；框高估算间距 {distance_est:.2f} m\")\n        print(f\"卷尺实测间距 {actual_gap_after:.2f} m\")\n        print(f\"里程计推算与实测相差 {odom_gap_est - actual_gap_after:+.2f} m\")\n        print(f\"框高估算与实测相差 {distance_est - actual_gap_after:+.2f} m\")\n    else:\n        print(\"框高为 0，无法估算距离\")\nelse:\n    print(\"画面里没有目标，无法估算；请用卷尺记录实际间距\")"))

# 5.5 三种距离读数的区别
cells.append(md("### 5.5 三项间距结果怎样解读\n\n里程计推算间距需要已知起步间距，并假设来宾站定、机器人基本直行。框高估距需要同一位来宾和适用的标定条件。卷尺实测用于核对本次停靠间距，也要保持测量参考点一致。\n\n假设里程计推算为 1.20 米，框高估距为 1.45 米，仅凭两项估计无法确定哪项更接近实际。测量卷尺间距后，再检查起步测量、直行情况、拍摄姿态和检测框完整性，才能解释本次差异。\n\n视觉估距提供了独立于起步间距减里程计行进量的核查信息。两项估计不一致，可以提醒我们重新检查测量条件；它们一致，也可能仍存在误差。把同一次停靠的结果填入第六节，不把一次比较解释成已经提高了定位精度。\n"))

# 5.6 收尾
cells.append(md("### 5.6 收尾\n\n走完先把速度清零，再让机器人退出行走模式、站稳定住。\n\n**STEP 10：** 停止并回到准备姿态"))

# robot.set_velocity(0, 0, 0)
cells.append(code("robot.set_velocity(0, 0, 0)\nrobot.set_mode(\"prepare\")\nprint(\"当前模式：\", robot.get_mode())"))

# <font color="red">由人工扶着让机器人坐下，确认坐稳之后再运行下一格。</font>
cells.append(md("<font color=\"red\">由人工扶着让机器人坐下，确认坐稳之后再运行下一格。</font>"))

# **STEP 11：** 进入软态
cells.append(md("**STEP 11：** 进入软态"))

# robot.set_mode("damping")
cells.append(code("robot.set_mode(\"damping\")\nprint(\"当前模式：\", robot.get_mode())"))

# 六、观察与记录
cells.append(md("## 六、观察与记录\n\n### 6.1 行进与停靠记录\n\n| 实验 | 起步间距（卷尺） | 计划行进量 | 里程计估计行进量 | 最终间距（卷尺） |\n| :--- | :---: | :---: | :---: | :---: |\n| STEP 07 | 　　　　 | 　　　　 | 　　　　 | 　　　　 |\n| STEP 08 | 　　　　 | 　　　　 | 　　　　 | 　　　　 |\n\n将 STEP 08 停靠后的读数放在一起比较，距离单位均为米：\n\n| 起步间距（卷尺） | 里程计估计行进量 | 里程计推算剩余间距 | 框高估算间距 | 卷尺实测间距 |\n| :---: | :---: | :---: | :---: | :---: |\n| 　　　　 | 　　　　 | 　　　　 | 　　　　 | 　　　　 |\n\n里程计推算剩余间距 = 起步间距 − 里程计估计行进量。这一计算适用于来宾站定、机器人基本沿直线接近的条件。分别计算两项估计与卷尺实测的差值；若两项估计不一致，写下下一次行进前准备检查的条件。\n\n### 6.2 框大小标定的记录\n\n| 用途 | 卷尺实测距离 | 框高占画面高度比例 | 框高估算距离 | 估算误差 |\n| :--- | :---: | :---: | :---: | :---: |\n| 标定 | 1.2 m | 　　　　 | 不适用 | 不适用 |\n| STEP 04 检查 | 1.5 m | 　　　　 | 　　　　 | 　　　　 |\n| STEP 09 停靠后估算 | 　　　　 | 　　　　 | 　　　　 | 　　　　 |\n\n估算误差 = 框高估算距离 − 卷尺实测距离。正值表示估算距离偏大，负值表示估算距离偏小。\n\n### 6.3 检查点\n\n- 是否能区分机器人行进量和到来宾的间距，并说明各自如何测量。\n- 是否能说出框高估算需要哪些已知条件，以及身高、姿势和遮挡会怎样影响结果。\n- 是否能把里程计推算间距、框高估距和卷尺实测放在一起比较，并说明本次差异不能证明长期漂移或某一来源总是更准确。\n\n### 6.4 思考题\n\n- 目标保持静止时，里程计控制仍可能与 1.2 米的目标间距有偏差。来宾移动后，起步间距与目标的相对位置会怎样变化？\n- 里程计推算和框高估距都与卷尺实测不一致时，你会先检查哪些测量条件？一次实验能否判断哪种估计长期更可靠？\n- 「还差多少」这个判断，和上一课偏差那个判断，写法上有哪些地方是一样的？\n"))


nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
