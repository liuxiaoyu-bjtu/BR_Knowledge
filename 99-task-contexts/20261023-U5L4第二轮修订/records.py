"""只联动本轮课程状态；历史日志保留，混合文件的增量另存。"""
import difflib
from revise import ROOT, TASK, PROJ, SHARED

DETAIL = 'U5-L4已完成第二轮学生稿修订，27格（18 Markdown/9代码）；细讲TaskHandle[None]、任务状态来源、有限等待及状态回调，状态机实际控制开始/查看/停止。学生正文已移除设计旁白与recognize()，新增可选部署拓展。待新稿确认①、②，未进入P2。'
OLD = 'U5-L4已按用户认可方向重构为持续会话管理，23格（15 Markdown/8代码），待新稿确认①、②；不再测单轮或ASR/LLM/TTS分段延迟，不使用U7线程与锁。'

def edit(p, fn):
    s = p.read_text(encoding='utf-8')
    t = fn(s)
    p.write_text(t, encoding='utf-8')

def once(s, a, b):
    assert s.count(a) == 1, (a, s.count(a))
    return s.replace(a, b, 1)

def main():
    for p in (ROOT/'AGENTS.md', PROJ/'X课程开发计划-v4.md', PROJ.parent/'README.md', SHARED[-1]):
        edit(p, lambda s: once(s, OLD, DETAIL))
    plan = PROJ/'X课程开发计划-v4.md'
    edit(plan, lambda s: once(s, '`Speech.chat()`→保留`TaskHandle`；`status/error/done()`查看任务；',
                            '`Speech.chat()`→保留`TaskHandle[None]`；`trace_id/status/error/done()`查看任务，登记状态回调；'))
    edit(plan, lambda s: once(s, 'U5-L4会话管理新稿已完成，待新确认①②，不能沿用旧确认。',
        'U5-L4第二轮27格新稿及教学审阅、真机验证建议已完成，待新确认①②，不能沿用旧确认。'))
    outline = PROJ/'X课程大纲-v4.md'
    edit(outline, lambda s: once(s, '保存`chat()`句柄；查看`status/error/done()`；',
        '理解`chat()`返回的任务句柄与无结果数据；查看`trace_id/status/error/done()`，登记状态回调；'))
    edit(outline, lambda s: once(s,
        '> **U5更新（2026-10-23）**：用户认可持续会话管理方向，L4新Notebook已重构为23格，待设计确认①、真机确认②；原单轮/分段延迟及内部四阶段程序状态机不再沿用。接口依据见[SDK能力核验记录](实验验证/U5_语音SDK能力核验记录.md)。L1～L3保留真机确认②，P2已复核、有问题待[修改方案](实验验证/U5-L1-L2-L3_P2复核与修改方案.md)确认；定稿后再同步相应课时的大纲文字。',
        '> **U5更新（2026-10-23）**：L4第二轮Notebook为27格（18 Markdown/9代码），新增句柄与状态观察实验，待新确认①②；教学审阅与测试步骤见[确认文档](实验验证/U5-L4_教学审阅与真机验证建议.md)。保留持续会话管理方向，停用单轮/分段计时，未引入U7。L1～L3已按用户反馈完成P2修订，保留历史真机确认②及原执行信息，改码部分待定向补验，尚未定稿；详见[P2记录](实验验证/U5-L1-L2-L3_P2复核与修改方案.md)。'))
    rules = SHARED[-1]
    oldrow = '| `03_X课程项目/notebooks/U5-L4_语音问答闭环.ipynb` |'
    def rule_rows(s):
        lines = s.splitlines(True)
        for i, line in enumerate(lines):
            if line.startswith(oldrow):
                lines[i] = oldrow + ' U5·L4 | 🟡 **P1第二轮修订完成（2026-10-23）；待新确认①②** | 27格（18 md/9 code），`_gen_L20.py`已同步。9个STEP：先观察句柄、状态、有限等待与回调，再用三应用状态控制开始/查看/停止。拦截重复启动、保留旧句柄、确认终态后重开；四道评价与两道解释题，教师答案移入审阅文档。可选端侧/联网部署拓展，不采用recognize()与U7并发。教学审阅与真机验证建议已形成，尚未真机验证。 |\n'
        return ''.join(lines)
    edit(rules, rule_rows)
    edit(rules, lambda s: once(s,
        '| U5-L4 | 原设计中的问答链路目标待随重构核对 | 原「测出用时并指出花在哪一段」已失效；新目标待方案确认后更新 |',
        '| U5-L4 | 按输入输出解释问答功能及持续会话 | 说明句柄用途并判断任务是否结束；依据转换条件操作会话管理程序（第二轮稿待新确认①②） |'))
    edit(rules, lambda s: once(s,
        '| U5-L4 | 原延迟测量主线已于2026-10-22复评停用，节序待重构 | 当前接口不能提供单轮及分段的起止信号，不据此制定计时验收线 |',
        '| U5-L4 | 功能过程 → 句柄 → 状态 → 实测观察 → 状态机操作 | 以真实任务状态决定能否重开，先观察再抽象转换规则；第二轮稿待验证 |'))
    edit(rules, lambda s: once(s,
        '`<font color="red">提示：…</font>` 只交代学生**看不到就会误判**的信息：会响多久、会不会出声、要不要准备秒表、要不要按顺序说话。U5-L4 的 4.2 是最完整的一例——「准备好手机、秒表——从你说完最后一个字开始按，到听见机器人开口再按一次，中途不要说话」。**不在提示里讲原理。**',
        '`<font color="red">提示：…</font>` 交代影响学生操作和判断的信息，例如是否出声、执行顺序、初始化是否会丢失旧句柄。原U5-L4秒表计时例子已停用，不再作为有效范例。原理另放知识讲解，提示不重复正文。'))
    edit(rules, lambda s: once(s,
        '- U5-L4 2.4：「……这是另一项有挑战的任务，本门课程暂时不做深入探讨，感兴趣的学生可以自行探索。」',
        '- 原U5-L4 2.4例句随计时设计停用；现稿以明确的操作范围说明任务，不追加泛泛的自行探索提示。'))
    edit(rules, lambda s: once(s, '## 8.27 知识型课的语言表述方式',
        '## 8.27 知识型课的语言表述方式'))
    # 新规则只限定本类学生材料，不改写既有跨课程制度。
    edit(rules, lambda s: s.rstrip() + '''

## 8.31 学生材料与教师审阅说明（2026-10-23，U5-L4第二轮）

学生正文解释完成当前任务所需的对象、条件、操作和可观察结果。旧版设计为何失效、与用户讨论的取舍、未采用接口的缺项及待核实SDK行为，放入实验验证目录的教师审阅文档。必要的操作限制仍须就近提示，如有限等待后检查终态、保留未结束的句柄。

任务状态先说明从哪个对象的哪个属性取得，再解释取值和判断用途。引入回调时写明参数、触发时机和登记范围。应用状态机须实际控制操作，不能用打印内部阶段或给只读状态赋值替代真实执行。接口契约、离线替身验证和真机现象分别记录。
''')
    log = '- 2026-10-23 **U5-L4第二轮学生稿修订**：27格（18 md/9 code）、9个STEP；补细致句柄讲解、有限等待与状态回调实验，应用状态参与实际控制；移除设计旁白与recognize()，另写教学审阅和真机验证建议。新确认①②待用户作出，前三课未改，未运行机器人。\n\n'
    edit(rules, lambda s: once(s, '- 2026-10-23 **U4-L1 P3、U5语音SDK核验与P2复核**', log + '- 2026-10-23 **U4-L1 P3、U5语音SDK核验与P2复核**'))
    edit(ROOT/'INDEX.md', lambda s: once(s,
        '| X课程 U5-L4 / 语音计时问题 / 会话管理重构 | [真机问题复评与重构建议](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U5-L4_真机问题复评与重构建议.md)（2026-10-23新稿已重构，23格；待新确认①②） |',
        '| X课程 U5-L4 / 语音计时问题 / 会话管理重构 | [真机问题复评与重构建议](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U5-L4_真机问题复评与重构建议.md)（历史问题依据；现稿27格，待新确认①②） |\n'
        '| X课程 U5-L4 / TaskHandle[None] / 状态回调 / 应用状态机 / 教学审阅 / 真机测试 | [教学审阅与真机验证建议](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U5-L4_教学审阅与真机验证建议.md)（第二轮修订、逐格测试及确认清单，2026-10-23） |'))
    edit(PROJ.parent/'README.md', lambda s: once(s, '- U5入口：',
        '- U5-L4第二轮审阅入口：[教学审阅与真机验证建议](03_X课程项目/实验验证/U5-L4_教学审阅与真机验证建议.md)（27格现稿；含教学取舍、状态机解释、逐格测试和待确认清单）。\n- U5入口：'))
    edit(ROOT/'CHANGELOG.md', lambda s: once(s, '# 更新日志\n', '''# 更新日志

## 2026-10-23 · U5-L4第二轮学生稿与教师确认文档

- 重写L4为27格（18 Markdown/9代码），补听、懂、说的功能关系、任务句柄及无结果数据的含义、状态来源与终态判断；加入有限等待、任务标识与状态回调观察。
- 三应用状态实际控制会话操作：旧任务未终止时阻止重复启动，取消后保留句柄核查终态，再允许重开。无线程或锁，不提前使用U7。
- 学生正文移除设计旁白、旧版纠错说明及recognize()，提示词改为简短学习助手；教师答案转存审阅文档。增加可选端侧/联网部署阅读，具体服务配置由教师确认。
- 新增教学审阅与真机验证建议，解释提示词、只读状态、cancel请求及状态机作用，列逐格测试和用户确认清单。同步生成器、大纲、计划、规则和导航。前三课未改；本轮仅离线核验，待新确认①②。
- 本地Git记录，推送仍由用户手动完成。
'''))
    sdk = PROJ/'实验验证/U5_语音SDK能力核验记录.md'
    edit(sdk, lambda s: s.rstrip() + '''

## 六、U5-L4第二轮：只读状态与应用状态机

2026-10-23再次回读TaskHandle、TaskStatus和chat的官方页面：status、error为只读；wait超时返回当前状态，不会自动取消；cancel返回是否成功提交请求。TaskHandle[None]仍是句柄，只是没有供程序领取的最终结果数据。

add_status_change_callback(fn)接收任务句柄，注册时立即以当前状态触发一次，后续状态变化时再调用；注册前已发生的短暂状态不会补发。本课回调只打印，不修改管理状态或调度其他任务。当前Notebook环境的后续回调输出位置待真机核实。

应用状态机可根据操作与旧任务是否终止来决定调用chat或cancel；SDK按实际执行情况更新任务状态。读状态、调用done或wait、修改应用字符串，都不会直接设定SDK状态。不主动取消时仍可能发生启动或故障等生命周期变化；公开文档未给出持续聊天的全部自然终止条件，不能承诺永远RUNNING，也不推定静默后自动停止。

L4第二轮未使用recognize()。该接口在本记录中作为官方能力索引保留，不表示加入课程。学生稿27格，新增状态观察与真实操作控制，待新确认①②；教学取舍、接口依据与逐格测试见[教学审阅与真机验证建议](U5-L4_教学审阅与真机验证建议.md)。本轮未连接真机或核验SDK实现源码。
''')
    review = PROJ/'实验验证/U5-L4_真机问题复评与重构建议.md'
    edit(review, lambda s: once(s, '# U5-L4 真机问题复评与重构建议\n', '''# U5-L4 真机问题复评与重构建议

> **第二轮更新（2026-10-23）**：现学生稿27格（18 Markdown/9代码），增加句柄与任务状态的细致讲解、有限等待和状态回调观察；应用状态实际参与控制。原设计问题与首轮23格记录保留作历史依据。当前教学安排、教师参考答案和逐格测试以[教学审阅与真机验证建议](U5-L4_教学审阅与真机验证建议.md)为准。待新确认①②，未运行真机。
'''))
    # 共享文件混有前序未提交工作，不整体纳入本轮提交。
    patch = []
    for p in SHARED:
        before = (TASK/'before'/p.relative_to(ROOT)).read_text(encoding='utf-8').splitlines(True)
        after = p.read_text(encoding='utf-8').splitlines(True)
        rel = p.relative_to(ROOT).as_posix()
        patch.extend(difflib.unified_diff(before, after, fromfile='a/'+rel, tofile='b/'+rel))
    (TASK/'共享文档本轮增量.patch').write_text(''.join(patch), encoding='utf-8')
    print('状态、大纲、规则、索引及SDK记录已联动；共享文件本轮增量已归档。')

if __name__ == '__main__':
    main()
