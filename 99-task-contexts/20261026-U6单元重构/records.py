"""同步本次U6重构的现行分工、产品说明及导航；保留前序工作区改动。"""
from pathlib import Path
import ast
import difflib
import json
import re
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = '05-internal-materials/vocational-planning/03_X课程项目'
RULE = '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md'
REPORT = 'U6_单元重构与动作编排核验.md'


def replace_line(text, prefix, new):
    lines = text.splitlines(keepends=True)
    matches = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    assert len(matches) == 1, (prefix, matches)
    lines[matches[0]] = new.rstrip() + '\n'
    return ''.join(lines)


def add_note(text, note):
    heading = re.search(r'^# [^\n]+\n', text, re.MULTILINE).group(0)
    assert note not in text
    return text.replace(heading, heading + '\n' + note + '\n', 1)


def transform(rel, text):
    if rel == PROJ + '/X课程大纲-v4.md':
        text = replace_line(text, '> 4. **U6 扩展', '> 4. **U6保留4课时「动作示教与模仿学习」**：L1概述，L2录制与回放，L3通过动作工坊开展视频动作训练，L4混合素材编排（2026-10-26重构）。')
        text = replace_line(text, '> 数采课程当前挂起', '> 数采课程当前挂起。**U6动作示教与模仿学习**结合轨迹录制与回放、动作工坊训练实践和动作编排。学生通过Studio使用视频提取、重定向与Booster Train强化学习训练流程，不要求编写训练算法；`.btraj`直接回放与训练策略分别说明。动作工坊新SDK入口测试中，用户确认后接入作品。')
        text = replace_line(text, '| U6     |', '| U6 | 动作示教与模仿学习 | 4 | 12.5% | 两版轨迹 + 视频训练任务 + 混合动作作品 | 示教/回放/骨架提取/重定向/参考动作训练/编排 | 后16·交互 |')
        text = replace_line(text, '> **定位**：L1 为知识引入', '> **定位**：L1为知识引入与方向概述，保留轨迹读取练习；L2完成示教录制、保存读回、实际回放与改录比较；L3通过动作工坊创建视频动作训练任务，承接L1的Booster Train参考动作跟踪；L4围绕具体场景整合素材、顺序编排、试演与改进。直接回放轨迹不等于训练新策略。')
        start = text.index('### U6：')
        end = text.index('### U7：', start)
        u6 = text[start:end]
        u6 = replace_line(u6, '| **2** |', '| **2** | 动作录制与回放 | 示教采集关节时序；录制停顿、节奏与首尾姿态对回放的影响；文件核对与执行效果的区别 | `with hand_guiding_manager`内录制并停止→退出上下文→保存→读回核对→`execute_trajectory()`；改录第二版比较 | **示教/遥操作(B13)**；**轨迹(B14)**；**回放/重演(B15)** | — | ② 两版轨迹及本课回放观察，说明一项调整及效果 |')
        u6 = replace_line(u6, '| **3** |', '| **3** | 视频动作训练（动作工坊） | 视频骨架提取→imretarget重定向→Booster Train强化学习训练；参考动作与策略、训练结束与效果的区别 | 拍摄检查MP4/MOV→创建K1训练任务→记录可见阶段→对照原片与结果→提出第二版方案；未当堂完成时用教师样例并补查本组结果 | **模仿学习(B02)**与**强化学习(B18)**：参考动作模仿目标与强化学习训练结合；**数据驱动 vs 规则驱动(B07)**复用 | 骨架动作、重定向：结合输入输出引入 | ③ 视频、任务记录、结果对照与有证据的调整方案 |')
        u6 = replace_line(u6, '| **4** |', '| **4** | 动作编排 | 不同来源的动作承担场景表达；任务顺序与物理姿态衔接分别检查 | 3～5步作品脚本；预检全部素材；`execute_trajectory()`与`do_action()`混合顺序执行、等待成功、记录异常及复测；工坊作品按确认接口接入 | **行为编排(B17)**；**预定义动作(B16)**复用U1，不重复设一课 | 状态机与行为树(B06)仅作组织方式拓展，不要求实现 | ④ 至少录制轨迹与内置动作两类素材的作品、日志、修改说明；第三类按可用条件加入 |')
        u6 = replace_line(u6, '**单元产出**', '**单元产出**：两版`.btraj`及回放比较 + 动作工坊输入视频、训练任务与结果对照 + 混合素材作品脚本、日志与修改说明。演示视频按课堂条件安排；训练未结束或接口未接入的项目标明待补，不作已完成成果。')
        text = text[:start] + u6 + text[end:]
        text = replace_line(text, '4. **U6 训练环节**', '4. **U6训练环节**：L3通过Studio使用动作工坊，理解骨架提取、重定向与Booster Train强化学习训练。教师准备已完成样例应对后台训练跨课时；不要求学生编写算法，也不假定`.btraj`能直接输入训练工程。L4的工坊SDK接入待用户确认。')
        return add_note(text, '> **U6重构（2026-10-26）**：现行分工见本文件U6表；实施节奏与验证项见[单元重构记录](实验验证/' + REPORT + ')。新稿待确认①与受影响内容确认②。')
    if rel == PROJ + '/X课程开发计划-v4.md':
        text = replace_line(text, '| U6 | L2 |', '| U6 | L2 | 动作录制与回放 | 录制→保存→读回→本课回放→改录比较；4代码格（2026-10-26 P1重构稿，待①②） | `U6-L2_动作录制与回放` |')
        text = replace_line(text, '| U6 | L3 |', '| U6 | L3 | 视频动作训练（动作工坊） | 视频检查、创建任务、骨架提取/重定向/Booster Train训练、结果对照与调整；Studio实训，教师样例保障课内分析（P1重构稿，待①及平台验证②） | `U6-L3_视频动作训练` |')
        text = replace_line(text, '| U6 | L4 |', '| U6 | L4 | 动作编排 | 场景设计、全部素材预检、轨迹与内置动作顺序混编、任务结果与姿态衔接复核；工坊SDK待用户确认（P1重构稿，待①②） | `U6-L4_动作编排` |')
        return add_note(text, '> **U6进度（2026-10-26）**：L2～L4按用户要求重构并同步生成器；L1精修稿未改。L2/L3文件已改名，现行课名以本文件逐课清单为准；新稿待①②，未登记P2或后续阶段通过。[重构与核验清单](实验验证/' + REPORT + ')。')
    if rel == RULE:
        text = text.replace('U6-L3 是复用＋扩展，不是首次', 'U6-L4混合编排时复用；U6-L3已于2026-10-26改为视频动作训练')
        specs = [
            ('L2', '动作录制', '动作录制与回放', '16格（12 md/4 code）', '录制、保存、读回、本课回放与两版比较；示教/轨迹/回放B13～B15；需验证示教范围、退出上下文、字段核对、回放与终态处理。'),
            ('L3', '动作回放', '视频动作训练', '16格（16 md/0 code）', 'Studio视频训练实训：视频检查、骨架提取、imretarget重定向、Booster Train强化学习训练、结果对照与修改；B02/B18/B07复用。教师样例应对训练跨课时，平台可见阶段与部署条件待验证；新SDK未写入代码。'),
            ('L4', '动作编排', '动作编排', '18格（14 md/4 code）', '3～5步场景作品，至少录制轨迹与内置动作两类；全部素材预检、成功后继续、忙/失败/超时不发后续动作，日志与现场观察分开。工坊第三类SDK待用户确认；B17、B16复用，B06仅拓展。'),
        ]
        for number, (key, old, new, count, detail) in enumerate(specs, 22):
            text = replace_line(text, f'| `03_X课程项目/notebooks/U6-{key}_{old}.ipynb`', f'| `03_X课程项目/notebooks/U6-{key}_{new}.ipynb` | U6·{key} | 🟡 **P1重构修订稿（2026-10-26），待确认①及受影响内容确认②** | **{count}**；生成器`_gen_L{number}.py`反向同步。{detail}实体按钮切模式，遵循§8.29。 |')
        return add_note(text, '> **U6本轮重构（2026-10-26）**：L2合并录制与回放，L3改视频动作训练，L4改混合素材作品实践。当前分工以进度表新行及[重构记录](../03_X课程项目/实验验证/' + REPORT + ')为准，后文早期日志保留历史原义。L1未改，①②未登记通过。')
    if rel in [PROJ + '/_diffcheck_u2.py', PROJ + '/_regen_from_nb.py']:
        text = text.replace('U6-L2_动作录制.ipynb', 'U6-L2_动作录制与回放.ipynb').replace('U6-L3_动作回放.ipynb', 'U6-L3_视频动作训练.ipynb')
        if rel.endswith('_regen_from_nb.py'):
            for num, key, title in [(22, 'L2', '动作录制与回放'), (23, 'L3', '视频动作训练'), (24, 'L4', '动作编排')]:
                desc = {
                    22: '录制→保存→读回核对→退出示教后的回放→第二版比较；4代码格。',
                    23: 'Studio拍摄与检查、创建训练任务、三阶段输入输出、结果对照；16格Markdown，无测试SDK调用。',
                    24: '3～5步作品；预检全部素材；轨迹与内置动作按成功状态顺序混编，日志与现场观察；4代码格。',
                }[num]
                content = f'U6-{key} {title} —— 2026-10-26重构，Notebook为单一源。\n  {desc}\n  P1修订稿，待①②；模式操作使用Markdown；动作工坊SDK由用户确认后接入。'
                pattern = rf"('_gen_L{num}\.py': )\"\"\".*?\"\"\""
                text, n = re.subn(pattern, lambda m: m[1] + '"""' + content + '"""', text, count=1, flags=re.S)
                assert n == 1
        return text
    if rel == 'AGENTS.md':
        text = replace_line(text, '  - U6 四课 P1 已完成', '  - U6-L2～L4已于2026-10-26重构为「动作录制与回放／视频动作训练（动作工坊）／动作编排」，L1精修稿未改。L2本课回放并改录比较，L3通过Studio使用骨架提取→imretarget→Booster Train强化学习训练流程，L4混编已验证轨迹与内置动作；工坊新SDK待用户确认。新稿待确认①和受影响内容确认②，未登记后续通过。实施与核验入口：`03_X课程项目/实验验证/' + REPORT + '`。')
        return text
    if rel == 'INDEX.md':
        return add_note(text, '> U6动作录制与回放 / 视频动作训练 / imretarget / 动作工坊与Booster Train / 混合动作编排：[重构与SDK核验](05-internal-materials/vocational-planning/03_X课程项目/实验验证/' + REPORT + ')（2026-10-26；L2本课回放、L3训练实践、L4综合作品；工坊SDK待确认）。')
    if rel == '05-internal-materials/vocational-planning/README.md':
        text = text.replace('U6 四课 P1 已完成，待确认①；U6-L1 已于 2026-10-20 按高职学生前置基础修订知识讲解、三种方式的关系与动作数据流程，代码尚待真机验证。', 'U6-L1保留精修稿；2026-10-26已重构L2录制与回放、L3视频动作训练、L4混合素材编排，生成器与现行大纲同步；新稿待①及受影响内容②。工坊SDK入口待用户确认，未登记P2通过。')
        return add_note(text, '> **U6重构（2026-10-26）**：[单元分工、45分钟实施建议与核验清单](03_X课程项目/实验验证/' + REPORT + ')已形成；新L2/L3见`03_X课程项目/notebooks/`，旧稿移到任务归档。')
    if rel == '01-booster-kb/07-tech-platform/_index.md':
        return replace_line(text, '| [motion-creator.md]', '| [motion-creator.md](motion-creator.md) | **Motion Creator动作工坊** — 视频骨架提取→imretarget重定向→Booster Train强化学习训练（2026-10-26用户更新）；Studio实践已纳入X课程U6-L3，导出与新SDK入口测试中 |')
    if rel == '01-booster-kb/07-tech-platform/motion-creator.md':
        text = text.replace('updated: 2026-10-16', 'updated: 2026-10-26')
        text = replace_line(text, 'source:', next(line for line in text.splitlines() if line.startswith('source:')) + ' + 用户最新功能与实现说明（2026-10-26）')
        text = replace_line(text, '> **定位**:', '> **定位**：Motion Creator（动作工坊）是Booster Studio中的动作创作工具。当前视频路线经过人体骨架提取、imretarget重定向和Booster Train强化学习训练，产出动作策略，可按产品提供的方式部署到匹配机型；不能将最终产物笼统写成普通可回放轨迹。')
        text = text.replace('真人动作视频 → AI 动作提取 → 机器人动作生成 → 虚拟/真机部署', '真人视频 → 人体骨架动作 → imretarget重定向参考动作 → Booster Train强化学习训练 → 动作策略 → 经确认的部署运行')
        text = text.replace('- **AI 动作提取**：自动从视频中提取人体关键点并映射到机器人关节', '- **骨架提取与重定向**：先估计人体运动，再适配目标机器人结构；参考动作与可运行策略分别形成。\n- **训练结束条件**：最大训练时长或训练终止标准满足任一即结束（用户2026-10-26说明）；数值由平台配置，训练结束不能直接说明效果合格。')
        text = replace_line(text, '按使用量消耗**加速豆**', '按使用量消耗**加速豆**，详见[产品生态体系](product-ecosystem.md#六加速豆体系)。PRD约定创建时按预计消耗扣除；提取/重定向失败返还，中途手动删除不返还；训练阶段失败是否返还仍有评审遗留口径，以当前规则为准。')
        text = text.replace('两种创建方式（新建时需', '用户2026-10-26确认当前可用的是命名并上传MP4/MOV创建训练。以下两种方式来自PRD，BVH入口是否已上线仍以版本为准（新建时需')
        anchor = '\n---\n\n## 二、与 BeyondMimic 的关系'
        addition = '''\n### 当前视频要求（用户2026-10-26补充）

- MP4/MOV，不低于720P、30帧/秒；单人全身清楚出镜。
- 避免肢体交叉遮挡和物体遮挡；保持身体稳定。
- 不设计跳跃、踮脚、单腿支撑，避免大幅弯腰、后仰及快速动作。

动作详情是否展示各阶段中间结果，以当前界面为准；PRD完成页展示的可能是策略运行录制，不能将观看预览记为一次部署运行。
'''
        text = text.replace(anchor, addition + anchor, 1)
        start = text.index('## 二、与 BeyondMimic 的关系')
        end = text.index('\n---\n\n## 三、', start)
        text = text[:start] + '''## 二、与Booster Train及轨迹回放的关系

动作工坊将视频输入到提取、重定向和训练流程。按用户当前实现说明，训练部分使用Booster Train；参考动作规定模仿目标，强化学习负责优化策略。学生可通过产品使用训练流程，不需要先安装训练工程或编写算法。

| 对象 | 数据或产物 | 执行方式与区别 |
| --- | --- | --- |
| 示教录制 | `.btraj`，含关节随时间变化的记录 | 正式SDK用`execute_trajectory()`回放；这一步不训练新策略 |
| 动作工坊重定向结果 | 适配目标机型的参考动作 | 用于后续训练；不能与最终策略混称 |
| 动作工坊训练结果 | 动作策略，部署资源设计包含策略、轨迹及参数 | 按产品部署方式验证；新导出/SDK方案仍测试中，不能当作`.btraj`调用 |

BeyondMimic相关研究路线与Booster Train工程介绍见[Booster Train](booster-train.md)。不能仅凭动作名称、视频外观或SDK入口，判定所有动作的训练算法与内部结构相同。
''' + text[end:]
        text = text.replace('| **动作数据集制作** | 批量生成训练数据（为 BeyondMimic 提供 NPZ） |', '| **动作过程分析** | 对照原视频、可见中间结果与策略表现，记录差异；是否支持导出以产品为准 |')
        text = text.replace('| **高职动捕课程** | 动捕→重定向→部署的完整链路教学 |', '| **高职动作实践** | 骨架提取→重定向→训练→结果分析，按条件部署；X课程U6-L3采用该路线 |')
        text = text.replace('- **动作导出（P0 新增）**：支持将训练完成的动作策略包**导出**，通过 SDK 直接调用播放（打通"训练 → 导出 → SDK 调用"全链路）', '- **动作导出及SDK调用**：全身控制资源接口方案测试中，资源导出也需按实际版本确认；见下方测试技术方案。不能将该方案写成正式SDK已发布能力。')
        return text
    if rel == 'CHANGELOG.md':
        return add_note(text, '''## 2026-10-26 · U6单元重构与混合动作SDK核验

- L2合并录制与回放，加入v1/v2改录比较；L3改为Studio动作工坊的视频动作训练；L4改为3～5步混合素材作品实践。共50格、8代码格，三份生成器反向同步；L2/L3改名，旧稿移至任务归档，L1精修稿未改。
- 核对正式SDK：录制轨迹与内置动作可分别调用execute_trajectory/do_action按任务成功结果顺序组合；物理姿态衔接仍需真机。动作工坊新资源接口测试中，由用户确认后接入，不写入学生执行代码。
- 同步大纲、计划、规则进度表、文件名引用和入口；修正技术平台动作工坊文档中“仅产轨迹”的旧说明，区分用户最新实现、PRD及测试接口。
- 增加教师实施建议、教学与平台/真机清单；静态和模拟核验不代替①②。仅本地提交，推送由用户完成。''')
    raise KeyError(rel)


