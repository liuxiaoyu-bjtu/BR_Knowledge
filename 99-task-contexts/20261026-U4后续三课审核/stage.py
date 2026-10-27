"""只暂存本轮三课、审核产物及导航新增记录，不提交其他任务原有改动。"""
from pathlib import Path
import json
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
manifest = json.loads((TASK / '修订清单.json').read_text(encoding='utf-8'))
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT).strip(), '暂存区有其他改动，请先检查'
files = []
for item in manifest['lessons']:
    files.extend([item['notebook'], item['generator']])
files.append('05-internal-materials/vocational-planning/03_X课程项目/实验验证/U4-L2-L4_距离实验复评与文字校对.md')
for name in ['research.py', 'revise.py', 'records.py', 'verify.py', 'stage.py', '修订清单.json',
             '导航清单.json', '导航本轮增量.patch', '工作区导航增量.patch', '校验结果.json',
             '02-产出清单与状态日志.md']:
    files.append((TASK / name).relative_to(ROOT).as_posix())
pages = json.loads((TASK / 'sdk-evidence/pages.json').read_text(encoding='utf-8'))
evidence = ['pages.json', 'sdk-urls.json'] + [x['text_file'] for x in pages]
for name in sorted(set(evidence)):
    files.append((TASK / 'sdk-evidence' / name).relative_to(ROOT).as_posix())
assert all((ROOT / p).is_file() for p in files)
subprocess.run(['git', 'apply', '--cached', '--check', str(TASK / '导航本轮增量.patch')], cwd=ROOT, check=True)
subprocess.run(['git', 'apply', '--cached', str(TASK / '导航本轮增量.patch')], cwd=ROOT, check=True)
subprocess.run(['git', 'add', '--', *files], cwd=ROOT, check=True)
staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'], cwd=ROOT).decode('utf-8').split('\0')
expected = set(files + manifest['shared'])
assert set(filter(None, staged)) == expected
print('暂存文件：', len(expected), '；无before目录或其他任务改动。')
