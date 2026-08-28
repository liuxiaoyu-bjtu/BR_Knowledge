# -*- coding: utf-8 -*-
"""U1-L4 实训手册生成器。重新运行本脚本将覆盖生成 notebooks/U1-L4_头部步态与预定义动作.ipynb（与当前 42-cells 版本一致）。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U1-L4_头部步态与预定义动作.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []
# # U1-L4：头部、步态与预定义动作
cells.append(md("# U1-L4：头部、步态与预定义动作\n\n**课程目标**\n\n1. 认识机器人头部坐标系：理解俯仰角 `pitch`（低头 / 抬头）与偏航角 `yaw`（左转 / 右转）的含义与正方向，会用 `set_head_angle(pitch, yaw)` 控制头部姿态，理解头部视野与运动的关系。\n2. 掌握 `set_gait(\"soccer\" | \"default\")` 切换步态，对比不同步态对行走稳定性与效率的影响。\n3. 学会用 `list_actions()` 与 `do_action(action_id)` 调用机器人出厂预置动作，理解“预定义动作库”概念，并体验开环方式下的组合行为（边走边转头扫描）。\n"))
# ## 一、头部坐标系与角度指令
cells.append(md("## 一、头部坐标系与角度指令\n\n头部姿态由两个角度控制，单位均为弧度（rad）。下面先建立坐标系概念，再认识对应的编程接口。\n"))
# ### 1.1 头部自身坐标系（pitch / yaw）
cells.append(md("### 1.1 头部自身坐标系（pitch / yaw）\n\n以机器人头部为参照：\n\n| 角度 | 名称 | 正值方向 | 负值方向 | 物理限位（约） |\n| --- | --- | --- | --- | --- |\n| `pitch` | 俯仰角 | 低头（看向地面） | 抬头（看向天空） | -0.3 ~ 1.0 rad |\n| `yaw` | 偏航角 | 头向左转 | 头向右转 | -0.785 ~ 0.785 rad |\n\n> 注意：`yaw` 这里指“头部”的左右转动，与 L3 学到的机身 `yaw`（整机绕竖直轴转向）是不同层面的概念；两者都叫 yaw，但控制对象不同。\n"))
# ### 1.2 接口 `set_head_angle(pitch, yaw)`
cells.append(md("### 1.2 接口 `set_head_angle(pitch, yaw)`\n\n`set_head_angle(pitch, yaw)` 同时设置两个角度，单位 rad，立即生效。\n\n| 参数 | 含义 | 正方向 | 模式约束 |\n| --- | --- | --- | --- |\n| `pitch` | 头部俯仰 | 正值 = 低头 | 仅在 `walk` 模式下有效 |\n| `yaw` | 头部偏航 | 正值 = 头向左转 | 仅在 `walk` 模式下有效 |\n\n> ⚠️ 模式约束：`set_head_angle` **仅在 `walk` 模式下有效**。在 `damping` 或 `prepare` 下调用会报错。因此控制头部前，必须先让机器人进入 `walk` 态（见实验二）。\n"))
# ### 1.3 头部视野与运动
cells.append(md("### 1.3 头部视野与运动\n\n机器人“看世界”主要靠头部的相机。头部不动时，视野范围有限；若让头部在行走过程中左右转动（改变 `yaw`），就能在移动中扫描更宽的视野，这对后续“看到目标再行动”的任务非常关键。本课先在实验中分别体验低头、转头、回正，再在拓展活动里尝试“边走边转头扫描”的组合行为。\n"))
# ## 二、头部控制实验（set_head_angle）
cells.append(md("## 二、头部控制实验（set_head_angle）\n\n**目标**：用 `set_head_angle` 控制头部俯仰与转向，观察视野变化（核心概念 A08 / A09）。\n\n⚠️ **安全**：控制头部须进入 `walk` 模式（`set_head_angle` 仅在 walk 有效）；头部运动幅度有限，仍须留意头部附近无异物、周围空旷。\n\n📌 **前置**：已完成 L2 模式安全、L3 速度控制；机器人已开机、配网、可连接。\n"))
# ### 2.1 连接 K1 机器人
cells.append(md("### 2.1 连接 K1 机器人\n\n运行下面单元格建立连接（仅连接，不移动）。\n"))
# [code] from boosteros.robots.booster import Boo
cells.append(code("from boosteros.robots.booster import BoosterRobot\n\nrobot = BoosterRobot()\nprint(\"已连接 K1\")"))
# ### 2.2 安全规范（必读）
cells.append(md("### 2.2 安全规范（必读）\n\n- 进入 `walk` 前，必须确认已手动将机器人拉起至直立站立（STAND），周围 1.5 米内无遮挡、无人员靠近。\n- `set_head_angle` 仅在 `walk` 模式下有效；在 `prepare` / `damping` 下调用会报错。\n- 头部运动幅度有限，但仍需留意头部附近无异物。\n"))
# ### 2.3 低头（pitch > 0）
cells.append(md("### 2.3 低头（pitch > 0）\n\n<font color=\"red\">确定已经手动拉起机器人、机器人处于 `walk` 模式。</font>\n\n此步只调头部、不发送速度。取消下面注释运行，观察头部低头、相机视野移向地面。\n"))
# # robot.set_head_angle(0.3, 0)    # 低头约 0.3 rad，
cells.append(code("# robot.set_head_angle(0.3, 0)    # 低头约 0.3 rad，yaw 保持 0"))
# ### 2.4 转头（yaw > 0）
cells.append(md("### 2.4 转头（yaw > 0）\n\n取消注释运行，观察头部向左转动。\n"))
# # robot.set_head_angle(0, 0.5)    # 头向左转 0.5 rad
cells.append(code("# robot.set_head_angle(0, 0.5)    # 头向左转 0.5 rad，pitch 保持 0"))
# ### 2.5 回正
cells.append(md("### 2.5 回正\n\n取消注释运行，头部回到中位。\n"))
# # robot.set_head_angle(0, 0)      # 回正
cells.append(code("# robot.set_head_angle(0, 0)      # 回正"))
# ## 三、步态切换实验（set_gait）
cells.append(md("## 三、步态切换实验（set_gait）\n\n**目标**：用 `set_gait` 切换足球 / 标准步态，对比行走差异。\n\n📌 **前置**：头部实验已收尾回 `prepare`，机器人处于直立稳定。\n\n<font color=\"red\">执行下面任务前，确认场地空旷、周围 1.5 米内无人；进入 `walk` 后发送速度须保持低速（建议 0.3 m/s）、短时（约 2 秒）并及时停止。</font>\n"))
# ### 3.1 进入行走态
cells.append(md("### 3.1 进入行走态\n\n使用 `robot.list_gaits()` 查看当前支持的步态列表。\n"))
# [code] print("支持的步态：", robot.list_gaits())
cells.append(code("print(\"支持的步态：\", robot.list_gaits())"))
# ### 3.2 足球步态走一段
cells.append(md("### 3.2 足球步态走一段\n\n<font color=\"red\">确定已经手动拉起机器人、机器人处于 `walk` 模式且机器人处于相对空旷的环境中，保障行走不触碰环境中的其他物体。</font>\n\n取消注释运行：切换为足球步态，再发小幅前进速度，走约 2 秒后停止。\n"))
# [code] import time
cells.append(code("import time\n\n# robot.set_gait(\"soccer\")          # 切换为足球步态\n# robot.set_velocity(0.3, 0, 0)     # 前进 0.3 m/s\n# time.sleep(2)\n# robot.set_velocity(0, 0, 0)       # 停止"))
# ### 3.3 标准步态走一段
cells.append(md("### 3.3 标准步态走一段\n\n机器人仍处于 `walk` 模式。取消注释运行：切回标准步态，同样前进约 2 秒，对比与足球步态的手感 / 姿态差异。\n"))
# # robot.set_gait("default")       # 切回标准步态
cells.append(code("# robot.set_gait(\"default\")       # 切回标准步态\n# robot.set_velocity(0.3, 0, 0)\n# time.sleep(2)\n# robot.set_velocity(0, 0, 0)"))
# ### 3.4 回到站立稳定
cells.append(md("### 3.4 回到站立稳定\n\n实验结束，回到 `prepare` 站立稳定。\n"))
# # robot.set_velocity(0, 0, 0)
cells.append(code("# robot.set_velocity(0, 0, 0)\n# robot.set_mode(\"prepare\")"))
# ## 四、预定义动作实验（do_action）
cells.append(md("## 四、预定义动作实验（do_action）\n\n**目标**：用 `do_action(action_id)` 调用厂商预置动作，理解 `ActionInfo`（动作元数据）与返回的 `TaskHandle`（任务句柄）；并通过连续编排不少于两个动作（含 `upper_body` 与 `whole_body` 各一）体验动作组合。\n\n<font color=\"red\">执行下面任务前，确保机器人处于 `walk` 模式，并在周围空旷、教师监督下再运行动作；预定义动作幅度较大，请保持安全距离。</font>\n"))
# ### 4.1 认识动作库与步态（不移动机器人）
cells.append(md("### 4.1 认识动作库与步态（不移动机器人）\n\n复习 L1 学到的 `list_actions()`，认识可调用的预定义动作及其 `id`——`do_action` 正是通过该 `id` 指定要执行哪个动作。同时查看机器人支持的步态列表。本单元格只读取信息，不发送任何运动指令。"))
# [code] actions = robot.list_actions()
cells.append(code("actions = robot.list_actions()\nfor a in actions:\n    print(f\"id={a.id:<20} type={a.type:<12} 时长={a.duration}s 可打断={a.interruptible}\")\n\nprint(\"支持的步态：\", robot.list_gaits())"))
# ### 4.2 探究：ActionInfo 与 TaskHandle
cells.append(md("### 4.2 探究：ActionInfo 与 TaskHandle\n\n运行下面单元格，任选一个动作执行，并观察两类返回值：\n\n1. **`ActionInfo`（动作元数据）**：`list_actions()` 返回的每一项都是一个 `ActionInfo`，含 `id`、`type`、`duration`、`interruptible`。重点看 `type` 与 `interruptible` 的关系——对照 4.1 的列表，思考「哪一类动作可被中途打断（`interruptible=True`）？`type` 为 `upper_body` / `whole_body` 的动作，其可打断性有何不同？」\n2. **`TaskHandle`（任务句柄）**：`do_action(action_id)` 立即返回 `TaskHandle`，用来跟踪这次动作任务。`handle.status` 表示当前状态（`PENDING` / `RUNNING` / …）；`handle.done()` 为 `True` 表示已进入**终态**（`SUCCEEDED` / `FAILED` / `CANCELLED`）；`handle.wait()` 可阻塞等待到终态。\n\n> `do_action` 必须在 `walk` 模式下调用；若当前仍在 `prepare`，先取消下方第一行注释进入 `walk`（已直立，无需手动拉起）。\n\n"))
# # robot.set_mode("walk")                       #
cells.append(code("# robot.set_mode(\"walk\")                       # 若仍在 prepare，先进入 walk（已直立，无需手动拉起）\nact = actions[0]                               # 任选一个动作（以 4.1 读到的 id 为准，不要假定名字）\nprint(\"id =\", act.id, \" type =\", act.type, \" duration =\", act.duration, \" interruptible =\", act.interruptible)\n\nhandle = robot.do_action(act.id)               # 返回 TaskHandle\nprint(\"status =\", handle.status)               # PENDING / RUNNING / ...\nhandle.wait()                                  # 阻塞直到进入终态\nprint(\"done =\", handle.done(), \" final =\", handle.status)   # SUCCEEDED / FAILED / CANCELLED\n\n"))
# ### 4.3 学生自主任务：连续编排两个动作
cells.append(md("### 4.3 学生自主任务：连续编排两个动作\n\n根据 4.1 读到的 `ActionInfo`，编写程序完成**不少于两个连续动作**的编排，要求：\n\n- 至少包含 1 个 `type=\"upper_body\"` 的动作；\n- 至少包含 1 个 `type=\"whole_body\"` 的动作；\n- 两个动作依次执行，每个动作都等待其进入终态后再执行下一个（用 `handle.wait()`）。\n\n可任选具体 `id`，但必须基于 4.1 实际读到的动作列表筛选，不要硬编码想象中的动作名。下面给出一段可运行的脚手架，也可自行改写。\n\n"))
# # 4.3 学生任务脚手架：筛选并连续编排两个动作
cells.append(code("# 4.3 学生任务脚手架：筛选并连续编排两个动作\nupper = [a for a in actions if a.type == \"upper_body\"]\nwhole = [a for a in actions if a.type == \"whole_body\"]\n\nif upper and whole:\n    h1 = robot.do_action(upper[0].id); h1.wait()   # 先执行 upper_body 动作，等待终态\n    h2 = robot.do_action(whole[0].id); h2.wait()   # 再执行 whole_body 动作，等待终态\n    print(\"连续编排完成：\", upper[0].id, \"->\", whole[0].id)\nelse:\n    print(\"未找到所需的 upper_body / whole_body 动作，请检查 4.1 列表\")\n\n"))
# ### 4.4 收尾
cells.append(md("### 4.4 收尾\n\n动作实验结束，**严禁直接用程序进 `damping`**。先把机器人退回稳定站立状态，再按约定由人工完成断电流程。\n\n"))
# # robot.set_mode("prepare")   # 回到站立稳定（不行走）
cells.append(code("# robot.set_mode(\"prepare\")   # 回到站立稳定（不行走）"))
cells.append(md("<font color=\"red\">本实验结束：机器人已回到 `prepare` 直立稳定。若没有其他后续任务，请手动将机器人放置为趴姿，再按约定进入 `damping` → 关机。</font>"))
# ## 五、观察与记录：组合行为与开环（非代码）
cells.append(md("## 五、观察与记录：组合行为与开环（非代码）\n\n本节不写代码，请在下方表格中记录你的观察。本课三个实验（L2 模式、L3 运动、L4 头 / 步态 / 动作）都采用**开环**方式：发出指令后观察结果，不自动纠正偏差。\n\n| 实验 | 你发出的指令 | 实际观察到的现象 | 与预期的偏差 / 备注 |\n| --- | --- | --- | --- |\n| 头部控制 | `set_head_angle(0.3, 0)` |  |  |\n| 头部控制 | `set_head_angle(0, 0.5)` |  |  |\n| 步态切换 | `set_gait(\"soccer\")` 前进 |  |  |\n| 步态切换 | `set_gait(\"default\")` 前进 |  |  |\n| 预定义动作 | `do_action(actions[0].id)` |  |  |\n\n> 想一想：同样是“前进 0.3 m/s 走 2 秒”，足球步态和标准步态走出的距离、姿态是否一样？为什么开环实验里我们要亲手记录这些差异？\n"))
# ## 六、拓展活动：设计“边走边转头扫描”行为（非代码操作）
cells.append(md("## 六、拓展活动：设计“边走边转头扫描”行为（非代码操作）\n\n把本课学到的头部控制与 L3 的速度控制组合起来，可以形成一个简单但有价值的组合行为：**让机器人在前进的同时，头部左右转动扫描视野**。\n\n设计任务（文字记录即可）：\n\n1. 写出组合行为的指令顺序（先做什么、再做什么、何时回正）。\n2. 标注每个指令应在什么模式下发送（哪些必须在 `walk` 下）。\n3. 列出至少 2 条安全注意点。\n\n> 【附件提示：组合行为的步骤分解、场地布置与危险区标注较多，详见附件《K1 综合行为设计任务卡》，请结合图文完成任务设计。】\n"))
# ## 七、检查点、思考题与学习评价
cells.append(md("## 七、检查点、思考题与学习评价\n"))
# ### 7.1 分步检查点（完成一项就在框里打勾 ✓）
cells.append(md("### 7.1 分步检查点（完成一项就在框里打勾 ✓）\n\n- [ ] 已用 `list_actions()` 看到动作库，并理解 `id` 是用 `do_action` 指定动作的稳定标识\n- [ ] 已在 `walk` 模式下用 `set_head_angle` 完成低头、转头、回正\n- [ ] 已对比 `soccer` 与 `default` 两种步态的前进差异\n- [ ] 已通过 `do_action` 运行动作，并用 `TaskHandle` 确认其进入终态（`SUCCEEDED` / `FAILED` / `CANCELLED`）\n- [ ] 已完成不少于两个连续动作编排（至少含 `upper_body` 与 `whole_body` 各一个）\n- [ ] 实验结束机器人回到稳定状态（`walk → prepare`），未出现 `walk → damping`\n"))
# ### 7.2 思考题
cells.append(md("### 7.2 思考题\n\n1. 为什么 `set_head_angle` 必须在 `walk` 模式下调用？如果在 `prepare` 下调用会发生什么？\n2. `set_gait` 在“非 walk 模式”下设置会被记录、下次进入 walk 时生效——这个特性有什么用？举例说明。\n3. `do_action` 为什么用 `id` 而不是动作名字来指定动作？（提示：名字可能变，`id` 是稳定标识）\n"))
# ### 7.3 学习评价
cells.append(md("### 7.3 学习评价\n\n请独立完成以下题目。\n\n**一、判断题**（对的打√，错的打×）\n\n1. `set_head_angle(pitch, yaw)` 只能在 `walk` 模式下调用，在 `damping` / `prepare` 下调用会报错。（    ）\n\n**二、填空题**\n\n2. 切换步态用 `set_gait(____)`；若当前不在 `walk` 模式，该设置会 ______（填“立即生效”或“记录并在下次进入 walk 时生效”）。\n3. 头部俯仰角 `pitch` 的正值表示 ______（填“低头”或“抬头”）。\n\n**三、选择题**（单选）\n\n4. 下列接口中，用于在 walk 模式下控制机器人头部姿态的是（    ）。\n   A. `set_velocity`　　B. `set_gait`　　C. `set_head_angle`　　D. `do_action`\n\n5. `do_action` 指定要执行的动作时，应传入（    ）。\n   A. 动作名字字符串　　B. `list_actions()` 返回的 `id`　　C. 动作的 `duration`　　D. 任意整数\n\n> 参考答案（教师留存，勿印发给学生）：\n> 1. √　2. `\"soccer\"` 或 `\"default\"`（任写其一）；记录并在下次进入 walk 时生效　3. 低头　4. C　5. B\n"))
# ## 八、扩展阅读
cells.append(md("## 八、扩展阅读\n\n### 8.1 头部视野与感知\n\n人形机器人“理解环境”的第一步是“看到”。头部相机随头部姿态变化而改变视野方向；让头部在行走中主动转动（改变 `yaw`），比固定朝前能看到更多侧后方信息。这也是许多机器人采用“主动视觉”——不是被动接收画面，而是主动决定“看哪里”。后续课程会进一步把“看到的画面”转化为“该往哪走”的控制量。\n\n### 8.2 预定义动作库与机器人行为工程\n\n厂商把常用行为（挥手、鞠躬、踢球等）固化成“预定义动作”，开发者用 `do_action(id)` 一行调用即可，不必关心底层关节轨迹如何生成。这种方式让上层应用可以快速组合出“迎宾”“表演”等行为。更灵活的做法是把多个动作 / 运动指令按状态组织起来（例如“先走到人前 → 挥手 → 鞠躬”），这就进入了“行为编排”的领域，也是机器人工程里把简单能力组合成复杂任务的基本思路。\n"))
cells.append(md("---\n\n## 课程大纲映射（Phase 2 · 确认①审核用）\n\n> 本块为课程大纲对齐审核用，不面向学生；PDF 导出（P7）时统一删除。\n\n- **单元定位**：U1 人形机器人初探与运动控制 · L4 头部、步态与预定义动作\n- **双主线**\n  - 技能线：连接 → 模式 → 速度 → 头部 → 步态 → 预定义动作\n  - 认知线：自身坐标系（x/y/yaw）→ 头部坐标系（pitch/yaw）→ 运动参数化 → 行为组合\n- **核心概念标注**\n  - **A08 俯仰角 Pitch**：本课新引入。头部低头 / 抬头的角度，正值 = 低头。\n  - **A09 偏航角 Yaw**：L3 已作为“机身绕竖直轴转向”轻量引入；本课扩展到“头部 yaw（左右转头）”，同一名称但控制对象不同，需在教学中明确区分。\n  - 本课**不引入** 闭环 / 里程计 / IMU（属 U2 / U4），保持严格开环（发指令、测偏差、做记录）。\n- **SDK 接口对齐**\n  - `set_head_angle(pitch, yaw)`（仅 walk 有效；pitch 正 = 低头，yaw 正 = 左转）\n  - `set_gait(\"soccer\" | \"default\")`（非 walk 仅记录，walk 立即切换）\n  - `do_action(action_id)`（用 `list_actions()` 的 `id`）\n  - `list_actions()` / `list_gaits()`（读取，不移动）\n- **安全约束（§3.6 / §3.8）**\n  - `set_head_angle` 仅在 walk 有效；预定义动作需在 `walk` 模式下调用 + 空旷 + 教师监督\n  - 进入 `walk` 的**首次**（需手动拉起 STAND）仍须 `prepare` 独立 cell → 人工确认拉起 → `walk` 独立 cell；其余步骤仅在必要代码前用一句话标注所需模式，不逐格重复拆分（见 §3.8 修订）\n  - 收尾先 `walk → prepare`（站立稳定），再手动趴姿 → `damping`（严禁直接用程序进 `damping`）\n- **大纲轻任务对齐**\n  - ④ 组合运动：边走边转头扫描 → 拓展活动（六）设计，实验二 / 三提供基础能力\n  - ⑤ 足球步态 vs 默认步态对比 → 实验三（3.2 / 3.3）\n  - ⑥ 探究 ActionInfo / TaskHandle 终态 + 连续编排两动作（upper_body 与 whole_body 各一） → 实验四（4.2 / 4.3）\n"))
nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
