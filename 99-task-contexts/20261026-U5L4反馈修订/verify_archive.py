"""核对本轮文稿、输入保留和生成器一致性；按清单归档，不连接机器人。"""
from pathlib import Path
import ast
import difflib
import json
import re
import runpy
import subprocess
import sys
import textwrap

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
NB = PROJ / 'notebooks/U5-L4_语音问答闭环.ipynb'
GEN = PROJ / '_gen_L20.py'
GUIDE = PROJ / '实验验证/U5-L4_教学审阅与真机验证建议.md'


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, check=True)


def verify():
    current = json.loads(NB.read_text(encoding='utf-8'))
    before = json.loads((TASK / 'before' / NB.relative_to(ROOT)).read_text(encoding='utf-8'))
    assert len(current['cells']) == len(before['cells']) == 27
    assert {k: v for k, v in current.items() if k != 'cells'} == {k: v for k, v in before.items() if k != 'cells'}
    code_count, changed = 0, []
    for i, (a, b) in enumerate(zip(current['cells'], before['cells']), 1):
        assert {k: v for k, v in a.items() if k != 'source'} == {k: v for k, v in b.items() if k != 'source'}, i
        if a['cell_type'] == 'code':
            assert a == b, f'代码或执行信息变化：第{i}格'
            ast.parse(''.join(a['source']))
            code_count += 1
        if a != b:
            changed.append(i)
    assert code_count == 9
    assert changed == [1, 2, 3, 4, 7, 9, 11, 13, 15, 17, 18, 22, 26], changed
    generator = runpy.run_path(str(GEN), run_name='verify_only')
    generated = generator['cells']
    assert len(generated) == len(current['cells'])
    assert all((a['id'], a['cell_type'], a['source']) == (b['id'], b['cell_type'], b['source'])
               for a, b in zip(current['cells'], generated))
    assert ''.join(current['cells'][22]['source']).startswith('can_start = False')
    assert not any('本课不通过 `result()`' in ''.join(c['source']) for c in current['cells'])
    assert not any('按两次“开始”' in ''.join(c['source']) or '按下“停止”' in ''.join(c['source']) for c in current['cells'])
    quoted = '\n'.join(re.sub(r'^> ?', '', line) for c in current['cells']
                       if c['cell_type'] == 'markdown' for line in ''.join(c['source']).splitlines())
    fenced = re.findall(r'```python\s*\n(.*?)```', quoted, flags=re.S)
    for source in fenced:
        ast.parse(textwrap.dedent(source))

    guide = GUIDE.read_text(encoding='utf-8')
    expression = re.search(r'^can_start = (.+)$', guide, flags=re.M).group(1)
    compiled = compile(ast.parse(expression, mode='eval'), '<guide-start-condition>', 'eval')

    class Task:
        def __init__(self, status):
            self.status = status
        def done(self):
            return self.status in {'SUCCEEDED', 'FAILED', 'CANCELLED'}

    cases = []
    for state in ['待机', '会话已发起', '停止请求已发出']:
        for status in [None, 'PENDING', 'RUNNING', 'CANCELLING', 'SUCCEEDED', 'FAILED', 'CANCELLED']:
            task = None if status is None else Task(status)
            actual = eval(compiled, {'__builtins__': {}}, {'app_state': state, 'chat_task': task})
            expected = state == '待机' and (status is None or status in {'SUCCEEDED', 'FAILED', 'CANCELLED'})
            assert actual is expected, (state, status)
            cases.append({'app_state': state, 'task_status': status, 'can_start': actual})

    paths = [GUIDE, TASK / '02-产出清单与状态日志.md']
    links = 0
    for path in paths:
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if re.match(r'^https?://', target):
                continue
            destination = (path.parent / target.split('#')[0]).resolve()
            if destination != TASK / '验证结果.json':
                assert destination.exists(), (path, target)
            links += 1
    result = {'date': '2026-10-26', 'passed': True, 'cells': 27, 'code_cells_unchanged': 9,
              'changed_markdown_cells': changed, 'execution_and_metadata_unchanged': True,
              'generator_sources_match': True, 'python_quote_blocks_parsed': len(fenced),
              'local_links_checked': links, 'start_condition_cases': cases,
              'robot_connected': False, 'confirmation_1_2': '未登记整课通过'}
    (TASK / '验证结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('通过：27格源内容一致、9格代码及全部执行信息不变、21组启动条件、代码与引用块语法及本地链接。')


def archive():
    baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
    chunks = []
    for item in baseline[3:]:
        rel = item['path']
        before = (TASK / 'before' / rel).read_text(encoding='utf-8').splitlines(keepends=True)
        current = (ROOT / rel).read_text(encoding='utf-8').splitlines(keepends=True)
        chunks.extend(difflib.unified_diff(before, current, fromfile='a/' + rel, tofile='b/' + rel))
    patch = TASK / '共享文档本轮增量.patch'
    patch.write_text(''.join(chunks), encoding='utf-8', newline='\n')
    git('apply', '--reverse', '--check', '--', patch.relative_to(ROOT).as_posix())
    return patch


def main():
    patch = archive()
    verify()
    if '--stage' not in sys.argv:
        return
    paths = [NB, GEN, GUIDE] + [TASK / name for name in [
        'revise.py', 'verify_archive.py', '02-产出清单与状态日志.md', '基线.json',
        '验证结果.json', '共享文档本轮增量.patch',
    ]]
    relative = {p.relative_to(ROOT).as_posix() for p in paths}
    staged = set(filter(None, git('diff', '--cached', '--name-only', '-z').stdout.decode('utf-8').split('\0')))
    assert not staged - relative, '暂存区包含其他文件，停止但不改其内容。'
    git('add', '--', *sorted(relative))
    actual = set(filter(None, git('diff', '--cached', '--name-only', '-z').stdout.decode('utf-8').split('\0')))
    assert actual == relative
    git('diff', '--cached', '--check', '--', '.', ':(exclude)' + patch.relative_to(ROOT).as_posix())
    print(git('-c', 'core.quotepath=false', 'diff', '--cached', '--stat').stdout.decode('utf-8'))
    print(f'已定向暂存{len(actual)}份文件；未提交、未推送。')


if __name__ == '__main__':
    main()
