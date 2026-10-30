from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = Path('05-internal-materials/vocational-planning/03_X课程项目')


def git(*args, data=None):
    return subprocess.check_output(['git', '-c', 'core.quotepath=false', *args], cwd=ROOT, input=data)


base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
assert git('rev-parse', 'HEAD').decode().strip() == base['head'], 'HEAD已变化，请先核对并发提交'
assert not git('diff', '--cached', '--name-only').strip(), '暂存区非空，不覆盖'
shared = json.loads((TASK / '共享文档清单.json').read_text(encoding='utf-8'))
for rel in shared:
    content = (TASK / 'head-increment' / rel).read_bytes().replace(b'\r\n', b'\n')
    oid = git('hash-object', '-w', '--stdin', data=content).decode().strip()
    git('update-index', '--add', '--cacheinfo', '100644', oid, rel)

direct = [P / 'notebooks/U4-L2_走近来宾.ipynb', P / 'notebooks/U4-L4_接待来宾.ipynb',
          P / '_gen_L14.py', P / '_gen_L16.py', P / '实验验证/U4-L2-L3-L4_P2复核与定稿记录.md']
direct += [TASK.relative_to(ROOT) / name for name in [
    '基线.json', '用户确认.md', '修订L2停止路径.py', '同步进度.py', '共享文档清单.json',
    '离线核查.py', '离线核查结果.json', '完成记录.md', '暂存本轮.py']]
git('add', '--', *[path.as_posix() for path in direct])
staged = set(git('diff', '--cached', '--name-only').decode('utf-8').splitlines())
assert staged == set(shared) | {path.as_posix() for path in direct}, '暂存范围不符'
git('diff', '--cached', '--check')
for rel in shared:
    assert git('show', ':' + rel).replace(b'\r\n', b'\n') == (TASK / 'head-increment' / rel).read_bytes().replace(b'\r\n', b'\n')
print(git('diff', '--cached', '--stat').decode('utf-8'))
print('仅本轮变更已暂存；未提交或推送。')
