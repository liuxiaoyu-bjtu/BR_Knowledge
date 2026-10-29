from pathlib import Path
import subprocess
import json

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = Path('05-internal-materials/vocational-planning/03_X课程项目')

def git(*args, data=None):
    return subprocess.check_output(['git', '-c', 'core.quotepath=false', *args], cwd=ROOT, input=data)

assert not git('diff', '--cached', '--name-only').strip(), '暂存区已有其他改动，停止自动暂存'
shared = json.loads((TASK / '共享文档清单.json').read_text(encoding='utf-8'))
for rel in shared:
    payload = (TASK / 'head-increment' / rel).read_bytes().replace(b'\r\n', b'\n')
    oid = git('hash-object', '-w', '--stdin', data=payload).decode().strip()
    git('update-index', '--add', '--cacheinfo', '100644', oid, rel)

paths = [P / '实验验证/U4-L3-L4_承接新版L2的同步审查.md', P / '实验验证/U7_逐课真机测试指导.md']
for prefix in ['U4-L3', 'U4-L4', 'U7-L1', 'U7-L2', 'U7-L3']:
    paths.append(next((P / 'notebooks').glob(prefix + '_*.ipynb')))
paths += [P / f'_gen_L{i}.py' for i in [15, 16, 25, 26, 27]]
paths += [TASK.relative_to(ROOT) / name for name in [
    '基线.json', '逐格修改记录.json', '新增cellID.json', '维护工具增量.patch', '共享文档清单.json',
    '修订Notebook.py', '补齐cellID.py', '同步文档.py', '离线核查.py', '离线核查结果.json',
    '提交本轮增量.py', '完成记录.md', '外部改动核对.json']]
allowed = set(shared + [p.as_posix() for p in paths])
git('add', '--', *[p.as_posix() for p in paths])
staged = set(git('diff', '--cached', '--name-only').decode().splitlines())
assert staged <= allowed, staged - allowed
git('diff', '--cached', '--check')
(TASK / '提交清单.json').write_text(json.dumps(sorted(staged), ensure_ascii=False, indent=2), encoding='utf-8')
print(git('diff', '--cached', '--stat').decode())
print('共享文档已按HEAD增量暂存，其他工作区改动保留。待审阅后本地commit。')
