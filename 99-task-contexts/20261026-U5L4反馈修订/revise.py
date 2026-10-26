"""以用户现稿为基础修订说明，保留代码、输出及其他单元格属性。"""
from pathlib import Path
import copy
import hashlib
import json

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
NB = PROJ / 'notebooks/U5-L4_语音问答闭环.ipynb'
GUIDE = PROJ / '实验验证/U5-L4_教学审阅与真机验证建议.md'
GEN = PROJ / '_gen_L20.py'
SHARED = [ROOT / p for p in [
    'AGENTS.md', 'INDEX.md', 'CHANGELOG.md', '05-internal-materials/_README.md',
    '05-internal-materials/vocational-planning/README.md',
    '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md',
]] + [PROJ / 'X课程开发计划-v4.md', PROJ / 'X课程大纲-v4.md']


def save(path, text):
    path.write_text(text, encoding='utf-8', newline='\n')


def main():
    baseline_path = TASK / '基线.json'
    assert not baseline_path.exists(), '本轮修订已执行；避免覆盖用户后续编辑。'
    files = [NB, GUIDE, GEN] + SHARED
    baseline = []
    for path in files:
        rel = path.relative_to(ROOT)
        data = path.read_bytes()
        backup = TASK / 'before' / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(data)
        baseline.append({'path': rel.as_posix(), 'sha256': hashlib.sha256(data).hexdigest()})
    save(baseline_path, json.dumps(baseline, ensure_ascii=False, indent=2) + '\n')
    notebook = json.loads(NB.read_text(encoding='utf-8'))
    original = copy.deepcopy(notebook)

    def set_cell(number, source):
        cell = notebook['cells'][number - 1]
        assert cell['cell_type'] == 'markdown'
        cell['source'] = (source.strip() + '\n').splitlines(keepends=True)

    set_cell(1, ''.join(notebook['cells'][0]['source']).replace('语音问答闭环', '语音会话管理'))
    set_cell(2, '''
## 一、同一个会话中的连续问答

L1 观察了录音与语音识别，L2 将文字合成为语音，L3 用 `chat()` 让机器人连续回答问题。机器人说完一个回答后，还可以接着听下一个问题；一轮问答结束时，整个会话通常仍在继续。

连续运行两次启动会话的代码格时，程序应保留正在使用的会话，避免重复启动。运行停止会话的代码格后，还要确认旧任务已经结束，才能再次启动。本课通过分别运行“启动会话、查看状态、停止会话”的代码格，管理同一个持续语音会话。
''')
    set_cell(3, ''.join(notebook['cells'][2]['source']).replace(
        '## 二、从语音问答到任务句柄', '## 二、持续语音会话的句柄与状态'))
    set_cell(4, '''
### 2.2 `chat()` 返回了什么

L3 中的 `task = speech.chat(...)`，把返回的对象保存在 `task` 中。这个对象叫**任务句柄**：程序凭它查看任务、等待结束或请求取消。可以把句柄理解为这次任务的办理凭据；保留它，才能继续查询和管理这次任务。本课使用变量名 `chat_task` 保存聊天任务的句柄。

官方将这个返回类型写成 `TaskHandle[None]`：

- `TaskHandle` 表示返回的是任务句柄。
- 方括号中的 `None` 表示任务完成时不提供结果数据。机器人仍会说话，`chat()` 也确实返回了句柄。

L2 的 `synthesize()` 会产生音频数据，成功后用 `result()` 取出音频。`chat()` 返回的句柄用于管理整个持续会话，使用 `wait()` 等待任务结束。机器人在会话中说出的回复，不会作为这个句柄的文字结果返回。

句柄的 `trace_id` 是本次任务的追踪标识。后面的程序打印它，便于比较重复运行启动格时是否保留旧任务，以及旧任务结束后再次启动时是否创建了新任务。
''')
    cell7 = ''.join(notebook['cells'][6]['source'])
    a = cell7.index('<font color="red">提示：')
    b = cell7.index('初始化中的 `chat_task = None`')
    set_cell(7, cell7[:a] + '''<font color="red">提示：</font>初始化格只在确认没有遗留任务时运行一次。会话启动后，重新执行 `chat_task = None` 会丢失原句柄，后台任务却可能仍在运行。需结束旧任务时，先保留句柄并按下列步骤处理。

> **补充操作：结束遗留会话**
>
> 1. 回到启动旧会话的 Notebook。如果原代码格仍在 `wait()` 中运行，先中断该代码格，再查看它的取消与收尾输出。
> 2. L3 使用变量 `task` 保存句柄。若该变量仍保留旧句柄，可在原 Notebook 的临时代码格运行：
>
>    ```python
>    task.cancel()
>    task.wait(timeout=5.0)
>    print("旧任务状态：", task.status, "；是否结束：", task.done())
>    ```
>
>    若旧会话来自本课，使用它原来所在内核中的 `chat_task`，将以上代码的 `task` 换为 `chat_task`。只有 `done()` 为 `True` 才能继续初始化；仍为 `False` 时保留句柄，由教师继续检查。
> 3. 若原句柄已被覆盖，且没有其他变量保存它，暂停实验，由教师按设备现场维护流程处理遗留会话，确认退出后再继续。重启内核、清空变量或中断代码格，都不能单独证明机器人端任务已经结束。

''' + cell7[b:])
    cell9 = ''.join(notebook['cells'][8]['source'])
    first = '才创建新会话。'
    assert first in cell9
    set_cell(9, cell9.replace(first, first + '\n\n下一格的 `chat_task = speech.chat(...)` 是保存句柄的赋值语句：等号右侧发起会话并返回句柄，左侧的变量 `chat_task` 保存它。后续查看、等待和取消都通过这个变量操作同一个任务。'))
    set_cell(11, '''
**STEP 03：** 读取状态，并进行一次有限等待。

`wait(timeout=2.0)` 会阻塞当前代码格，最多等待任务结束两秒。任务提前结束时，等待会提前返回；达到两秒上限时，返回当时的状态。`wait()` 返回后，程序才把这个状态保存到 `observed_status`，再执行后面的 `print()`。

会话持续运行时，等待返回值和当前状态都可能为 `RUNNING`，`done()` 为 `False`：本次等待已经结束，会话任务仍未结束。两秒是等待上限，不是一轮问答的耗时。

`observed_status` 保存本次等待返回的状态，`chat_task.status` 读取打印时的当前状态；两次读取之间若发生状态变化，打印结果可能不同。

记下任务标识，再次运行 STEP 02。若旧任务仍未结束，应出现“已有未结束的会话，保留原句柄”，任务标识与前一次相同。随后再提一个问题，检查原会话能否继续使用。这一步检查重复启动是否被拦截，不要求任务状态发生变化；若任务已自行结束，记录终态和错误信息，再决定是否重开。
''')
    set_cell(13, '''
### 3.3 用回调观察状态变化

**STEP 04：** 为当前句柄登记一个状态回调。

L1 把函数 `on_text(text)` 交给 SDK，收到识别文字时，由 SDK 调用它并传入文字。本课沿用这种回调方式观察任务状态：把 `on_status(task)` 登记到当前句柄后，SDK 在调用它时传入任务句柄，函数再通过 `task.status` 读取并打印状态。两种回调接收的信息不同，前者接收文字，后者接收句柄。

`add_status_change_callback()` 登记后会立即按当前状态调用一次，之后任务状态发生变化时再调用。这一格对当前句柄只运行一次，重复登记会产生重复输出。

登记完成后继续提问，再暂时保持安静，同时用 STEP 03 查看状态。听问题、回答和等待下次提问，都可能属于同一个 `RUNNING` 任务，因此不一定产生新的状态回调。到 STEP 05 取消任务时，再观察有没有后续输出；短暂状态可能来不及看到，按实际输出记录。

这个回调绑定当前任务，重新创建的任务需要另行登记。
''')
    set_cell(15, '''
### 3.4 打断说话与取消会话

**STEP 05：** 在机器人正在回答时，尝试说“停一下”。先观察当前播报是否停止，再运行 STEP 03，记录任务标识、状态和 `done()`；随后再提一个问题，检查能否继续交流。

语音打断若生效，当前播报可能停止，而整个会话仍保持 `RUNNING`、`done()` 为 `False`，任务标识也保持不变。此时仍能继续提问，说明打断播报没有结束整个会话。“停一下”是否生效受说话时机、识别和服务行为影响，请分别记录“播报是否停止”“任务是否结束”“能否继续提问”。

然后运行下一格，用 `cancel()` 请求结束整个会话。五秒是这次停止操作愿意等待的上限。若还未进入终态，保留句柄，稍后再运行 STEP 03 查看，不另开会话。
''')
    cell17 = ''.join(notebook['cells'][16]['source'])
    cell17 = cell17.replace('用户在什么时候可以操作', '在什么条件下可以执行各项操作')
    cell17 = cell17.replace('任务也可能在用户没有按“停止”时因故障结束。', '即使没有运行停止操作，任务也可能因故障结束。')
    cell17 = cell17.replace('依据表格画出状态图', '表中“开始、查看、停止”是传给管理函数的操作文字。将 `command` 设为相应文字并运行代码格，程序才会处理这次操作。\n\n依据表格画出状态图')
    set_cell(17, cell17)
    cell18 = ''.join(notebook['cells'][17]['source']).replace('再按“停止”会继续等待原任务。', '再次执行“停止”操作会继续等待原任务。')
    set_cell(18, cell18)
    set_cell(22, '''
### 4.3 补写启动条件

**STEP 08：** 将下一格的 `False` 替换为允许启动的条件表达式。需同时满足：

1. `app_state` 为“待机”。
2. 没有旧任务，或旧任务的 `done()` 返回 `True`。

用 `and` 连接这两项要求，用括号把第二项的两种情况放在一起。`done()` 是方法，需要带括号调用；`chat_task is None` 应放在这组 `or` 判断的前面，变量为空时 Python 就会跳过后面的任务检查。

每次先在 STEP 07 将 `command` 设为“查看”并运行，更新应用状态，再运行本格。分别记录会话使用中、停止请求已提交但任务尚未结束、确认结束后的判断结果。取消很快完成时，直接记录实际终态，无需设法让取消停在中间状态。

`can_start` 保存本格运行当时的判断结果，不会随后台任务自动更新；观察条件改变后需重新运行。本格只判断是否允许启动，创建任务仍通过 STEP 07 完成。
''')
    cell26 = ''.join(notebook['cells'][25]['source'])
    cell26 = cell26.replace('| 语音打断后继续提问 |', '| 尝试语音打断后查看状态，再继续提问 |')
    cell26 = cell26.replace('本次 `cancel()` 返回值：______；最终任务状态：______。',
        '语音打断观察：播报是否停止______；任务是否结束______；能否继续提问______。\n\n本次 `cancel()` 返回值：______；最终任务状态：______。')
    set_cell(26, cell26)
    assert len(notebook['cells']) == len(original['cells']) == 27
    assert all(a == b for a, b in zip(notebook['cells'], original['cells']) if a['cell_type'] == 'code')
    save(NB, json.dumps(notebook, ensure_ascii=False, indent=1) + '\n')

    # 反向同步现稿，包括用户此前修改的段落；不运行生成器覆盖 Notebook。
    lines = ['"""U5-L4 语音会话管理：2026-10-26由学生Notebook反向同步。',
             'Notebook为主稿；重建会清空输出，不用于覆盖真机记录。"""',
             'import json', 'from pathlib import Path',
             'OUT = Path(__file__).resolve().parent / "notebooks" / "U5-L4_语音问答闭环.ipynb"',
             '', 'def md(s, cell_id):',
             '    return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": s.splitlines(keepends=True)}',
             '', 'def code(s, cell_id):',
             '    return {"cell_type": "code", "id": cell_id, "metadata": {}, "execution_count": None, "outputs": [], "source": s.splitlines(keepends=True)}',
             '', 'cells = []']
    for c in notebook['cells']:
        fn = 'md' if c['cell_type'] == 'markdown' else 'code'
        lines.append(f"cells.append({fn}({''.join(c['source'])!r}, {c['id']!r}))")
    lines += ['', 'if __name__ == "__main__":',
              "    notebook = {'cells': cells, 'metadata': " + repr(notebook['metadata']) + ", 'nbformat': 4, 'nbformat_minor': 5}",
              "    OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\\n', encoding='utf-8')",
              '    print(OUT)', '']
    save(GEN, '\n'.join(lines))

    guide = GUIDE.read_text(encoding='utf-8')
    guide = guide.replace('日期：2026-10-23。对象：第二轮修订的《语音问答闭环》学生 Notebook',
        '初稿日期：2026-10-23；本轮更新：2026-10-26。对象：《语音会话管理》学生 Notebook')
    guide = guide.replace('仅对应第二轮稿', '对应当前27格稿')
    insert = '''## 0. 2026-10-26反馈修订与实测记录

课内标题改为《语音会话管理》，文件名暂保留 `U5-L4_语音问答闭环.ipynb`，现有引用继续有效。结构仍为27格、9个STEP，9格实验代码保持原样；4.3继续由学生补写，参考表达式在本文件§5。

| 反馈 | 本轮修改 | 格号 |
|---|---|---|
| “闭环”与内容不贴切；开始、停止被写成按钮 | 改课内标题；操作改为运行代码格、设置command并运行 | 1～2、17～18 |
| 第二部分标题缺少对应关系；result表述像设计旁白 | 改为“持续语音会话的句柄与状态”；解释句柄不提供聊天文字结果；核实L3变量名实际为task | 3～4 |
| 旧任务处理缺少步骤；保存句柄位置不明确 | 用引用块补原Notebook中取消、等待、核对终态的步骤，以及句柄已丢失时的处理范围；指出赋值语句 | 7、9 |
| 重复启动和有限等待的观察要求不明确 | 补同标识、保留旧句柄的预期；写明wait返回后才赋值并打印，两个状态读取时点可能不同 | 11 |
| 回调的前课回顾缺少承接 | 明确L1接收文字、本课接收句柄，再读取status；问答内部活动不一定触发状态变化 | 13 |
| “停一下”后查看状态缺少观察目的 | 先尝试打断播报，再查看标识/状态，再提问；分开记录播报、任务结束和继续问答 | 15、26 |
| 4.3补写要求不够清楚 | 写明and、or分组、done()调用、空值短路、先刷新应用状态及布尔值不会自动更新 | 22 |

**用户报告的局部真机现象：** 重跑STEP 02时提示“已有未结束的会话，保留原句柄”，任务标识不变（用户示例末四位为bff6），状态为RUNNING；将STEP 03的等待与打印分格执行，等待返回及当前状态均为RUNNING，done()为False。这与重复启动拦截、有限等待超时的设计一致。记录来自用户提供的信息，Notebook中未补写输出，未将局部观察登记为整课确认②通过。

**本轮核验范围：** 文稿、代码不变、生成器源内容一致及启动条件表达式。助手未连接机器人。旧任务取消指引及语音打断效果仍按现场实际验证；句柄完全丢失时未编造通过trace_id找回任务的接口。

'''
    guide = guide.replace('## 1. 本轮逐项处理', insert + '## 1. 前轮逐项处理')
    guide = guide.replace('再按“停止”只继续等待', '再次执行“停止”操作只继续等待')
    guide = guide.replace('不安排学生反复快速点击。', '不安排学生快速反复运行停止格。')
    guide = guide.replace('| 8 | 回答时说“停一下”，再提问 |', '| 8 | 回答时说“停一下”，运行第12格查看，再提问 |')
    guide = guide.replace('| 13 | 运行“查看”后，第23格补条件 | 使用中不放行，终态后可放行；若取消瞬间完成，直接记终态 | |',
        '| 13 | 运行“查看”后，第23格补条件 | 使用中为False，取消尚未结束为False，终态且应用刷新为待机后为True；若取消瞬间完成，直接记终态 | |')
    guide = guide.replace('先通过“查看”刷新应用状态，再判断。',
        '使用`and`连接待机条件与括号中的`or`条件。`done()`必须带括号；`chat_task is None`为真时会跳过右侧方法调用。`can_start`是计算时的结果，任务或应用状态变化后需要重算。\n\n先通过“查看”刷新应用状态，再判断。')
    guide = guide.replace('离线核验结果见本轮任务目录中的`验证结果.json`；',
        '2026-10-26文稿、源内容及条件核验结果见[本轮任务记录](../../../../99-task-contexts/20261026-U5L4反馈修订/02-产出清单与状态日志.md)；前轮控制分支检查记录继续保留；')
    save(GUIDE, guide)

    progress = 'U5-L4于2026-10-26按用户反馈修订为《语音会话管理》（课内标题），仍为27格（18 Markdown/9代码）。补旧任务处理指引、句柄赋值、重复启动与有限等待的观察要求、回调承接及语音打断记录；4.3保留学生补写，教师答案使用done()。9格代码及执行信息保留，生成器已反向同步；用户局部运行结果已记录，整课确认①②仍待完成，未进入P2。文件名保留以兼容现有链接。'
    for path in SHARED:
        text = path.read_text(encoding='utf-8')
        if path.name == 'AGENTS.md':
            text = text.replace('  - 教学设计/PPT内容/PPT/实训手册：', '  - ' + progress + '\n  - 教学设计/PPT内容/PPT/实训手册：')
        elif path.name == 'INDEX.md':
            text = text.replace('| X课程 U5-L4 / TaskHandle[None]', '| X课程 U5-L4 / 语音会话管理 / TaskHandle[None]')
            text = text.replace('（第二轮修订、逐格测试及确认清单，2026-10-23）', '（2026-10-26反馈修订；重复启动、有限等待、done()补写及逐格测试清单）')
        elif path.name == 'CHANGELOG.md':
            entry = '''## 2026-10-26 · U5-L4学生说明与实验观察要求修订

- 课内标题改为《语音会话管理》，文件名保留；将按钮描述改为运行代码格，第二部分改为“持续语音会话的句柄与状态”。
- 补旧任务取消与终态确认指引、句柄赋值说明；明确重复启动应保留标识、wait返回后再打印、回调的参数与触发、语音打断和任务取消的不同观察要求。
- 4.3继续由学生补写，细化and/or分组、done()及应用状态刷新；教师答案与测试清单同步。27格和9格实验代码、执行信息保留，生成器从用户现稿反向同步。
- 用户局部实测结果单独记录，未代记整课确认①②通过。相关大纲、计划、导航及规则同步；本地提交，推送由用户手动完成。

'''
            text = text.replace('# 更新日志\n', '# 更新日志\n\n' + entry, 1)
        elif path.name == '_README.md':
            text = text.replace('## 📂 目录结构', '> **U5-L4反馈修订（2026-10-26）**：' + progress + '\n\n## 📂 目录结构', 1)
        elif path.name == 'README.md':
            text = text.replace('- U5-L4第二轮审阅入口：', '- **U5-L4更新（2026-10-26）**：' + progress + '\n- U5-L4审阅入口：')
        elif path.name == 'notebook开发规则.md':
            text = text.replace('## 7. 变更记录', '## 7. 变更记录\n\n- 2026-10-26 **U5-L4反馈修订**：' + progress, 1)
            text = text.replace('| `03_X课程项目/notebooks/U5-L4_语音问答闭环.ipynb` | U5·L4 |', '| `03_X课程项目/notebooks/U5-L4_语音问答闭环.ipynb`（课内标题：语音会话管理） | U5·L4 |')
        elif path.name == 'X课程开发计划-v4.md':
            text = text.replace('语音问答闭环（持续会话管理）', '语音会话管理')
            text = text.replace('> **现行流程（2026-10-20）**', '> **U5-L4反馈修订（2026-10-26）**：' + progress + '\n\n> **现行流程（2026-10-20）**', 1)
        elif path.name == 'X课程大纲-v4.md':
            text = text.replace('| **4** | 语音问答闭环 |', '| **4** | 语音会话管理 |')
            text = text.replace('> **U5更新（2026-10-23）**', '> **U5-L4更新（2026-10-26）**：' + progress + '\n\n> **U5更新（2026-10-23）**', 1)
        assert text != path.read_text(encoding='utf-8'), f'未更新：{path}'
        save(path, text)
    print('已修订Notebook说明并同步生成器、教师文档及8份关联记录；9格实验代码保持不变。')


if __name__ == '__main__':
    main()
