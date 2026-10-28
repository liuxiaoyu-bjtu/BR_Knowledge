from pathlib import Path
from types import SimpleNamespace
import ast
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
COURSE = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
SPECS = {
    'U5-L4': ('语音会话管理', 20, 27, 9, [(1,1,1),(2,3,1),(4,6,2),(7,8,2),(9,12,2),(13,14,3),(15,16,3),(17,19,4),(20,21,4),(22,23,4),(24,25,5),(26,26,5),(27,27,5)]),
    'U6-L1': ('动作的来源', 21, 18, 2, [(1,2,1),(3,4,2),(5,6,3),(7,8,4),(9,10,5),(11,12,5),(13,14,6),(15,17,6),(18,18,7)]),
    'U6-L2': ('动作录制与回放', 22, 16, 4, [(1,3,1),(4,6,1),(7,8,2),(9,10,2),(11,13,2),(14,14,4),(15,15,6),(16,16,5)]),
    'U6-L3': ('视频动作训练', 23, 17, 1, [(1,2,1),(3,5,1),(6,7,2),(8,8,3),(9,10,3),(11,11,3),(12,12,4),(13,13,5),(14,15,4),(16,16,5),(17,17,6)]),
    'U6-L4': ('动作编排', 24, 18, 4, [(1,2,1),(3,5,1),(6,8,2),(9,10,2),(11,12,3),(13,14,3),(15,15,4),(16,16,5),(17,17,6),(18,18,5)]),
}
result = {'日期': '2026-10-28', '教学设计': {}, '离线保护场景': [], '本地链接': 0}
nb_by_id = {}
SECTIONS = ['一、课时目标','二、重难点','三、环节时间轴','四、教学环节详解','五、板书设计','六、学习评价']

def normalized(s):
    return re.sub(r'\s+', '', s)

for key, (title, gen, total, code_count, mappings) in SPECS.items():
    matches = list((COURSE / 'notebooks').glob(key + '_*.ipynb'))
    assert len(matches) == 1
    path = matches[0]
    rel = path.relative_to(ROOT)
    before_path = TASK / 'before' / rel
    before = json.loads(before_path.read_text(encoding='utf-8'))
    nb = json.loads(path.read_text(encoding='utf-8'))
    nb_by_id[key] = nb
    assert len(nb['cells']) == total
    assert sum(c['cell_type'] == 'code' for c in nb['cells']) == code_count
    assert {k:v for k,v in before.items() if k != 'cells'} == {k:v for k,v in nb.items() if k != 'cells'}
    changed = []
    for i, (old, new) in enumerate(zip(before['cells'], nb['cells']), 1):
        assert {k:v for k,v in old.items() if k != 'source'} == {k:v for k,v in new.items() if k != 'source'}, (key, i, 'metadata')
        if old['source'] != new['source']:
            changed.append(i)
        if new['cell_type'] == 'code':
            ast.parse(''.join(new['source']))
    allowed = {'U6-L2': [10,15], 'U6-L4': [1,4,8,11,12,13,18]}.get(key, [])
    assert changed == allowed, (key, changed)
    if not allowed:
        assert path.read_bytes() == before_path.read_bytes(), key

    tree = ast.parse((COURSE / f'_gen_L{gen}.py').read_text(encoding='utf-8'))
    mirror_cells = []
    mirror = None
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id == 'cells' and call.func.attr == 'append':
                mirror_cells.append(ast.literal_eval(call.args[0]))
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'notebook':
            mirror = ast.literal_eval(node.value)
    mirror['cells'] = mirror_cells
    assert mirror == nb, (key, 'generator')

    doc_path = COURSE / '教学设计' / f'{key}_{title}_教学设计.md'
    doc = doc_path.read_text(encoding='utf-8')
    headers = re.findall(r'^## (.+)$', doc, re.M)
    assert headers[:6] == SECTIONS
    assert '> 教学提示：' in doc
    assert '教学资源与附件' not in doc
    assert '```mermaid' in doc and '**板书1' in doc
    timeline = doc.split('## 三、环节时间轴')[1].split('## 四、教学环节详解')[0]
    slots = [(int(a), int(b)) for a,b in re.findall(r'^\|\s*(\d+)[–-](\d+)min\s*\|', timeline, re.M)]
    assert slots[0][0] == 0 and slots[-1][1] == 45 and all(a < b for a,b in slots)
    assert all(slots[i][1] == slots[i+1][0] for i in range(len(slots)-1))
    assert len(slots) == len(re.findall(r'^### 环节\d+', doc, re.M))
    goals = re.findall(r'^\d+\. (.+)$', ''.join(nb['cells'][0]['source']), re.M)
    teaching_goals = doc.split('## 一、课时目标')[1].split('## 二、重难点')[0]
    assert all(normalized(goal) in normalized(teaching_goals) for goal in goals)
    assert len(goals) == 3
    for line in doc.splitlines():
        if '【投影】' in line:
            assert '依据：' in line and '待P5-B回填' in line and '拟展示：' in line, (key, line)

    last = ''.join(nb['cells'][-1]['source'])
    if key == 'U5-L4':
        last = ''.join(nb['cells'][25]['source'])
    eval_text = re.split(r'^### \d+\.\d+ 学习评价\s*$', last, flags=re.M)[-1]
    eval_text = eval_text.split('> 参考答案')[0].split('### 5.4')[0]
    questions = re.findall(r'^\d+\. (.+)$', eval_text, re.M)
    teacher_eval = doc.split('## 六、学习评价')[1].split('## 七、')[0]
    assert all(normalized(q) in normalized(teacher_eval) for q in questions), (key, questions)
    assert len(questions) == (4 if key == 'U5-L4' else 3)

    covered = []
    for first, end, lesson in mappings:
        covered.extend(range(first, end+1))
        assert 1 <= lesson <= len(slots)
    assert covered == list(range(1, total+1)), (key, covered)
    result['教学设计'][key] = {'格数': total, '代码格': code_count, '目标': 3,
                               '评价题': len(questions), '时间轴': slots,
                               '全格覆盖': True, '生成器逐格一致': True,
                               '元数据与执行证据保留': True, '本轮修改格': changed}

