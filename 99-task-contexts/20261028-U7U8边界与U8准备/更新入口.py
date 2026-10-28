"""仅更新本次U7/U8排查入口；分别生成工作区与HEAD增量，隔离既有改动。"""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
BASE = json.loads((TASK / "基线.json").read_text(encoding="utf-8"))
COURSE = "05-internal-materials/vocational-planning/03_X课程项目/"


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("精确匹配数量不为1：" + old[:120])
    return text.replace(old, new, 1)


def under_title(text, title, block):
    return once(text, title + "\n\n", title + "\n\n" + block + "\n\n")


def transform(rel, text):
    if rel == "AGENTS.md":
        return under_title(text, "# AGENTS.md — 面向 AI Agent 的知识库使用指南 + 内容总览",
            "> **U8开发准备（2026-10-28）**：已排查最新U7-L4与U8的内容边界。U7固定三幕与迎宾主题明显重叠，建议U8通过需求、模块接口、彩排复测及答辩证据区分；U7 Notebook未改。U8四课开发准备完成，P1学生稿尚未产出；视觉踢球需先补教师预验证模块。入口：`" + COURSE + "U8-P1开发准备.md`及`" + COURSE + "实验验证/U7-L4与U8_内容边界排查.md`。")
    if rel == "INDEX.md":
        return under_title(text, "# 全局关键词索引",
            "> U7/U8内容重叠 / U8-P1准备 / 模块接口与验收 / 视觉踢球前置：[边界排查](" + COURSE + "实验验证/U7-L4与U8_内容边界排查.md)、[四课开发准备](" + COURSE + "U8-P1开发准备.md)（2026-10-28；准备完成，U8学生稿尚未产出；U7 Notebook未改）。")
    if rel == "CHANGELOG.md":
        return under_title(text, "# 更新日志",
            "## 2026-10-28 · U7/U8内容边界与U8-P1开发准备\n\n"
            "- 排查最新U7-L4的29格及现行U8大纲：固定迎宾三幕行为明显重叠，但未覆盖小组需求、接口协作、彩排复测和答辩交付；建议保留U7示例，以这些任务区分U8。\n"
            "- 形成U8四课目标、45分钟活动、接口与测试表、评价证据、素材与确认清单；指出自动踢球缺少专用API和米制球坐标前置，建议教师预验证后开放。\n"
            "- 统一现行计划中U8-L1/L4的交付要求为完整Markdown活动学材，修正“仅骨架”旧文字；历史排期保留。同步逐课进度与导航。\n"
            "- U7 Notebook和现行大纲未改，未运行机器人；U8仅完成开发准备，四课P1学生稿未产出。Git仅本地记录，推送由用户手动进行。")
    if rel == "05-internal-materials/vocational-planning/README.md":
        title = text.splitlines()[0]
        return under_title(text, title,
            "> **U8开发准备（2026-10-28）**：[U7-L4与U8边界排查](03_X课程项目/实验验证/U7-L4与U8_内容边界排查.md)、[U8四课P1开发准备](03_X课程项目/U8-P1开发准备.md)已完成；以需求、接口、彩排复测和答辩区分综合项目。U7原稿保留；U8学生稿尚未产出，视觉踢球列教师预验证条件。")
    if rel == COURSE + "X课程开发计划-v4.md":
        text = under_title(text, "# X 课程开发计划（v4）",
            "> **U8开发准备（2026-10-28）**：[开发准备](U8-P1开发准备.md)及[U7/U8内容边界](实验验证/U7-L4与U8_内容边界排查.md)已完成；四课P1学生稿尚未产出。本轮统一现行U8-L1/L4要求为完整Markdown活动学材，历史排期保留；主题与评价范围调整详见准备稿建议，未擅改大纲。")
        for old, new in [
            ("2 实验 notebook（L2/L3）+ 2 骨架（L1/L4）", "4 notebook（L1/L4为完整Markdown活动学材）"),
            ("U8 的 L1/L4 为纯教学环节，notebook 仅留 markdown 骨架。", "U8 的 L1/L4 以非代码活动为主，Notebook需包含完整任务、示例、记录、检查与评价；L2/L3提供实验代码与说明。"),
            ("—（教学环节，无实验 cell，仅 markdown 骨架）", "—（完整Markdown活动学材：选题、需求、接口、分工、检查与评价）"),
            ("—（展演/答辩环节，无实验 cell，仅 markdown 骨架）", "—（完整Markdown活动学材：展演、答辩、评分、记录与反思）"),
        ]:
            text = once(text, old, new)
        return text
    if rel == COURSE + "X课程当前进度.md":
        text = under_title(text, "# X课程当前进度",
            "> **U8准备更新（2026-10-28）**：[内容边界排查](实验验证/U7-L4与U8_内容边界排查.md)和[四课P1开发准备](U8-P1开发准备.md)已完成；学生Notebook尚未产出，未登记P1或确认①②完成。U7现稿及现行大纲保留。")
        text = once(text, "| 仅有计划，未找到P1产物 | 4 | U8四课 |", "| P1开发准备已完成，学生稿尚未产出 | 4 | U8四课 |")
        names = ["选题与任务拆解", "核心模块开发（分组并行）", "真机彩排与联调", "成果展演与答辩"]
        notes = ["完整Markdown学材，含委托、需求、接口、分工与评价", "局部模块支架与本组整合流程；主题B有前置缺口", "彩排、修改复测及版本交付；需明确跨课程序载体", "完整Markdown学材，含展演、答辩与评分；需按组数组织"]
        for i, (name, note) in enumerate(zip(names, notes), 1):
            prefix = f"| U8-L{i} {name} |"
            rows = [line for line in text.splitlines() if line.startswith(prefix)]
            if len(rows) != 1:
                raise ValueError("U8逐课状态行不唯一")
            text = once(text, rows[0], prefix + " 开发准备完成；P1学生稿尚未产出 | 未登记任何完成确认 | 按[开发准备](U8-P1开发准备.md)编写P1 | " + note + " |")
        text = once(text, "| U8当前产物 | 0 | 计划列出四课，但本次未找到对应Notebook、教学设计或课件文件 |", "| U8学生Notebook／教师稿／课件 | 0 | 已完成边界排查与开发准备；四课学生材料仍未产出 |")
        text = once(text, "8. **U8计划文字与产物分开**：计划写“Markdown骨架”是交付要求；本次没有找到对应文件，不登记为已完成骨架。", "8. **U8开发准备与学生稿分开**：边界排查和四课准备已完成；现行计划的“仅骨架”旧要求已统一为完整Markdown活动学材。四课Notebook仍未产出，不登记P1或确认通过。")
        text = once(text, "4. 审阅U7本轮修订并完成逐格真机①②，再进入P2；U8可同时整理主题与作品评价要求。", "4. 审阅U7本轮修订并完成逐格真机①②，再进入P2；U8可按开发准备编写P1，所引用模块须据相应真机结果核对，视觉踢球先补前置。")
        text += "\n- [U7-L4与U8内容边界](实验验证/U7-L4与U8_内容边界排查.md)、[U8-P1开发准备](U8-P1开发准备.md)：准备完成，四课学生稿未产出。\n"
        return text
    raise ValueError(rel)


def decode(data):
    return data.decode("utf-8").replace("\r\n", "\n")


pending = []
for rel, expected in BASE["files"].items():
    current = (ROOT / rel).read_bytes()
    if hashlib.sha256(current).hexdigest() != expected:
        raise RuntimeError("共享文件在基线后发生变化，停止：" + rel)
    head = subprocess.check_output(["git", "show", "HEAD:" + rel], cwd=ROOT)
    work_out = transform(rel, decode(current))
    head_out = transform(rel, decode(head))
    if work_out == decode(current) or head_out == decode(head):
        raise RuntimeError("缺少预期增量：" + rel)
    pending.append((rel, current, work_out, head_out))

for rel, current, work_out, head_out in pending:
    newline = "\r\n" if b"\r\n" in current else "\n"
    (ROOT / rel).write_bytes(work_out.replace("\n", newline).encode("utf-8"))
    staged = TASK / "head-increment" / rel
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text(head_out, encoding="utf-8", newline="\n")
print("已精确更新6份入口；生成仅含本次增量的HEAD版本，未暂存其他任务修改。")
