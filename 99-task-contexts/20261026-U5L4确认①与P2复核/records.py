"""登记用户确认①，冻结Notebook现稿，更新P2复核记录与阶段入口。"""
from pathlib import Path
import hashlib
import json
import runpy

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
NB = PROJ / 'notebooks/U5-L4_语音问答闭环.ipynb'
GEN = PROJ / '_gen_L20.py'
GUIDE = PROJ / '实验验证/U5-L4_教学审阅与真机验证建议.md'
RECORD = PROJ / '实验验证/U5-L4_P2复核与定稿记录.md'
SHARED = [ROOT / p for p in [
    'AGENTS.md', 'INDEX.md', 'CHANGELOG.md', '05-internal-materials/_README.md',
    '05-internal-materials/vocational-planning/README.md',
    '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md',
]] + [PROJ / 'X课程开发计划-v4.md', PROJ / 'X课程大纲-v4.md']


def save(path, text):
    path.write_text(text, encoding='utf-8', newline='\n')


def main():
    assert not (TASK / '基线.json').exists(), '已执行，勿覆盖基线或重复插入记录。'
    assert not RECORD.exists(), '已有P2记录，需先核对现状。'
    files = [NB, GEN, GUIDE] + SHARED
    baseline = []
    for path in files:
        data = path.read_bytes()
        rel = path.relative_to(ROOT)
        backup = TASK / 'before' / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(data)
        baseline.append({'path': rel.as_posix(), 'sha256': hashlib.sha256(data).hexdigest()})
    save(TASK / '基线.json', json.dumps(baseline, ensure_ascii=False, indent=2) + '\n')
    notebook = json.loads(NB.read_text(encoding='utf-8'))
    old_generated = runpy.run_path(str(GEN), run_name='inspect_only')['cells']
    changed = [i for i, (a, b) in enumerate(zip(notebook['cells'], old_generated), 1) if a['source'] != b['source']]
    assert changed == [7, 15], changed
    lines = GEN.read_text(encoding='utf-8').splitlines(keepends=True)
    for cell in notebook['cells']:
        fn = 'md' if cell['cell_type'] == 'markdown' else 'code'
        if cell['source'] != old_generated[notebook['cells'].index(cell)]['source']:
            prefix = f'cells.append({fn}('
            matches = [i for i, line in enumerate(lines) if line.startswith(prefix) and repr(cell['id']) in line]
            assert len(matches) == 1, cell['id']
            lines[matches[0]] = f"cells.append({fn}({''.join(cell['source'])!r}, {cell['id']!r}))\n"
    save(GEN, ''.join(lines))
    assert hashlib.sha256(NB.read_bytes()).hexdigest() == baseline[0]['sha256']

    guide = GUIDE.read_text(encoding='utf-8')
    guide = guide.replace('**当前状态：新稿待设计确认①、真机确认②。**',
        '**当前状态：2026-10-26用户确认①通过，学生设计稿定稿；按用户指令进入P2复核。文稿复核已完成，整课真机确认②依据待齐，确认③暂不登记。**')
    guide = guide.replace('## 0. 2026-10-26反馈修订与实测记录',
        '> 当前阶段结论见[P2复核与定稿记录](U5-L4_P2复核与定稿记录.md)。以下反馈修订与局部实测记录继续留存。\n\n## 0. 2026-10-26反馈修订与实测记录')
    start = guide.index('教学审阅：', guide.index('## 6. 供用户确认'))
    end = guide.index('真机确认：', start)
    part = guide[start:end].replace('- [ ]', '- [x]').replace(
        '设计确认①：待确认。意见/需改位置：______。',
        '设计确认①：2026-10-26用户明确确认通过，当前学生内容定稿。Notebook未作改写，生成器已反向同步用户最后两处文字调整。')
    guide = guide[:start] + part + guide[end:]
    guide = guide.replace('下一步：用户确认设计并完成真机验证后，再进入P2复核与定稿。本轮不登记通过，不提前进入P3。',
        '当前按用户指令推进P2，文稿复核已完成。待补齐整课真机确认②依据后，再作P2最终审定及确认③结论；本轮未进入P3。已有局部实测继续有效，未据此补写未提供的真机结果。')
    save(GUIDE, guide)

    status = 'U5-L4《语音会话管理》于2026-10-26由用户确认①通过，学生设计稿定稿。按用户指令进入P2；文稿与控制逻辑复核完成，整课真机确认②依据待齐，确认③暂不登记。27格（18 Markdown/9代码）主稿原字节保留，生成器已反向同步用户最后两处文字调整。复核及待补依据见`实验验证/U5-L4_P2复核与定稿记录.md`，未进入P3。'
    for path in SHARED:
        text = path.read_text(encoding='utf-8')
        if path.name == 'AGENTS.md':
            text = text.replace('待新稿确认①、②，未进入P2。覆盖依据见', '当前状态以次条2026-10-26更新为准。覆盖依据见')
            lines = text.splitlines(keepends=True)
            for i, line in enumerate(lines):
                if line.startswith('  - U5-L4于2026-10-26'):
                    lines[i] = '  - ' + status + '\n'
            text = ''.join(lines)
        elif path.name == 'INDEX.md':
            text = text.replace('（历史问题依据；现稿27格，待新确认①②）', '（历史问题依据；现稿27格，确认①通过、P2复核中，整课②待齐）')
            anchor = '| X课程 U5-L4 / 语音会话管理 /'
            lines = text.splitlines(keepends=True)
            for i, line in enumerate(lines):
                if line.startswith(anchor):
                    lines.insert(i + 1, '| X课程 U5-L4 / 确认① / P2复核 / 真机依据 | [P2复核与定稿记录](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U5-L4_P2复核与定稿记录.md)（2026-10-26①通过；文稿复核完成，整课②依据待齐，③暂不登记） |\n')
                    break
            else:
                raise AssertionError('索引锚点缺失')
            text = ''.join(lines)
        elif path.name == 'CHANGELOG.md':
            entry = '''## 2026-10-26 · U5-L4确认①通过与P2复核

- 登记用户确认《语音会话管理》当前内容定稿、确认①通过，并按指令进入P2；不将设计确认代记为整课真机确认②或确认③。
- 完成目标、知识承接、控制逻辑、练习评价、学生表达及收尾复核，形成P2记录和剩余真机依据清单；文稿未发现需再修订的问题。
- Notebook原字节及执行信息保留，生成器反向同步用户第7、15格最后的文字调整。用户已报告的重复启动与有限等待结果保留为局部依据。
- 联动教师确认栏、计划、规则与导航；未进入P3。本地提交，推送由用户手动完成。

'''
            text = text.replace('# 更新日志\n', '# 更新日志\n\n' + entry, 1)
        elif path.name in ['_README.md', 'README.md', 'X课程开发计划-v4.md', 'X课程大纲-v4.md']:
            lines = text.splitlines(keepends=True)
            replaced = False
            for i, line in enumerate(lines):
                if 'U5-L4于2026-10-26按用户反馈修订为' in line:
                    prefix = '> **U5-L4确认①与P2（2026-10-26）**：' if line.startswith('>') else '- **U5-L4确认①与P2（2026-10-26）**：'
                    lines[i] = prefix + status + '\n'
                    replaced = True
            assert replaced, path
            text = ''.join(lines)
            if path.name == 'README.md':
                text = text.replace('（27格现稿；含教学取舍、状态机解释、逐格测试和待确认清单）',
                    '（27格定稿；确认①通过，逐格测试及整课②待补项见[P2记录](03_X课程项目/实验验证/U5-L4_P2复核与定稿记录.md)）')
        elif path.name == 'notebook开发规则.md':
            lines = text.splitlines(keepends=True)
            for i, line in enumerate(lines):
                if line.startswith('| `03_X课程项目/notebooks/U5-L4_语音问答闭环.ipynb`'):
                    lines[i] = '| `03_X课程项目/notebooks/U5-L4_语音问答闭环.ipynb`（课内标题：语音会话管理） | U5·L4 | 🟡 **确认①通过；P2复核中（2026-10-26），整课②依据待齐** | 27格（18 md/9 code），9个STEP。学生设计稿定稿，主稿未改；生成器同步用户最后两处文字调整。目标、知识与控制逻辑、练习评价的文稿复核完成。重复启动与有限等待已有用户局部实测，回调/打断/取消/管理函数启停及最终终态等按P2清单补齐依据，③暂不登记；未进入P3。 |\n'
                elif line.startswith('| U5-L4 | 按输入输出解释问答功能'):
                    lines[i] = line.replace('第二轮稿待新确认①②', '确认①通过；P2复核中，整课②依据待齐')
                elif line.startswith('| U5-L4 | 功能过程'):
                    lines[i] = line.replace('第二轮稿待验证', '当前稿①通过，整课真机依据待齐')
            text = ''.join(lines).replace('## 7. 变更记录', '## 7. 变更记录\n\n- 2026-10-26 **U5-L4确认①与P2复核**：' + status, 1)
        assert text != path.read_text(encoding='utf-8'), f'未更新：{path}'
        save(path, text)

    digest = baseline[0]['sha256']
    report = '''# U5-L4 语音会话管理｜P2复核与定稿记录

日期：2026-10-26。审定对象：[当前Notebook](../notebooks/U5-L4_语音问答闭环.ipynb)，27格（18 Markdown、9代码）。格号从1计数，包含Markdown格。

## 当前结论

用户明确指令：“确定U5-L4当前内容定稿，通过确认①，进入phase 2”。据此登记**确认①通过、学生设计稿定稿，并按授权开展P2复核**。本轮完成文稿与控制逻辑审查，未发现需要再次修改学生材料的问题。

现有记录包含用户局部真机反馈，尚未见对当前整课正常路径的确认②结论。**当前为P2复核中：文稿复核完成，整课真机依据待齐；确认③暂不登记，未进入P3。** 这一区分按现行[开发规则](../../02_共创规则与上下文/notebook开发规则.md)§1执行；本轮遵照用户指令先推进可独立完成的复核，不推定未报告的实验已经通过。

Notebook本轮原字节保留，未改代码、Markdown、执行信息或元数据。用户在第7格补充旧Notebook的定位说明、第15格调整语音打断描述，均作为当前定稿原样保留；生成器已据此反向同步。无须再确认整份设计。

Notebook SHA256：`DIGEST`。输入指纹、静态与控制分支检查见[本轮日志](../../../../99-task-contexts/20261026-U5L4确认①与P2复核/02-产出清单与状态日志.md)。

## 一、课程目标、活动与评价

| 目标 | 知识与操作 | 评价证据 | 复核结论 |
|---|---|---|---|
| 1 按输入输出解释采音、转写、生成、合成、播放，说明持续问答 | 第2～3格；STEP02追问、STEP05打断与继续提问 | 第26格检查点1、解释题1及问答记录 | 功能关系清楚；未把chat封装画成必须逐步结束的严格串行，也未要求取得内部阶段返回值 |
| 2 说明句柄用途、读取状态与判断结束 | 第4～6格；STEP02～05保存句柄、标识、有限等待、回调、取消 | 检查点2、评价1～3、任务信息与终态记录 | 返回对象与最终结果数据分清；done()、wait和cancel的含义、执行顺序与局限一致 |
| 3 画出转换条件、管理启停并防止重复启动 | 第17～22格；STEP06～09管理函数、命令操作、补条件、收尾 | 检查点3、评价4、解释题2、应用状态记录 | 应用状态参与实际分支，任务终态决定重开；第23格保留False待学生替换，教师答案在确认文档§5 |

三目标均有知识、实践和评价支撑，未发现Notebook内容遗漏或评价无法从本课取得证据的情况。第27格是模型部署的概念拓展，按教师建议课后阅读，不增加端侧部署操作任务。

## 二、知识承接、技术事实与学生表达

1. 前置经验来自L1录音/识别与回调、L2音频合成及任务等待、L3持续聊天和人设。L3变量名task与本课chat_task的区别已说明。未引入U7线程、锁或并发调度，也未使用recognize()。
2. TaskHandle[None]表示返回句柄而没有最终结果数据；wait(timeout)等待终态或超时返回当前状态，返回后才执行赋值与打印。RUNNING反映整个会话，不等于正在生成或正在播报。
3. cancel()返回请求提交情况，不直接等同结束；状态回调接收句柄，注册即观察当前状态，后续绑定同一任务。听、说或安静不必触发新的任务状态，语音打断的效果以现场记录为据。
4. 开始、查看、停止对应command文字和运行代码格；正文已补保存句柄、重复启动标识比较及旧任务处理步骤。参考答案留教师文档，学生4.3继续补写and/or条件，done()带括号且空值检查在前。
5. 状态机采用三个应用状态；每次操作前后核对SDK任务。取消尚未完成时保留句柄、拦截重开，失败先显示错误并按课堂指引检查。管理函数由手动运行推动，应用状态不会自动随后台变化刷新。
6. 仅使用音频能力，未发运动命令；初始化覆盖句柄的风险、停止等待超时、最终终态检查均就近说明。没有额外必发附件；旧句柄完全丢失的处理交教师按现场维护方式进行，未宣称有未核实的句柄找回接口。

知识、语言与操作安排未发现需要向用户提交修改方案的问题。后续P3应保留教师审阅文档的45分钟安排：5/8/12/15/5分钟，连接课前完成；服务等待或轮换较慢时另排操作时间，保留终态收尾。

## 三、已有真机依据及尚待补齐的范围

**已有依据来自用户反馈：**

- 重跑STEP02时，提示保留原句柄，任务标识相同，SDK状态为RUNNING，支持重复启动拦截。
- STEP03将wait与后续打印分开执行，返回状态、当前状态均为RUNNING，done()为False，支持有限等待与持续任务的区别。

本地9格代码当前无执行输出。输出为空不能证明未做真机测试，本轮据已提供的反馈记录范围，不推定其他步骤未测试或已通过。如下项如已完成，只需补结论与异常记录；无须为生成新记录重复制造实验。

| 待补依据 | 对应格/STEP | 需要记录 |
|---|---|---|
| 当前环境下连续问答、代码格退出后任务继续 | 8～12，STEP01～03 | 版本与连接、至少两次问答、任务标识和状态 |
| 回调登记与后续输出 | 14，STEP04及后续取消 | 是否立即输出当前状态、取消时的输出及Notebook显示位置；不要求看到完整状态序列 |
| 语音打断与程序取消的区别 | 15～16，STEP05 | 播报是否停止、是否能继续提问；cancel返回、wait返回和done()；打断未生效照实记录 |
| 管理函数启停与终态后重开 | 19～21，STEP06～07 | 重复开始保留标识，取消未结束时拦截，终态后新标识与问答；取消很快时直接记实际终态 |
| 补写条件及最终收尾 | 22～25，STEP08～09 | 查看刷新后判断使用中False、未结束False、终态且待机True；最后确认新启动会话已结束 |

逐格细目沿用[教师审阅与真机验证建议](U5-L4_教学审阅与真机验证建议.md)§4，不新增故障演练，不要求为观察CANCELLING人为拖延取消。确认②由用户作出，助手不补写现场输出。

## 四、P2最终审定的后续处理

1. 当前确认①已通过，按用户指令完成P2文稿复核，不再改动已确认主稿。
2. 补齐当前整课真机确认②依据后，核对是否出现接口、运行顺序或输出解释问题。若发现问题，按P2约定先给修改方案；未发现问题则登记③通过，提示可以进入P3。
3. 本轮不编写P3教学设计，不推进P4/P5，不代记任何后续确认。
'''.replace('DIGEST', digest)
    save(RECORD, report)
    print('已登记确认①，形成P2复核记录；Notebook未改，生成器同步第7、15格，整课②依据待齐。')


if __name__ == '__main__':
    main()
