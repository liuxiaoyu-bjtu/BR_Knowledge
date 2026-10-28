from pathlib import Path
import difflib
import json

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
CP = '05-internal-materials/vocational-planning/03_X课程项目/'
RP = '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md'
REPORT = 'U5-L4_U6_P3教学设计覆盖检查记录.md'
NAMES = {'U5-L4': '语音会话管理', 'U6-L1': '动作的来源', 'U6-L2': '动作录制与回放',
         'U6-L3': '视频动作训练', 'U6-L4': '动作编排'}
NOTE = '2026-10-28：用户确认U5-L4 P2复核通过，U6四课P1/P2评审及确认①②通过；五课P3教学设计已产出，待用户确认④。U6-L4按用户真机结论保留等待后取消，以现场动作表现和取消终态共同判断；不把CANCELLED解释为动作完整完成。'

def after_heading(text, block):
    first, rest = text.split('\n', 1)
    return first + '\n\n' + block.strip() + '\n' + rest

def replace_line(text, prefix, new):
    return '\n'.join(new if line.startswith(prefix) else line for line in text.split('\n'))

def update(rel, text):
    if rel == 'AGENTS.md':
        text = text.replace('U5-L4在P2，11课P1待审/验证', 'U5-L4与U6四课P3待确认④，7课P1待审/验证')
        text = after_heading(text, '> **五课P3（2026-10-28）**：' + NOTE + '\n> 入口：`' + CP + '实验验证/' + REPORT + '`。')
        text = replace_line(text, '  - U5-L4《语音会话管理》',
            '  - U5-L4《语音会话管理》用户本轮确认P2复核通过，登记③并按授权完成P3教学设计，待确认④；未新增逐格真机输出。Notebook原字节保留，生成器反向同步。入口：`实验验证/' + REPORT + '`。')
        text = replace_line(text, '  - U6-L2～L4已于2026-10-26重构',
            '  - U6四课P1/P2评审及确认①②已由用户通过；四份P3教学设计已产出，待确认④。L3现稿含execute_whole_body_control资源示例；导出附件尚待提供。L4基础脚本实际支持轨迹与内置动作，工坊资源混编另需接入。按用户实测保留等待后取消，相关文字与评价已同步，句柄初始化移回首次连接格；这处保护修正仅作离线核查，不冒称新增真机测试。')
    elif rel == 'INDEX.md':
        text = text.replace('（2026-10-26；L2本课回放、L3训练实践、L4综合作品；工坊SDK待确认）', '（2026-10-28更新；四课P2通过，P3待④；L3现有资源调用示例，L4基础混编尚未接入工坊资源）')
        anchor = '| X 课程实验代码 |'
        rows = []
        for line in text.split('\n'):
            rows.append(line)
            if line.startswith(anchor):
                rows.append('| X课程 U5-L4 / U6 P3 / 教学设计 / 确认④ / 全格覆盖 | [五课教学设计及覆盖检查](' + CP + '实验验证/' + REPORT + ')（五份45分钟教师稿；P2通过、P3待④；含取消终态与现场表现、训练等待、附件及补做安排） |')
        text = '\n'.join(rows)
        text = text.replace('现稿27格，确认①通过、P2复核中，整课②待齐', '现稿27格；用户确认P2复核通过，P3教学设计待④')
        text = text.replace('2026-10-26①通过；文稿复核完成，整课②依据待齐，③暂不登记', '2026-10-26①通过；2026-10-28用户确认P2复核通过，③登记，P3待④')
    elif rel == 'CHANGELOG.md':
        marker = '# 更新日志\n'
        entry = '''\n## 2026-10-28 · U5-L4与U6四课P3教学设计

- 按用户确认登记U5-L4 P2复核通过、U6四课P1/P2评审及①②通过；五课教师用教学设计完成，待确认④，未进入P4。
- 五课各45分钟，覆盖当前96格Notebook及20格代码、目标、观察、思考与学习评价；保留目标下教学提示、按需FAQ及P5-B投影回填安排。训练未完成、设备轮换与条件部署另有实施安排。
- U6-L4按用户真机反馈保留等待后取消的调用，文字、评价与教师稿统一区分取消终态和实际动作效果；将active_motion初始化从试演格移回首次连接格，防止旧任务检查失效。U6-L2仅修正保存提示文件名与收尾标点。五课生成器以当前Notebook反向同步，未运行旧生成器或机器人。
- 更新逐课总表、计划、规则与导航；未找到《动作工坊训练策略模型导出》独立附件，列入部署准备项。总表教学设计覆盖由16课增至21课；PPT产物范围不变。Git仅本地提交，由用户推送。
\n'''
        assert marker in text
        text = text.replace(marker, marker + entry, 1)
    elif rel.endswith('vocational-planning/README.md'):
        text = text.replace('16课已有教学设计/PPT大纲/课件产物', '21课已有教学设计，16课已有PPT大纲/课件产物')
        text = after_heading(text, '> **五课P3（2026-10-28）**：' + NOTE + '\n> [五份教学设计与覆盖检查](03_X课程项目/实验验证/' + REPORT + ')；《动作工坊训练策略模型导出》附件待准备，工坊资源尚未接入L4基础混编。以下较早日期记录保留历史原义。')
        text = text.replace('> **U6-L4更新（2026-10-27）**', '> **U6-L4历史更新（2026-10-27，现状见上）**')
        text = text.replace('- **U5-L4确认①与P2（2026-10-26）**', '- **U5-L4历史确认①与P2（2026-10-26，已由10-28结论更新）**')
        text = text.replace('27格定稿；确认①通过，逐格测试及整课②待补项见', '27格定稿；P2已由用户确认通过，历史逐格测试范围见')
    elif rel == RP:
        text = after_heading(text, '> **五课阶段更新（2026-10-28）**：' + NOTE + '\n> [P3教师稿、全部格映射及确认④检查项](../03_X课程项目/实验验证/' + REPORT + ')。五课生成器已按当前稿同步；本轮保护修正的离线核查不延伸为新真机结论。')
        remarks = {
            'U5-L4': '27格（18 md/9 code），9个STEP。①既有通过，用户本轮确认P2复核通过并授权P3；③登记，P3教师稿待④。原Notebook字节保留，生成器镜像当前稿；历史测试清单保留，不新造逐格输出。',
            'U6-L1': '18格（16 md/2 code），_gen_L21.py镜像当前稿。三种动作依据、采集/回放/训练、Booster Train分工及预录轨迹字段；P1/P2及①②由用户通过。Notebook原字节保留，45分钟教师稿待④。',
            'U6-L2': '16格（12 md/4 code），_gen_L22.py反向同步。录制、保存、读回、本课回放及两版比较；P1/P2及①②通过。仅订正保存提示和收尾标点；当前代码未自动检查所有版本绑定，教师稿据实安排核查。实体按钮切模式。',
            'U6-L3': '17格（16 md/1 code），_gen_L23.py反向同步用户当前稿。骨架提取、imretarget、Booster Train、输入/结果对照与条件部署；当前含execute_whole_body_control资源示例，导出附件待备。P1/P2及①②通过，P3教师稿待④。',
            'U6-L4': '18格（14 md/4 code），_gen_L24.py反向同步。3～5步作品，实际混编录制轨迹与内置动作；用户确认等待后取消并检查CANCELLED，结合现场效果判断。句柄初始化移回首次连接格；本轮保护仅离线核查。工坊资源未接入基础循环。P1/P2及①②通过，P3教师稿待④。',
        }
        lines = []
        for line in text.split('\n'):
            if line.startswith('| `03_X课程项目/notebooks/') and any('/' + key + '_' in line for key in NAMES):
                key = next(key for key in NAMES if '/' + key + '_' in line)
                parts = line.split('|')
                parts[3] = ' 🟢 **P2通过；P3教学设计已完成，待用户确认④（2026-10-28）** '
                parts[4] = ' ' + remarks[key] + ' '
                line = '|'.join(parts)
            lines.append(line)
        text = '\n'.join(lines)
        existing = {key for key in NAMES if any(line.startswith('| `03_X课程项目/notebooks/' + key + '_') for line in lines)}
        def current_row(key):
            basename = 'U5-L4_语音问答闭环' if key == 'U5-L4' else key + '_' + NAMES[key]
            return '| `03_X课程项目/notebooks/' + basename + '.ipynb` | ' + key.replace('-', '·') + ' | 🟢 **P2通过；P3教学设计已完成，待用户确认④（2026-10-28）** | ' + remarks[key] + ' |'
        if existing != set(NAMES):
            expanded = []
            for line in text.split('\n'):
                if line.startswith('| `03_X课程项目/notebooks/U6-L1_') and 'U5-L4' not in existing:
                    expanded.append(current_row('U5-L4'))
                expanded.append(line)
                if line.startswith('| `03_X课程项目/notebooks/U6-L1_'):
                    expanded.extend(current_row(key) for key in ('U6-L2', 'U6-L3', 'U6-L4') if key not in existing)
            text = '\n'.join(expanded)
        text = text.replace('## 7. 变更记录\n', '## 7. 变更记录\n\n- 2026-10-28 **五课P3**：U5-L4及U6四课P2由用户确认通过，五份教师稿完成、待④；96格/20代码格覆盖检查通过。L4按实测保留取消方式，文字评价及初始化保护同步；L3资源示例已纳入条件演示，导出附件待备。\n')
    elif rel == CP + 'X课程开发计划-v4.md':
        text = replace_line(text, '| U5 | L4 |', '| U5 | L4 | 语音会话管理 | 持续chat任务句柄、状态回调、有限等待、取消与终态，应用状态机控制启停；P2用户确认通过，P3教学设计待④ | `U5-L4_语音问答闭环` |')
        text = after_heading(text, '> **五课P3（2026-10-28）**：' + NOTE + '\n> [教师稿与覆盖检查](实验验证/' + REPORT + ')。本轮五课教学设计完成，等待确认④；未生成P4内容大纲。')
        text = text.replace('1课P2、11课P1待审/验证', '5课P3待④、7课P1待审/验证')
        text = text.replace('> **U6进度（2026-10-26）**', '> **U6历史进度（2026-10-26，已由10-28结论更新）**')
        text = text.replace('> **U5-L4确认①与P2（2026-10-26）**', '> **U5-L4历史确认①与P2（2026-10-26，已由10-28结论更新）**')
        text = text.replace('（2026-10-20 评审修订稿，待确认①与真机确认②）', '（用户确认P1/P2及①②通过；P3教学设计待④）')
        text = text.replace('（2026-10-26 P1重构稿，待①②）', '（P1/P2及①②通过；P3教学设计待④）')
        text = text.replace('（P1重构稿，待①及平台验证②）', '；现稿含全身控制资源调用示例（P1/P2及①②通过；P3教学设计待④）')
        text = text.replace('；工坊SDK待用户确认（P1重构稿，待①②）', '；按用户实测等待后取消，区分取消终态与动作效果；工坊资源混编未接入（P1/P2及①②通过；P3教学设计待④）')
        text = text.replace('## 十三、下一步（2026-10-24）', '## 十三、下一步（2026-10-28更新）\n\n五课P3教学设计已产出，先由用户确认④；通过后再按授权进入P4。以下其他课程安排沿用已有范围。')
        text = text.replace('U5-L4第二轮27格新稿仍待新确认①②。', 'U5-L4 P2复核已由用户确认通过，P3教学设计待④。')
    elif rel == CP + 'X课程当前进度.md':
        text = text.replace('本次不运行机器人、不复审PPT内容、不改学生学材或教学设计正文。', '2026-10-28按用户确认更新U5-L4和U6四课：P2通过，P3教师稿完成、待确认④。历史核查和本轮修订范围分别记录，不编造新真机输出。')
        text = text.replace('| P2复核中 | 1 | U5-L4，文稿已复核，整课真机依据待齐，③未通过 |', '| P3教学设计已产出，确认④待审 | 5 | U5-L4、U6四课；用户已确认P2通过 |')
        text = text.replace('| P1修订或待审/验证 | 11 | U4-L2～L4、U6四课、U7四课 |', '| P1修订或待审/验证 | 7 | U4-L2～L4、U7四课 |')
        pending = {
            'U5-L4': '语音会话管理；原文件名保留。部署拓展课后阅读；不补造旧清单逐项实测输出',
            'U6-L1': '概念概述与预录轨迹读取；反向同步当前稿，保持Notebook原字节',
            'U6-L2': '两版录制与回放；仅修正保存提示及标点，设备轮换未完成项另排补做',
            'U6-L3': '当前17格含1格资源调用示例；导出附件待备，本组训练未结束时用已完成样例比较',
            'U6-L4': '按实测保留等待后取消；句柄初始化保护已离线修正，未冒称新真机；工坊资源未接入基础混编',
        }
        lines = []
        for line in text.split('\n'):
            key = next((k for k in NAMES if line.startswith('| [' + k + ' ')), None)
            if key:
                first = line.split('|')[1].strip()
                confirm = '①既有通过；用户本轮确认P2复核通过，登记③' if key == 'U5-L4' else '用户本轮确认P1/P2评审及①②通过，登记③'
                link = f'[教学设计](教学设计/{key}_{NAMES[key]}_教学设计.md)'
                line = f'| {first} | P3教学设计已完成，待确认④ | {confirm} | 审阅{link}并确认④ | {pending[key]} |'
            lines.append(line)
        text = '\n'.join(lines)
        text = text.replace('| 教学设计 | 16 | U1/U2/U3各4课、U4-L1、U5-L1～L3；目录含总草案及副本，不重复计课 |', '| 教学设计 | 21 | 原16课加U5-L4、U6四课；本轮五课待④；总草案和副本不重复计课 |')
        text = text.replace('5. **U5-L4已进入P2，但③尚未通过**：①已通过，部分STEP有用户实测，整课②依据待补；旧P5清单中“U5-L4待①”是当时状态，已被后续确认覆盖。', '5. **U5-L4 P2结论已更新**：用户2026-10-28明确确认P2复核通过并要求推进P3，按结论登记③；五课教师稿已完成、待④。旧清单保留为历史依据，不再把旧待补项作为阻止本次推进的条件，也不补造逐格输出。')
        text = text.replace('6. **U6/L4静态检查与真机验证分开**：重构和初学者代码简化已完成；平台与真机②尚待完成，动作工坊新SDK由用户确认后接入。', '6. **U6用户确认与本轮修正范围分开**：用户确认四课P1/P2及①②通过，并确认L4等待后取消的用法。五课P3稿基于当前Notebook；L4句柄初始化保护本轮离线核查，不冒称新增真机。L3资源接口示例已在现稿中，L4基础脚本尚未接入该类型。')
        text = text.replace('2. 补齐U5-L4整课②依据后结束P2审定；不重复已经有明确实测结论的步骤。', '2. 审阅U5-L4与U6四课P3教学设计，确认④后再进入P4；不要求重新确认已由用户通过的P1/P2。')
        text = text.replace('3. U6按新分工审阅及验证，L3先确认平台实际入口和样例，L4先验证录制轨迹与内置动作组合，工坊SDK接入另补验。', '3. 准备L3导出附件与已完成样例；L4三类素材整合在基础版本之外另作接入与整体验证，课堂用任务终态和现场效果分别记录。')
        text += '\n## 8. 五课P3最新依据（2026-10-28）\n\n' + NOTE + '\n\n详见[五课覆盖检查](实验验证/' + REPORT + ')及五份教师稿。P3尚待确认④，未登记P4/P5完成。\n'
    elif rel == CP + '实验验证/U5-L4_P2复核与定稿记录.md':
        text = after_heading(text, '## 最新结论（2026-10-28）\n\n用户明确“U5-L4 P2复核通过”，并授权推进P3。据此登记P2/③通过，P3教学设计已产出、待确认④；不再将下方历史依据待补作为本次推进阻断项。用户没有提供的新逐格输出不代为补写。\n\n[教学设计](../教学设计/U5-L4_语音会话管理_教学设计.md)；[五课覆盖检查](' + REPORT + ')。本轮Notebook原字节保留，生成器以当前主稿反向同步。\n\n---\n\n以下为2026-10-26历史复核记录，保留当时结论与待补范围；现行阶段以上述用户最新确认为准。')
        text = text.replace('## 当前结论', '## 2026-10-26当时结论')
    elif rel == CP + '实验验证/U6_单元重构与动作编排核验.md':
        text = after_heading(text, '> **最新结论（2026-10-28）**：用户确认U6四课P1/P2评审及①②通过，P3四份教师稿已完成、待④。当前L3为17格，包含1格execute_whole_body_control资源调用；L4按用户实测保留等待后取消，文字与评价已同步，初始化保护移回首次连接格。下方2026-10-26/27的待验及“仅SUCCEEDED继续”等描述是历史依据，不作为现行调用规则。详见[' + REPORT + '](' + REPORT + ')。')
    return text

