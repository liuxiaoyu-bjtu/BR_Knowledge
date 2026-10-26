"""P2静态与控制分支复核；不导入SDK，不连接机器人。"""
from pathlib import Path
import ast
import contextlib
import difflib
import hashlib
import io
import json
import re
import runpy
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
NB = PROJ / 'notebooks/U5-L4_语音问答闭环.ipynb'
GEN = PROJ / '_gen_L20.py'
GUIDE = PROJ / '实验验证/U5-L4_教学审阅与真机验证建议.md'
RECORD = PROJ / '实验验证/U5-L4_P2复核与定稿记录.md'


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, check=True)


class Task:
    serial = 0
    def __init__(self, status='RUNNING', accepted=True, wait_next=None):
        Task.serial += 1
        self.trace_id = f'offline-only-{Task.serial}'
        self.status = status
        self.accepted = accepted
        self.wait_next = wait_next
        self.error = 'offline-error' if status == 'FAILED' else None
        self.cancels = 0
        self.waits = 0
    def done(self):
        return self.status in {'SUCCEEDED', 'FAILED', 'CANCELLED'}
    def cancel(self):
        self.cancels += 1
        return self.accepted
    def wait(self, timeout=None):
        self.waits += 1
        if self.wait_next is not None:
            self.status, self.wait_next = self.wait_next, None
        return self.status


class Speech:
    def __init__(self):
        self.calls = []
    def chat(self, **kwargs):
        task = Task()
        self.calls.append((task, kwargs))
        return task


def control_checks(source):
    tree = ast.parse(source)
    definition = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'manage_chat')
    speech = Speech()
    env = {'speech': speech, 'PROMPT': 'offline only', 'ChatConfig': lambda **kw: kw}
    exec(compile(ast.Module(body=[definition], type_ignores=[]), '<Notebook-manage_chat>', 'exec'), env)
    manage = env['manage_chat']
    cases = []
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        task, state = manage('开始', None, '待机')
        assert state == '会话已发起' and len(speech.calls) == 1
        cases.append('无旧任务时创建并保存句柄')
        same, state = manage('开始', task, '待机')
        assert same is task and state == '会话已发起' and len(speech.calls) == 1
        cases.append('应用旧值为待机但任务仍运行时拦截重复启动')
        cancelling = Task('CANCELLING')
        same, state = manage('开始', cancelling, '待机')
        assert same is cancelling and state == '停止请求已发出' and len(speech.calls) == 1
        cases.append('SDK取消中时拦截重开')
        same, state = manage('停止', task, '会话已发起')
        assert same is task and state == '停止请求已发出' and task.cancels == 1 and not task.done()
        same, state = manage('开始', task, state)
        assert same is task and len(speech.calls) == 1
        same, state = manage('停止', task, state)
        assert same is task and task.cancels == 1 and task.waits == 2
        cases.append('取消请求已提交但任务未结束时保留句柄、拦截重开、再次停止仅等待')
        refused = Task(accepted=False)
        same, state = manage('停止', refused, '会话已发起')
        assert same is refused and state == '会话已发起' and not refused.done()
        cases.append('取消请求未提交成功时保留原任务和应用状态')
        fast = Task(wait_next='CANCELLED')
        same, state = manage('停止', fast, '会话已发起')
        assert same is fast and state == '待机' and fast.done()
        fresh, state = manage('开始', same, state)
        assert fresh is not fast and state == '会话已发起' and len(speech.calls) == 2
        cases.append('取消后确认终态才恢复待机并创建新任务')
        failed = Task('FAILED')
        same, state = manage('查看', failed, '会话已发起')
        assert same is failed and state == '待机' and 'offline-error' in output.getvalue()
        cases.append('失败终态显示错误并在查看时刷新应用状态')
        same, state = manage('停止', None, '待机')
        assert same is None and state == '待机' and len(speech.calls) == 2
        cases.append('无任务时停止不创建新任务')
    return cases


