from pathlib import Path
import json
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
COURSE = '05-internal-materials/vocational-planning/03_X课程项目'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()

assert not git('diff', '--cached', '--name-only'), '共享暂存区仍有其他任务，保持其内容，不混合提交'
head = git('rev-parse', 'HEAD')
baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
subprocess.run(['git', 'merge-base', '--is-ancestor', baseline['head'], head], cwd=ROOT, check=True)
scope = runpy.run_path(str(TASK / '同步入口并移除旧版.py'))
expected = set()
for name in baseline['shared']:
    current = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT).decode('utf-8-sig')
    updated = scope['change'](name, current)
    staged_path = TASK / 'head-increment' / name
    staged_path.parent.mkdir(parents=True, exist_ok=True)
    staged_path.write_text(updated, encoding='utf-8', newline='')
    blob = git('hash-object', '-w', '--path=' + name, str(staged_path))
    subprocess.run(['git', 'update-index', '--add', '--cacheinfo', '100644,' + blob + ',' + name], cwd=ROOT, check=True)
    expected.add(name)

for name in baseline['old']:
    assert not (ROOT / name).exists(), name
subprocess.run(['git', 'add', '-u', '--', *baseline['old']], cwd=ROOT, check=True)
expected.update(baseline['old'])
newfiles = [COURSE + '/实验验证/足球测试_第1轮_操作与记录.md',
            COURSE + '/实验验证/足球测试_第1轮_静止检测.ipynb']
taskfiles = ['基线.json', '生成第一轮测试.py', '同步入口并移除旧版.py', '联动记录.json',
             '离线核查.py', '离线核查结果.json', '完成记录.md', '提交本轮.py']
newfiles += [(TASK / name).relative_to(ROOT).as_posix() for name in taskfiles]
subprocess.run(['git', 'add', '--', *newfiles], cwd=ROOT, check=True)
expected.update(newfiles)
actual = set(git('-c', 'core.quotepath=false', 'diff', '--cached', '--name-only').splitlines())
assert actual == expected, (actual - expected, expected - actual)
assert git('rev-parse', 'HEAD') == head, '暂存过程中HEAD发生变化，先复核'
subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
print(git('diff', '--cached', '--stat'))
(TASK / '提交清单.json').write_text(json.dumps(sorted(expected), ensure_ascii=False, indent=2), encoding='utf-8')
subprocess.run(['git', 'commit', '-m', '将足球测试改为逐轮指导与记录，配套第一轮代码并清理旧版'], cwd=ROOT, check=True)
print(git('log', '-1', '--oneline'))