class Handle:
    def __init__(self, statuses=('RUNNING','CANCELLED'), done=False, wait_error=None, accepted=True):
        self.statuses = list(statuses)
        self.status = self.statuses[0]
        self.finished = done
        self.waits = []
        self.cancel_calls = 0
        self.wait_error = wait_error
        self.accepted = accepted
    def done(self):
        return self.finished
    def wait(self, timeout=None):
        self.waits.append(timeout)
        if self.wait_error:
            raise self.wait_error
        self.status = self.statuses.pop(0) if self.statuses else self.status
        self.finished = self.status in ('SUCCEEDED','FAILED','CANCELLED')
        return self.status
    def cancel(self):
        self.cancel_calls += 1
        return self.accepted

class Robot:
    def __init__(self, handles, mode='walk', error=None):
        self.handles = list(handles)
        self.mode = mode
        self.calls = []
        self.error = error
    def get_mode(self):
        return self.mode
    def launch(self, kind, data):
        self.calls.append((kind, data))
        if self.error:
            raise self.error
        return self.handles.pop(0)
    def execute_trajectory(self, data):
        return self.launch('trajectory', data)
    def do_action(self, data):
        return self.launch('action', data)

l4 = nb_by_id['U6-L4']
student_code = ''.join(l4['cells'][11]['source'])
assert 'active_motion = None' not in student_code
assert 'active_motion = None' in ''.join(l4['cells'][7]['source'])
traj = SimpleNamespace(duration=SimpleNamespace(seconds=2.5))
steps = [['action','wave','wave'], ['trajectory','demo.btraj',traj], ['action','bow','bow']]

def run_case(name, handles, expected_calls, old=None, ready=True, mode='walk', error=None, interrupted=False):
    robot = Robot(handles, mode, error)
    ctx = {'robot': robot, 'active_motion': old, 'plan_ready': ready, 'run_log': [],
           'prepared_steps': steps, 'print': lambda *args, **kwargs: None}
    try:
        exec(compile(student_code, '<U6-L4-STEP03>', 'exec'), ctx)
        assert not interrupted
    except KeyboardInterrupt:
        assert interrupted
    assert len(robot.calls) == expected_calls, name
    if old is not None and not old.done():
        assert ctx['active_motion'] is old, name
    if expected_calls and not error:
        assert ctx['active_motion'] is handles[expected_calls-1]
    result['离线保护场景'].append(name)
    return ctx

hs = [Handle(), Handle(), Handle()]
ctx = run_case('三步等待、取消、确认CANCELLED后顺序执行', hs, 3)
assert hs[0].waits == [5.0,5.0] and hs[1].waits == [3.5,5.0] and hs[2].waits == [5.0,5.0]
assert all(h.cancel_calls == 1 for h in hs)
assert len(ctx['run_log']) == 3
run_case('旧任务未结束时保留句柄并拦截重开', [], 0, old=Handle())
run_case('清单未通过时不运动', [], 0, ready=False)
run_case('模式不符时不运动', [], 0, mode='prepare')
for status in ['RUNNING','FAILED','SUCCEEDED']:
    ctx = run_case(status + '不满足当前取消分支则停止后续', [Handle(('RUNNING',status))], 1)
    assert len(ctx['run_log']) == 1
run_case('取消请求未成功且任务仍运行时不继续', [Handle(('RUNNING','RUNNING'), accepted=False)], 1)
ctx = run_case('SDK忙状态RuntimeError保留错误记录并停止', [], 1, error=RuntimeError('busy'))
assert len(ctx['run_log']) == 1
run_case('等待异常时保留已取得句柄', [Handle(wait_error=RuntimeError('wait error'))], 1)
run_case('人工中断时保留已取得句柄', [Handle(wait_error=KeyboardInterrupt())], 1, interrupted=True)

files = list((COURSE / '教学设计').glob('U6-L*_教学设计.md'))
files += [COURSE / '教学设计/U5-L4_语音会话管理_教学设计.md', COURSE / '实验验证/U5-L4_U6_P3教学设计覆盖检查记录.md']
for path in files:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
        if '://' in target:
            continue
        actual = (path.parent / target.split('#')[0]).resolve()
        assert actual.exists(), (path, target)
        result['本地链接'] += 1

progress = (COURSE / 'X课程当前进度.md').read_text(encoding='utf-8')
lesson_rows = [line for line in progress.splitlines() if re.match(r'^\| (\[)?U[1-8]-L[1-4] ', line)]
assert len(lesson_rows) == 32, len(lesson_rows)
assert '| P3教学设计已产出，确认④待审 | 5 |' in progress
assert '| 教学设计 | 21 |' in progress
assert sum('P3教学设计已完成，待确认④' in line for line in lesson_rows) == 5
result['课程总表'] = {'逐课行': 32, '本轮P3待④': 5, '教学设计覆盖课数': 21}
result['汇总'] = {'Notebook格': sum(v[2] for v in SPECS.values()), '代码格': sum(v[3] for v in SPECS.values()),
                  '目标': 15, '评价题': 16, '思考或解释题': 14,
                  '新真机运行': False, '检查通过': True}
(TASK / '校验结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result['汇总'], ensure_ascii=False))
print('五课目标/题目/时间轴、全部格、镜像、元数据、11类离线场景与链接通过')
