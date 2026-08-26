# -*- coding: utf-8 -*-
import json, io

P = r"d:\A_Project\BoosterRobotics\知识库\05-internal-materials\vocational-planning\03_X课程项目\notebooks\U1-L2_运行模式与安全.ipynb"

with io.open(P, encoding="utf-8") as f:
    nb = json.load(f)

def md(lines):
    # lines: list of str, each WITHOUT trailing newline; return source list with \n per §8.5
    return [l + "\n" for l in lines]

def make_md_cell(lines, cid):
    return {
        "cell_type": "markdown",
        "id": cid,
        "metadata": {},
        "source": md(lines),
    }

cells = nb["cells"]

# ---- 1) 插入「2.3 观察与记录」(情景1：纯文字记录) 在 get_mode 代码 cell 之后 ----
obs_lines = [
    "### 2.3 观察与记录：不同模式下的机器人状态（非代码）",
    "",
    "不运行代码，直接观察 K1 当前所处模式下的**实际姿态与状态**，把观察结果填入下表（可结合 2.2 读到的模式值对照填写）。",
    "",
    "| 运行模式 | 机器人姿态描述 | 能否运动 | 你的观察 / 备注 |",
    "|---|---|---|---|",
    "| `damping` | （例：趴着 / 坐着时是“软”的，关节有阻尼但不支撑站立） | 否 |  |",
    "| `prepare` | （例：站立就绪，但原地不动） | 否（仅就绪） |  |",
    "| `walk` | （例：站立且可响应速度指令） | 是 |  |",
    "",
    "> \U0001F4DD 这是一项“观察 + 记录”的**非代码活动**：用 md 表格把你的观察固定下来，比只看不记更能形成记忆。",
]
obs_cell = make_md_cell(obs_lines, "cell-obs-2-3")

# 找 get_mode 代码 cell
idx_get = None
for i, c in enumerate(cells):
    if c["cell_type"] == "code" and "get_mode" in "".join(c["source"]):
        idx_get = i
        break
assert idx_get is not None, "get_mode cell not found"
cells.insert(idx_get + 1, obs_cell)
print("inserted 2.3 obs after code cell index", idx_get)

# ---- 2) 插入「五、拓展活动：手柄手动操控」(情景2：配图→附件提示) 在 检查点 之前，并把原 五/六 顺延为 六/七 ----
gp_lines = [
    "## 五、拓展活动：用手柄手动操控 K1（非代码操作）",
    "",
    "除了用程序（SDK）控制，K1 也支持用**手柄（gamepad）直接手动遥控**——这是“人直接操作”的另一种方式，能帮你直观感受机器人姿态与动态平衡。",
    "",
    "**操作目标**：在教师指导下，用手柄让 K1 完成“就绪 → 原地小幅移动 → 停止回稳”的简单动作，体会手动控制与程序控制的差别。",
    "",
    "**前置条件**：",
    "- K1 已开机、配网，BoosterStudio 已成功连接（见前面实验环节）；",
    "- 手柄已与 K1 / 控制端完成配对；",
    "- 场地空旷、周围无人员紧贴，教师监督下进行。",
    "",
    "**关键步骤（概括）**：",
    "1. 在 BoosterStudio / 控制界面切到“手柄控制”模式；",
    "2. 先让 K1 进入 `prepare` 并直立站稳，再切到 `walk` 方可移动；",
    "3. 用左摇杆控制移动、右摇杆控制转向 / 姿态（具体按键映射以附件为准）；",
    "4. 停止时回到 `prepare` 稳定，再收尾到 `damping`，**严禁 walk → damping 直接切换**。",
    "",
    "> \u26A0\uFE0F **安全要点**：手动遥控同样遵守本课的安全顺序；随时准备急停，不要在 `walk` 中突然切 `damping`。",
    "",
    "\u3010附件提示：手柄按键布局、配对方式与 BoosterStudio 手柄控制界面的逐步操作图示较多，详见附件《K1 手柄遥控操作图示》，请结合图文完成学习。\u3011",
]
gp_cell = make_md_cell(gp_lines, "cell-gp-5")

# 找 检查点 cell（原 五）与 扩展阅读 cell（原 六）
idx_check = None
idx_ext = None
for i, c in enumerate(cells):
    src = "".join(c["source"])
    if src.startswith("## 五、检查点"):
        idx_check = i
    if src.startswith("## 六、扩展阅读"):
        idx_ext = i
assert idx_check is not None and idx_ext is not None, "check/ext header not found"

# 插入手柄活动到 检查点 之前
cells.insert(idx_check, gp_cell)
print("inserted gamepad section before check header (index", idx_check, ")")

# 顺延标题：原 五->六，原 六->七
def set_first_line(cell, new_first):
    src = cell["source"]
    # source is list of lines each with \n
    rest = src[1:]
    cell["source"] = [new_first + "\n"] + rest

for c in cells:
    src = "".join(c["source"])
    if src.startswith("## 五、检查点"):
        set_first_line(c, "## 六、检查点、思考题与学习评价")
        print("renumbered 五->六 (检查点)")
        break
for c in cells:
    src = "".join(c["source"])
    if src.startswith("## 六、扩展阅读"):
        set_first_line(c, "## 七、扩展阅读：安全操作与职业素养")
        print("renumbered 六->七 (扩展阅读)")
        break

# ---- 3) 在 课程大纲映射 的 轻任务↔cell 对应表 追加非代码活动行 ----
for c in cells:
    if c["cell_type"] == "markdown" and "轻任务 ↔ 代码 cell 对应表" in "".join(c["source"]):
        src = c["source"]
        # 找到表格最后一行（含 行走安全路径）后插入新行
        for i, line in enumerate(src):
            if "行走安全路径" in line:
                new_row = "| ② 手柄手动操控（非代码） | 五 | 附件《K1 手柄遥控操作图示》 | 附件 |\n"
                src.insert(i + 1, new_row)
                print("appended gamepad row to mapping table")
                break
        c["source"] = src
        break

nb["cells"] = cells

with io.open(P, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("OK cells now:", len(cells))
