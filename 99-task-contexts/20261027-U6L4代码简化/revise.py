"""按初学者阅读需要简化L4学生代码；不连接机器人。"""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import re
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = '05-internal-materials/vocational-planning/03_X课程项目'
NB = PROJ + '/notebooks/U6-L4_动作编排.ipynb'
GEN = PROJ + '/_gen_L24.py'
REPORT = PROJ + '/实验验证/U6_单元重构与动作编排核验.md'
RULE = '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md'


def backup(rel):
    path = ROOT / rel
    target = TASK / 'before' / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(path.read_bytes())
    return path.read_text(encoding='utf-8')


def add_note(text, note):
    heading = re.search(r'^# [^\n]+\n', text, re.M).group()
    return text.replace(heading, heading + '\n' + note + '\n', 1)


def main():
    assert not (TASK / '修改清单.json').exists(), '已修订，不覆盖基线'
    raw = backup(NB)
    doc = json.loads(raw)
    sources = {
        7: '''**STEP 01：** 连接设备并查看内置动作

先读取清单。选择教师确认可用的动作，保留清单实际返回的ID，不把整数编号或界面名称自行转换成SDK ID。

`action_ids`用普通循环保存动作ID，供STEP 02核对。`active_motion = None`表示本课还没有发起动作任务；发起任务后，这个变量保存当前句柄。`plan_ready`记录素材是否检查通过，`run_log`保存本轮执行结果。

本格在本课开始时运行一次。中断试演后保留当前连接与句柄，先检查任务和设备，不要靠重跑本格重新初始化。''',
        8: '''from boosteros.robots.booster import BoosterRobot
from boosteros.types import TrajectoryData

robot = BoosterRobot()
active_motion = None
plan_ready = False
run_log = []

actions = robot.list_actions()
action_ids = []
print("机器人：", robot.robot_info.model, robot.robot_info.serial_number)
print("当前模式：", robot.get_mode())
for action in actions:
    action_ids.append(action.id)
    print(action.id, action.type, action.duration, action.interruptible)''',
        9: '''### 4.1 写出本次程序执行清单

每个小列表按顺序填写“素材类型、对应文件或ID”。`trajectory`表示录制轨迹，`action`表示内置动作。先按本组方案替换示例；`hand_wave`、`bow`也要在本机清单中存在并经教师确认，才能使用。作品应为3～5步，同时包含本组录制轨迹和内置动作。

**STEP 02：** 检查素材并读入轨迹

本格不执行运动。`step[0]`取素材类型，`step[1]`取文件名或ID。检查通过后，程序把类型、文件名或ID、执行所需数据依次放入`prepared_steps`。内置动作的数据就是ID；录制动作的数据是读回的轨迹对象。

程序每次先将`plan_ready`设为`False`，只有清单内全部素材检查通过，才改为`True`。文件读取报错、ID不存在或素材类型未接入时，先处理问题，不能继续STEP 03。动作工坊片段不能擅自写成`action`或`trajectory`。

修改文件、ID或动作顺序后，重新运行本格，再进行试演。''',
        10: '''plan_ready = False
steps = [
    ["action", "hand_wave"],
    ["trajectory", "my_action_v1.btraj"],
    ["action", "bow"],
]
prepared_steps = []

if len(steps) < 3 or len(steps) > 5:
    print("请将作品安排为3～5步")
else:
    for step in steps:
        source = step[0]
        resource = step[1]
        if source == "trajectory":
            data = TrajectoryData.load(resource)
            if not data.points or data.duration.seconds <= 0:
                print("轨迹没有有效的动作数据：", resource)
                break
        elif source == "action":
            if resource not in action_ids:
                print("本机动作清单中没有：", resource)
                break
            data = resource
        else:
            print("本次程序未接入这种素材：", source)
            break
        prepared_steps.append([source, resource, data])

    if len(prepared_steps) == len(steps):
        plan_ready = True
        print("全部素材检查通过，尚未发起运动")''',
        11: '''### 4.2 试演并记录每一步

`for step in prepared_steps`依次取出准备好的动作。`step[0]`、`step[1]`、`step[2]`分别是素材类型、文件名或ID、执行所需数据。程序根据类型调用`execute_trajectory()`或`do_action()`，把当前任务句柄保存在`active_motion`中。

`wait(timeout=45.0)`每步最多等待45秒，教师应根据所选动作时长调整。返回`SUCCEEDED`才继续下一步；其他状态都停止后续启动。超时不会自动停止机器人，此时保留句柄，由教师检查仍在运行的任务。

`try`中的SDK调用若抛出`RuntimeError`，例如机器人正在执行其他动作，`except`会打印错误并用`break`退出循环。文件读取等错误仍保留Python原本的报错信息，便于按提示检查。

`run_log`按执行顺序记录素材来源、文件名或ID、状态。每次试演前先保存上一轮记录；重新运行STEP 03会清空本轮日志。

**STEP 03：** 经教师检查后试演

<font color="red">提示：当前应为行走模式，教师确认清单顺序、动作衔接与周围空间。先完成STEP 02，再运行本格；异常中断后先核对`active_motion`和设备状态，不能直接重跑。</font>''',
        12: '''run_log = []
if not plan_ready:
    print("请先完成STEP 02的素材检查")
elif active_motion is not None and not active_motion.done():
    print("上一任务仍未结束，请教师检查，暂不重新试演")
elif robot.get_mode() != "walk":
    print("请先按教师要求进入行走模式")
else:
    for step in prepared_steps:
        source = step[0]
        resource = step[1]
        data = step[2]
        try:
            if source == "trajectory":
                active_motion = robot.execute_trajectory(data)
            else:
                active_motion = robot.do_action(data)
            status = active_motion.wait(timeout=45.0)
        except RuntimeError as error:
            print("本步发生错误，不启动后续动作：", error)
            run_log.append([source, resource, "调用或等待失败"])
            break

        print(resource, "任务状态：", status)
        run_log.append([source, resource, status])
        if status != "SUCCEEDED":
            print("本步未成功完成，不启动后续动作")
            break''',
        13: '''**STEP 04：** 读日志，补充现场观察

每条记录依次保存“来源、素材、结果”。`row[0]`、`row[1]`、`row[2]`取出这三个内容。没有开始调用的步骤不会出现在日志中，应在作品记录里标为“未执行”；“调用或等待失败”也不能记作完成。

任务状态全部为成功时，仍需观察节奏、首尾姿态和动作间过渡是否符合设计。''',
        14: '''print("来源 | 素材 | 结果")
for row in run_log:
    print(row[0], row[1], row[2], sep=" | ")''',
    }
    for number, source in sources.items():
        cell = doc['cells'][number - 1]
        if cell['cell_type'] == 'code':
            ast.parse(source)
            cell['execution_count'] = None
            cell['outputs'] = []
        cell['source'] = (source.strip() + '\n').splitlines(keepends=True)
    (ROOT / NB).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    gen_before = backup(GEN)
    tree = ast.parse(gen_before)
    lines = gen_before.splitlines(keepends=True)
    appends = [node for node in tree.body if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
               and isinstance(node.value.func, ast.Attribute) and isinstance(node.value.func.value, ast.Name)
               and node.value.func.value.id == 'cells' and node.value.func.attr == 'append']
    assert len(appends) == len(doc['cells'])
    for node, cell in reversed(list(zip(appends, doc['cells']))):
        lines[node.lineno - 1:node.end_lineno] = ['cells.append(' + repr(cell) + ')\n']
    gen_after = ''.join(lines)
    ast.parse(gen_after)
    (ROOT / GEN).write_text(gen_after, encoding='utf-8', newline='\n')

    text = backup(REPORT)
    text = text.replace('每一步只有在`done()`为真且等待返回`SUCCEEDED`时，才启动下一步', '每一步只有等待返回`SUCCEEDED`时，才启动下一步（成功状态已是终态）；`done()`用于重跑前核对旧句柄')
    text = text.replace('检查失败时不保留可执行的部分清单；修改清单后需要重新检查；未结束的旧句柄与运动任务会阻止重开。模拟只核验这些程序分支，不代替真机。', '检查失败时`plan_ready`保持False，不执行部分清单；修改清单后按步骤重新检查。旧句柄未结束时拒绝重跑；其他运动占用交SDK拒绝调用，由一处`except RuntimeError`提示并退出。取消清单签名、全局变量查询、lambda筛选、enumerate编号及计时，日志改为来源/素材/结果三列。模拟只核验程序分支，不代替真机。')
    text = text.replace('- [ ] 已有运动任务或本轮句柄未结束时拒绝重开；失败/取消/超时不继续下一步。', '- [ ] 本轮句柄未结束时拒绝重开；其他运动任务占用时SDK报错可被提示并退出；失败/取消/超时不继续下一步。')
    note = '''> **L4代码简化（2026-10-27）**：按用户反馈，18格/4代码格不变，STEP 01～04改为普通循环、列表索引与条件判断；只保留一处RuntimeError捕获。初始化、素材检查、执行、日志说明同步，去掉计时及复杂签名判断。检查代码不再自动判断是否同时使用两类素材，由作品表和教师检查核对。修改清单后须重新运行STEP 02，不再声称自动发现任意手改；连接格不作为任务恢复手段。新代码待真机补验，不登记新的确认。'''
    text = add_note(text, note)
    (ROOT / REPORT).write_text(text, encoding='utf-8', newline='\n')

    notes = {
        'CHANGELOG.md': '''## 2026-10-27 · 简化U6-L4学生编排代码

- STEP 01～04改用普通循环、列表与索引，删除globals、lambda、enumerate、清单签名、计时和复杂日志；不再主动抛出各类异常，只保留SDK调用的RuntimeError捕获。
- 保留素材全部检查后再运行、模式检查、旧任务未结束时拒绝重跑，以及仅SUCCEEDED才进入下一步；明确超时不取消任务。素材来源与3～5步作品要求由设计表和教师共同核对。
- 同步Notebook说明、日志读取、生成器及教师核验记录。18格/4代码格不变；模拟检查不代替真机，仍待①②。本地提交，推送由用户执行。''',
        '05-internal-materials/vocational-planning/README.md': '> **U6-L4更新（2026-10-27）**：学生编排程序已简化为普通循环、列表索引和条件判断，只保留一处SDK RuntimeError捕获；预检、等待成功与旧任务处理保留，计时和复杂日志移除。18格/4代码格不变，生成器及[核验说明](03_X课程项目/实验验证/U6_单元重构与动作编排核验.md)同步；受影响内容仍待真机补验。',
        RULE: '> **U6-L4初学者代码（2026-10-27）**：18格/4代码格不变，连接、素材准备、执行与日志改为普通循环和列表索引；移除globals/lambda/enumerate/清单签名/计时，保留plan_ready、旧句柄done检查、模式与SUCCEEDED判断及一处RuntimeError捕获。清单修改后按步骤重检；两类素材要求由作品设计与教师核对；Notebook和_gen_L24.py同步，仍待①②。',
    }
    workspace_patch, staged_patch = [], []
    for rel, note in notes.items():
        before = backup(rel)
        after = add_note(before, note)
        (ROOT / rel).write_text(after, encoding='utf-8', newline='\n')
        workspace_patch.extend(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), fromfile='a/' + rel, tofile='b/' + rel))
        base = subprocess.check_output(['git', 'show', 'HEAD:' + rel], cwd=ROOT).decode('utf-8').replace('\r\n', '\n')
        target = add_note(base, note)
        staged_patch.extend(difflib.unified_diff(base.splitlines(keepends=True), target.splitlines(keepends=True), fromfile='a/' + rel, tofile='b/' + rel))
    (TASK / '工作区增量.patch').write_text(''.join(workspace_patch), encoding='utf-8', newline='\n')
    (TASK / '提交增量.patch').write_text(''.join(staged_patch), encoding='utf-8', newline='\n')
    manifest = {'date': '2026-10-27', 'notebook': NB, 'generator': GEN, 'report': REPORT,
                'changed_cells': list(sources), 'cells': len(doc['cells']),
                'notebook_before_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(),
                'notebook_after_sha256': hashlib.sha256((ROOT / NB).read_bytes()).hexdigest(),
                'notes': list(notes), 'robot_commands_executed': False, 'new_confirmations': []}
    (TASK / '修改清单.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'cells': len(doc['cells']), 'changed_cells': list(sources)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
