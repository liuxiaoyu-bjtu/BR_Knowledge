"""将本次用户确认与P3/P4产出同步到进度入口；不改Notebook。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
STATUS = ('U4-L1、U5-L1～L3已由用户于2026-10-23确认③通过并授权推进P4。'
          '四课P4内容大纲已完成，页数依次为27/27/28/28；U5三份P3教学设计已补齐，'
          '确认④、⑤待用户审阅。四课Notebook、L2附件及发放副本、四个生成器本轮未改。'
          'U4纵向对准编程与U5-L2/L3扩展阅读另排课后，未完成的个人轮换保留补做记录。'
          'P5未启动，实际投影定位在P5-B回填。U4-L2～L4仍待真机确认②。')
L4 = ('U5-L4已完成第二轮学生稿修订，27格（18 Markdown/9代码）；细讲TaskHandle[None]、'
      '任务状态来源、有限等待及状态回调，状态机实际控制开始/查看/停止。学生正文已移除设计旁白与'
      'recognize()，新增可选部署拓展。待新稿确认①、②，未进入P2。')
COVERAGE = 'PPT内容设计/U4-L1_U5-L1-L3_P4覆盖检查记录.md'


def read(path):
    return path.read_text(encoding='utf-8')


def write(path, text):
    path.write_text(text, encoding='utf-8')


def replace_line(path, prefix, replacement):
    text = read(path)
    lines = text.splitlines()
    matches = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    assert len(matches) == 1, (path, prefix, matches)
    lines[matches[0]] = replacement
    write(path, '\n'.join(lines) + '\n')


replace_line(ROOT / 'AGENTS.md', '  - U4-L1 P3教学设计已完成',
             '  - ' + STATUS + L4 + '覆盖与审阅入口见`03_X课程项目/' + COVERAGE + '`。')
replace_line(PROJECT / 'X课程开发计划-v4.md', '> **U4/U5更新（2026-10-23）**',
             '> **U4/U5更新（2026-10-23）**：' + STATUS + L4 +
             '详见[四课P4覆盖检查记录](' + COVERAGE + ')。')
replace_line(PROJECT / 'X课程开发计划-v4.md', '3. U4-L1 P3教学设计已完成',
             '3. U4-L1已由用户确认③通过并授权推进P4，27页内容大纲已完成；教学设计与大纲待确认④⑤。'
             '纵向对准自主编程课内交思路、课后由教师安排验证；P5-B再回填实际投影定位。其余三课仍待真机确认②。')
replace_line(PROJECT / 'X课程开发计划-v4.md', '4. U5-L1～L3已按用户反馈修订并同步',
             '4. U5-L1～L3已由用户确认③通过并授权推进P4，三份P3教学设计与27/28/28页P4大纲已完成，'
             '待确认④⑤。保持已确认Notebook、执行记录、附件和生成器；L2/L3全文扩展阅读课后完成，'
             'L3三种人设分组汇总、个人未完成操作另排补做。U5-L4第二轮27格新稿仍待新确认①②。'
             'L2发放保持Notebook、sound_lab.py和fonts/相对位置。')

nav = ROOT / '05-internal-materials/vocational-planning/README.md'
replace_line(nav, '- **U4/U5进度（2026-10-23）**', '- **U4/U5进度（2026-10-23）**：' + STATUS + L4)
replace_line(nav, '- U4-L1入口：',
             '- U4-L1入口：[P2复核与定稿记录](03_X课程项目/实验验证/U4-L1_P2复核与定稿记录.md)、'
             '[P3教学设计](03_X课程项目/教学设计/U4-L1_转向来宾_教学设计.md)、'
             '[P4内容大纲](03_X课程项目/PPT内容设计/U4-L1_转向来宾_PPT内容大纲.md)（确认③已通过，④⑤待审）。')
s = read(nav)
needle = '- U5-L4第二轮审阅入口：'
assert needle in s
s = s.replace(needle, '- 四课P4审阅入口：[覆盖检查记录](03_X课程项目/' + COVERAGE +
              ')（含四份大纲、四份教学设计链接、144格及40格代码映射、评价与课后安排）。\n' + needle, 1)
write(nav, s)

index = ROOT / 'INDEX.md'
replace_line(index, '| X课程 U4-L1 P2 /',
             '| X课程 U4-L1 P2 / 转向对准 / 结束原因 | [复核与定稿记录]('
             '05-internal-materials/vocational-planning/03_X课程项目/实验验证/U4-L1_P2复核与定稿记录.md)'
             '（2026-10-23用户确认③通过；P4已完成，④⑤待审） |')
replace_line(index, '| X课程 U5 P2 /',
             '| X课程 U5 P2 / 三课复核与修改方案 | [U5-L1～L3复核方案]('
             '05-internal-materials/vocational-planning/03_X课程项目/实验验证/U5-L1-L2-L3_P2复核与修改方案.md)'
             '（2026-10-23用户确认③通过；历史问题与补验清单保留，已完成P3/P4，④⑤待审） |')
s = read(index)
needle = '\n## 临时任务记录'
assert needle in s
new = ('| X课程 U4-L1 / U5-L1～L3 P4 / 教学设计 / 内容大纲 / 覆盖检查 | '
       '[四课覆盖检查记录](05-internal-materials/vocational-planning/03_X课程项目/' + COVERAGE +
       ')（27/27/28/28页，144格与40格代码、目标、评价、附件及课后安排；确认③通过，④⑤待审） |\n')
s = s.replace(needle, new + needle, 1)
write(index, s)

internal = ROOT / '05-internal-materials/_README.md'
s = read(internal)
needle = '\n## 📂 目录结构'
assert needle in s
s = s.replace(needle, '\n> **X课程四课P4（2026-10-23）**：U4-L1与U5-L1～L3用户确认③通过，'
              '四份内容大纲已完成，U5三份教学设计已补齐，确认④⑤待用户审阅；Notebook未改。'
              '见[覆盖与审阅入口](vocational-planning/03_X课程项目/' + COVERAGE + ')。\n' + needle, 1)
write(internal, s)

rules = ROOT / '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md'
replace_line(rules, '> **状态更新（2026-10-23，U4-L1与U5）**',
             '> **状态更新（2026-10-23，U4-L1与U5）**：' + STATUS + L4 +
             '详见[四课P4覆盖检查记录](../03_X课程项目/' + COVERAGE + ')。')
s = read(rules)
needle = '## 7. 变更记录\n'
assert needle in s
s = s.replace(needle, needle + '\n- 2026-10-23 **四课确认③与P4交付**：用户确认U4-L1、U5-L1～L3通过确认③，'
              '授权直接推进P4；补齐U5三份P3，完成27/27/28/28页大纲和覆盖检查。'
              '确认④⑤待用户审阅，P5未启动；Notebook、附件、副本和四个生成器均未改。'
              '课后内容、分组汇总和个人补做明确记录；教学设计实际投影定位留P5-B。\n', 1)
write(rules, s)

u4design = PROJECT / '教学设计/U4-L1_转向来宾_教学设计.md'
s = read(u4design)
header = '# U4-L1：转向来宾（视觉对准）\n'
assert s.startswith(header)
s = s.replace(header, header + '\n> 2026-10-23：用户确认③通过并授权推进P4；本课教学设计与27页内容大纲已完成，'
              '确认④、⑤待用户审阅。Notebook保持原稿；P5-B回填实际投影定位。\n'
              '> 依据：[学生Notebook](../notebooks/U4-L1_转向来宾.ipynb)、'
              '[PPT内容大纲](../PPT内容设计/U4-L1_转向来宾_PPT内容大纲.md)。\n', 1)
write(u4design, s)

u4p2 = PROJECT / '实验验证/U4-L1_P2复核与定稿记录.md'
s = read(u4p2)
lines = s.splitlines()
lines[1:1] = ['', '> 2026-10-23进度更新：用户明确确认③通过并授权推进P4。P3教学设计和27页P4大纲已完成，'
              '确认④⑤待审；本轮不改Notebook、不重新运行真机。下文保留前次P2审定记录。',
              '> 见[四课P4覆盖检查记录](../' + COVERAGE + ')。']
write(u4p2, '\n'.join(lines) + '\n')

u5p2 = PROJECT / '实验验证/U5-L1-L2-L3_P2复核与修改方案.md'
s = read(u5p2)
old = '日期：2026-10-23。状态：**已按用户2026-10-23逐项反馈修订三课，待改码部分定向真机补验；P2尚未定稿，不进入P3。**'
assert old in s
s = s.replace(old, '日期：2026-10-23。当前状态：**用户已明确确认L1～L3通过确认③，并授权推进P4。'
              'P2已定稿，三份P3教学设计及27/28/28页P4大纲已完成，确认④⑤待审。**\n\n'
              '> 本文表格保留前轮发现、修订和当时提出的定向补验清单，作为历史记录；“需补验”等表内措辞不是当前阶段结论。'
              '本次确认依据用户明确指令，助手未重新执行真机，也不补写不存在的现场输出。'
              '当前四课审阅入口见[覆盖检查记录](../' + COVERAGE + ')。', 1)
old = '完成补验后再做P2定稿判断。当前未登记确认③通过，未启动P3。'
assert old in s
s = s.replace(old, '以上为前轮定向补验建议。2026-10-23用户已明确确认③通过并授权推进P4，'
              '现登记P2定稿；三份P3及P4已完成，确认④⑤待用户审阅。本轮不改三课代码和执行记录。', 1)
write(u5p2, s)

attachments = PROJECT / 'notebooks/_外挂附件清单.md'
s = read(attachments)
old = '已入库；确认②历史通过；2026-10-23补播放终态与超时判断，待定向补验'
assert old in s
s = s.replace(old, '已入库；补播放终态与超时判断后，用户于2026-10-23确认本课③通过；P3/P4已完成，附件本轮未改', 1)
write(attachments, s)

changelog = ROOT / 'CHANGELOG.md'
s = read(changelog)
needle = '# 更新日志\n'
assert needle in s
entry = '''
## 2026-10-23 · U4-L1与U5前三课确认③、完成P4内容大纲

- 登记用户明确确认U4-L1、U5-L1～L3通过确认③并授权推进P4；保留历史复核及补验清单，不冒记助手再次真机运行。
- 补齐U5三份45分钟教学设计，完成四份27/27/28/28页内容大纲。四课144格、40格代码、目标、检查点、思考及附件均有映射；U4纵向编程、U5-L2/L3扩展阅读和未完成轮换列明课后安排。
- 明确三声道PCM换算、队列写入计时、头角读取与角速度、同文本音色对照、持续会话wait与分组人设实验。Notebook、L2附件及发放副本、四个生成器保持不变。
- 更新计划、规则、确认记录和导航。P3/P4产物待用户确认④⑤，P5未启动；实际投影定位留P5-B。U4其他三课和U5-L4确认状态不变。
- 本地Git仅记录本轮产物和增量，推送由用户手动完成。
'''
s = s.replace(needle, needle + entry, 1)
write(changelog, s)
print('已同步11份确认记录、计划与导航。')

# 逐课状态也同步到当前结论，前轮问题保留在P2历史记录中。
row_notes = {
    'U4-L1_转向来宾': '现稿44格（30 md/14 code）；本轮Notebook未改。P3沿用现稿，P4共27页；覆盖STEP01～12、比例对照、两种转身、Kpx、记录及评价。纵向自主编程课内交思路，课后教师安排验证；实际投影定位留P5-B。',
    'U5-L1_语音识别': '现稿34格（25 md/9 code）；本轮Notebook、执行信息及_gen_L17.py未改。三声道PCM、队列对照、close→wait及识别收尾沿确认稿；已补P3并完成27页P4。前轮问题和补验清单保留在P2复核方案，当前③通过。',
    'U5-L2_语音合成': '现稿34格（24 md/10 code）；本轮Notebook、执行信息、附件、发放副本及_gen_L18.py未改。已补P3并完成28页P4，第28页为课后阅读；按完整目录发放，区分附件与SDK同名播放函数。前轮问题保留在P2复核方案，当前③通过。',
    'U5-L3_LLM对话': '现稿32格（25 md/7 code）；本轮Notebook、执行信息及_gen_L19.py未改。已补P3并完成28页P4，第28页为课后阅读；保留wait、中断取消与终态核查。三人设分组汇总，个人未完成操作另排补做。前轮问题保留在P2复核方案，当前③通过。',
}
s = read(rules)
lines = s.splitlines()
for key, note in row_notes.items():
    matches = [i for i, line in enumerate(lines) if line.startswith('| `03_X课程项目/notebooks/' + key + '.ipynb` |')]
    assert len(matches) == 1, (key, matches)
    i = matches[0]
    cols = lines[i].split('|')
    cols[3] = ' 🟡 **确认③通过；P3/P4完成，待确认④⑤（2026-10-23）** '
    cols[4] = ' ' + note + ' '
    lines[i] = '|'.join(cols)
write(rules, '\n'.join(lines) + '\n')
print('四课逐课状态已与汇总一致。')