def main():
    baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(NB.read_bytes()).hexdigest() == baseline[0]['sha256'], '已确认Notebook发生变化'
    notebook = json.loads(NB.read_text(encoding='utf-8'))
    codes = [(i, c) for i, c in enumerate(notebook['cells'], 1) if c['cell_type'] == 'code']
    assert len(notebook['cells']) == 27 and len(codes) == 9
    for i, cell in codes:
        ast.parse(''.join(cell['source']), filename=f'cell-{i}')
    generated = runpy.run_path(str(GEN), run_name='verify_only')['cells']
    assert len(generated) == 27
    assert all((a['id'], a['cell_type'], a['source']) == (b['id'], b['cell_type'], b['source'])
               for a, b in zip(notebook['cells'], generated))
    branches = control_checks(''.join(notebook['cells'][18]['source']))
    guide = GUIDE.read_text(encoding='utf-8')
    expression = re.search(r'^can_start = (.+)$', guide, flags=re.M).group(1)
    condition = compile(expression, '<teacher-start-condition>', 'eval')
    condition_count = 0
    for state in ['待机', '会话已发起', '停止请求已发出']:
        for status in [None, 'PENDING', 'RUNNING', 'CANCELLING', 'SUCCEEDED', 'FAILED', 'CANCELLED']:
            task = None if status is None else Task(status)
            expected = state == '待机' and (status is None or status in {'SUCCEEDED', 'FAILED', 'CANCELLED'})
            assert eval(condition, {'__builtins__': {}}, {'app_state': state, 'chat_task': task}) is expected
            condition_count += 1
    assert notebook['cells'][22]['source'][0].startswith('can_start = False')
    assert '设计确认①：2026-10-26用户明确确认通过' in guide
    assert '真机确认②：待确认' in guide

    chunks = []
    for item in baseline[3:]:
        rel = item['path']
        a = (TASK / 'before' / rel).read_text(encoding='utf-8').splitlines(keepends=True)
        b = (ROOT / rel).read_text(encoding='utf-8').splitlines(keepends=True)
        chunks.extend(difflib.unified_diff(a, b, fromfile='a/' + rel, tofile='b/' + rel))
    patch = TASK / '共享文档本轮增量.patch'
    patch.write_text(''.join(chunks), encoding='utf-8', newline='\n')
    git('apply', '--reverse', '--check', '--', patch.relative_to(ROOT).as_posix())
    links = 0
    for path in [GUIDE, RECORD, TASK / '02-产出清单与状态日志.md']:
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if re.match(r'^https?://', target):
                continue
            destination = (path.parent / target.split('#')[0]).resolve()
            if destination != TASK / '验证结果.json':
                assert destination.exists(), (path, target)
            links += 1
    result = {'date': '2026-10-26', 'passed': True, 'notebook_sha256': baseline[0]['sha256'],
              'notebook_bytes_unchanged': True, 'cells': 27, 'code_cells_parsed': 9,
              'generator_matches_current_source': True, 'offline_control_cases': branches,
              'start_condition_cases': condition_count, 'local_links_checked': links,
              'shared_increment_patch_reverse_check': True, 'robot_connected': False,
              'confirmation_1': '用户明确通过', 'confirmation_2': '整课依据待齐',
              'confirmation_3': '暂不登记；P2文稿复核完成'}
    (TASK / '验证结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'通过：主稿原字节不变，27格生成器一致，9格语法、{len(branches)}组离线控制场景、21组条件与{links}处本地链接。')
    if '--stage' not in sys.argv:
        return
    paths = [NB, GEN, GUIDE, RECORD] + [TASK / name for name in [
        'records.py', 'verify_archive.py', '02-产出清单与状态日志.md', '基线.json',
        '验证结果.json', '共享文档本轮增量.patch',
    ]]
    relative = {p.relative_to(ROOT).as_posix() for p in paths}
    existing = set(filter(None, git('diff', '--cached', '--name-only', '-z').stdout.decode('utf-8').split('\0')))
    assert not existing - relative, '暂存区含其他文件，停止，不改变其状态。'
    git('add', '--', *sorted(relative))
    staged = set(filter(None, git('diff', '--cached', '--name-only', '-z').stdout.decode('utf-8').split('\0')))
    assert staged == relative
    git('diff', '--cached', '--check', '--', '.', ':(exclude)' + patch.relative_to(ROOT).as_posix())
    print(git('-c', 'core.quotepath=false', 'diff', '--cached', '--stat').stdout.decode('utf-8'))
    print('定向暂存完成，未提交、未推送。')


if __name__ == '__main__':
    main()