def main():
    paths = json.loads((TASK / '输入指纹.json').read_text(encoding='utf-8'))
    patches = []
    for rel in paths:
        if rel not in ('AGENTS.md', 'INDEX.md', 'CHANGELOG.md', RP,
                       '05-internal-materials/vocational-planning/README.md',
                       CP + 'X课程开发计划-v4.md', CP + 'X课程当前进度.md',
                       CP + '实验验证/U5-L4_P2复核与定稿记录.md',
                       CP + '实验验证/U6_单元重构与动作编排核验.md'):
            continue
        path = ROOT / rel
        original = (TASK / 'before' / rel).read_text(encoding='utf-8')
        new = update(rel, original)
        assert new != original, rel
        path.write_text(new, encoding='utf-8')
        base = TASK / 'head' / rel
        if base.exists():
            old_head = base.read_text(encoding='utf-8')
            new_head = update(rel, old_head)
            patches.extend(difflib.unified_diff(old_head.splitlines(keepends=True),
                           new_head.splitlines(keepends=True), fromfile='a/' + rel, tofile='b/' + rel))
    (TASK / '提交状态增量.patch').write_bytes(''.join(patches).encode('utf-8'))
    print('已从本轮输入基线更新9份阶段/导航记录，并生成仅含本轮状态变更的暂存补丁')

if __name__ == '__main__':
    main()