def main():
    manifest = json.loads((TASK / '重构清单.json').read_text(encoding='utf-8'))
    patch, index_patch, skipped = [], [], []
    for rel in manifest['shared']:
        before = (TASK / 'before' / rel).read_text(encoding='utf-8')
        path = ROOT / rel
        assert path.read_text(encoding='utf-8') == before, '输入已变化：' + rel
        after = transform(rel, before)
        path.write_text(after, encoding='utf-8', newline='\n')
        patch.extend(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), fromfile='a/' + rel, tofile='b/' + rel))
        # 将同一转换施于HEAD，避免整文件暂存前序任务的未提交修改。
        proc = subprocess.run(['git', 'show', 'HEAD:' + rel], cwd=ROOT, capture_output=True)
        if proc.returncode:
            skipped.append({'path': rel, 'reason': 'HEAD尚无此文件；本轮增量保存在工作区补丁'})
            continue
        base = proc.stdout.decode('utf-8').replace('\r\n', '\n')
        try:
            target = transform(rel, base)
        except (AssertionError, StopIteration, ValueError) as exc:
            skipped.append({'path': rel, 'reason': 'HEAD缺少所需现行上下文；本轮增量保存在工作区补丁', 'detail': str(exc)})
            continue
        index_patch.extend(difflib.unified_diff(base.splitlines(keepends=True), target.splitlines(keepends=True), fromfile='a/' + rel, tofile='b/' + rel))
    for name in ['_regen_from_nb.py', '_diffcheck_u2.py']:
        ast.parse((ROOT / PROJ / name).read_text(encoding='utf-8'))
    (TASK / '工作区联动增量.patch').write_text(''.join(patch), encoding='utf-8', newline='\n')
    (TASK / '联动暂存增量.patch').write_text(''.join(index_patch), encoding='utf-8', newline='\n')
    (TASK / '联动暂存限制.json').write_text(json.dumps(skipped, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'updated': len(manifest['shared']), 'index_context_missing': skipped}, ensure_ascii=False))


if __name__ == '__main__':
    main()
