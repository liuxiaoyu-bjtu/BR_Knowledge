# 课程实验 notebook（.ipynb）开发规则

> **用途**：本课程全部实验以 Jupyter Notebook 为单一源文件。本文件汇总编写时**必须把握的规则**，随开发动态维护。
> **维护方式**：每新增/修正一条规则，追加到对应章节并在底部「变更记录」登记日期与摘要。
> **适用对象**：`vocational-planning/03_X课程项目/notebooks/` 下所有 `U{单元}-L{课时}_{关键名}.ipynb`。

---

## 1. 文件与工作流

- 单一源文件 = `.ipynb`（Jupyter Notebook），由 `python cells` + 必要的 `markdown` 说明组成。
- 未来导出 PDF 即「实训手册」；学生端直接打开 notebook 学习，教师端导出 PDF 印发。
- 命名规范：`03_X课程项目/notebooks/U{单元}-L{课时}_{关键名}.ipynb`，例：`U1-L1_K1连接与信息.ipynb`。
- 五阶段工作流（写入 `03_X课程项目/X课程开发计划-v3.md`）：
  - **P1** 实验代码（ipynb，python + 说明）
  - **P2** 大纲嵌入 + 确认①
  - **P3** 详细编写（= 实训手册 ipynb）→ 导出 PDF + 派生教学设计
  - **P4** PPT 内容大纲（每课页设计）+ 确认②
  - **P5** PPTX 开发（32 份）

---

## 2. Phase 1 实验代码设计约定

1. **禁用复杂程序结构**：不写 `try/except`、`assert`，不定义 `print_section` 之类辅助函数。课程面向初步程序能力者，目的是探索 BoosterOS SDK，代码越精炼、越直指学习目标越好。
2. **Phase 1 仅含实验代码**：课程导入类知识（具身智能发展、人形机器人发展等）**不是 Phase 1 内容**，在后续阶段（大纲嵌入 / 详细编写）补充。
3. **实验分三类**：
   - **运行类**：md 指示 → 运行提供的 python 单元格 → 观察结果、理解知识/能力。
   - **填空类**：md 给出任务/练习/问题 → 学生删除 python 代码中的下划线占位符、补全程序才能运行 → md 提示「删除下划线并补全」。
   - **自主编写类**：md 描述任务 + 提供空白 python cell → 学生自主编程。不要求每课都有，视整体内容设计而定。
4. **课头精简（必守）**：
   - 不写【单元】【课时】【实验类型】等标题框。
   - 不写「Phase 1 范围说明」之类 meta 注。
   - 实验类型**不**在每课开头描述，由未来统一汇总文档记录。
   - 步骤名称上**不**标注（运行类）等类型标签。

---

## 3. 内容与表述规则（面向学生文件）

1. **不写交互/日志型话术**：学生文件**不写**「我与你交互形成的决策叙述」，例如「本实验仅读取已开放的…`max_torque` 尚未开放不纳入」「字段说明：SDK 持续更新中…」等。只描述内容本身；设计理由、占位约束等记入内部开发计划/记忆，**不进学生文件**。
2. **不写课程设计前向引用 / 前因后果**：如「IMU、里程计等将在 U2 详细学习」这类设计逻辑**不给学生看**。保留学生向表述（如「机器人有自身状态」）。
3. **仅使用 SDK 已开放、有真实值的字段**：`None` / 占位字段一律不出现在实验代码、说明、或填空/自主编写题中。若某接口仅占位字段可用，则不在课程中使用该接口。
4. **真机实测字段可用性（K1，以真机为准）**：
   - `list_joints()` 每项：`limits`（min/max，单位 rad）**有数据→纳入**；`max_velocity`（rad/s）**有数据→纳入**；`max_torque`（恒 `None`）、`extra`（空）→ **不纳入**。
   - `robot_info`：`manufacturer` / `model` / `name` / `serial_number` / `firmware_version` 均打印（空字符串本身有教学意义）。
   - `get_joint_states()`：仅 `position`（rad）可用，本实验仅观察角度。
5. **涉及真机连接 / 运动的实验**，须加：
   - 「📌 前置准备」注：须先完成 K1 **开机、配网（连同一 WiFi）、查看 IP**，并能用 **BoosterStudio** 成功连接机器人。
   - 「⚠️ 安全提示」注：说明本实验是否涉及运动；涉及运动者，实验结束须切回安全模式（damping）。

---

## 4. cell 结构规则

1. **用户刻意的多 cell 拆分不可合并**：cell 的拆分方式本身是有意义的教学设计。重做 / 修改已存在的 notebook 时，**只改格内内容，不动 cell 边界**（含 cell 顺序）。
2. **新建 notebook** 应做合理拆分：一个步骤可用「多个 md cell + 多个 python cell」组合，便于讲解与观察。
3. **每课末尾新增「学习评价」markdown 单元**：
   - 含 **2~3 题**混合（判断 / 填空 / 选择），留空供学生作答。
   - 参考答案用 `> 参考答案（教师留存，勿印发给学生）` 引用块，置于同一 cell 内。
   - 格式示例见 `03_X课程项目/notebooks/U1-L1_K1连接与信息.ipynb` 末尾 cell。

---

## 5. BoosterOS SDK 技术约束

- **导入路径**：
  - `from boosteros.robots.booster import BoosterRobot` ✅
  - `from boosteros.brain import Detection` ✅
  - `from boosteros import BoosterRobot` ❌（顶层 `__init__` 为空）
- **真实可用的接口 / 字段**：
  - 连接：`BoosterRobot()`
  - 信息：`robot_info`（manufacturer/model/name/serial_number/firmware_version）、`list_joints()`（name/limits/max_velocity）、`list_actions()`（id/type/duration/interruptible）
  - 状态：`get_mode()`、`get_battery()`、`get_joint_states()`（仅 position）
  - 模式：`set_mode("damping" | "prepare" | "walk" | "custom")`（`get_mode()` 返回同名字符串；damping 优先级最高、prepare 为行走前置、walk 接收速度指令）
  - 运动：`set_velocity(vx, vy, vyaw)`、`set_head_angle(pitch, yaw)`（walk 模式下）、`set_gait("default" | "soccer")`、`do_action(action_id)`
  - 感知：`get_odom()` / `reset_odom()`（`pose_2d = [x, y, yaw]`）、`get_imu()`（`angular_velocity` / `linear_acceleration`；**航向用 `odom.pose_2d[2]`，不取可能 `None` 的 `imu.orientation`**）、`detect()`（bbox.center / bbox.area）
- **已弃用 / 不采用**：
  - `distance_m`：全包仅定义、零赋值，恒为 `None`。
  - 深度图方案（`get_image(img_type="depth")`）：坐标映射 / 单位换算 / 无效值过滤对高职学生过重，U4 不采用。
  - ArUco / OpenCV 二维码库：视觉定位由「检测框 + 里程计 + IMU」三传感融合完成，第三方库仅作可选扩展。

---

## 6. 交付进度

| 文件 | 单元·课时 | 状态 | 备注 |
|---|---|---|---|
| `03_X课程项目/notebooks/U1-L1_K1连接与信息.ipynb` | U1·L1 | ✅ 完成 | 20 cells（含「学习评价」） |
| `03_X课程项目/notebooks/U1-L2_运行模式与安全.ipynb` | U1·L2 | ✅ 完成 | 11 cells（含「学习评价」），模式切换 prepare→walk→damping |

---

## 7. 变更记录

- 2026-08-17 初建规则文件，汇总截至今日的全部 notebook 开发约束（工作流、Phase1 约定、表述规则、cell 结构、SDK 约束），并登记 U1-L1 交付状态。
