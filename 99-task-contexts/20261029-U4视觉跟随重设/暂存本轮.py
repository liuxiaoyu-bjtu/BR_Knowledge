from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = Path('05-internal-materials/vocational-planning/03_X课程项目')

def git(*args, data=None):
    return subprocess.check_output(['git', '-c', 'core.quotepath=false', *args], cwd=ROOT, input=data)

base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
assert git('rev-parse', 'HEAD').decode().strip() == base['head'], 'HEAD在本轮改变，先重新审阅'
assert not git('diff', '--cached', '--name-only').strip(), '暂存区已有改动'
shared = json.loads((TASK / '共享文档清单.json').read_text(encoding='utf-8'))
for rel in shared:
    payload = (TASK / 'head-increment' / rel).read_bytes().replace(b'\r\n', b'\n')
    oid = git('hash-object', '-w', '--stdin', data=payload).decode().strip()
    git('update-index', '--add', '--cacheinfo', '100644', oid, rel)

direct = [P / 'notebooks/U4-L3_跟住来宾.ipynb', P / 'notebooks/U4-L4_接待来宾.ipynb',
          P / '_gen_L15.py', P / '_gen_L16.py',
          P / '实验验证/U4-L3-L4_视觉移动跟随重设与验证.md']
task_rel = TASK.relative_to(ROOT)
direct += [task_rel / name for name in [
    '基线.json', '完成记录.md', '重设Notebook.py', '同步文档.py', '共享文档清单.json',
    '同步维护说明.py', '维护工具说明增量.patch', '离线核查.py', '离线核查结果.json', '暂存本轮.py']]
direct += [task_rel / 'before' / rel for rel in [
    P / 'notebooks/U4-L3_跟住来宾.ipynb', P / 'notebooks/U4-L4_接待来宾.ipynb', P / '_gen_L15.py', P / '_gen_L16.py']]
git('add', '--', *[p.as_posix() for p in direct])
staged = set(git('diff', '--cached', '--name-only').decode().splitlines())
assert staged == set(shared) | {p.as_posix() for p in direct}
git('diff', '--cached', '--check')
(TASK / '提交清单.json').write_text(json.dumps(sorted(staged), ensure_ascii=False, indent=2), encoding='utf-8')
print(git('diff', '--cached', '--stat').decode())
print('已隔离暂存本轮增量；未commit或push。')
