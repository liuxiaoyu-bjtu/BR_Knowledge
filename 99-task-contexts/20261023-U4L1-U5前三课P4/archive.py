"""归档本轮独立产物；混有前序修改的共享文档仅保存本轮补丁。"""
from pathlib import Path
import difflib
import json
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'


def git(*args, check=True):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, check=check)


def normalized(data):
    return data.decode('utf-8-sig').replace('\r\n', '\n')


baseline = json.loads((TASK / '输入与本轮基线.json').read_text(encoding='utf-8'))
clean, mixed, patches = [], [], []
for raw in baseline['shared']:
    rel = Path(raw).as_posix()
    before = (TASK / 'before' / rel).read_bytes()
    original = git('show', 'HEAD:' + rel, check=False)
    if original.returncode == 0 and normalized(original.stdout) == normalized(before):
        clean.append(rel)
    else:
        mixed.append(rel)
        patches.extend(difflib.unified_diff(
            normalized(before).splitlines(keepends=True),
            normalized((ROOT / rel).read_bytes()).splitlines(keepends=True),
            fromfile='a/' + rel, tofile='b/' + rel,
        ))
patch_path = TASK / '共享文档本轮增量.patch'
patch_path.write_text(''.join(patches), encoding='utf-8', newline='\n')
git('apply', '--reverse', '--check', '--', patch_path.relative_to(ROOT).as_posix())
assert len(clean) == 3 and len(mixed) == 8, (clean, mixed)

if '--stage' not in sys.argv:
    print(f'已记录{len(mixed)}份共享文件增量；{len(clean)}份原本干净的文件将直接暂存。补丁反向匹配通过。')
    raise SystemExit(0)

subprocess.run([sys.executable, '-X', 'utf8', str(TASK / 'verify.py')], cwd=ROOT, check=True)
paths = [ROOT / p for p in clean]
for name in ['U5-L1_语音识别', 'U5-L2_语音合成', 'U5-L3_LLM对话']:
    paths.append(PROJ / '教学设计' / f'{name}_教学设计.md')
for name in ['U4-L1_转向来宾', 'U5-L1_语音识别', 'U5-L2_语音合成', 'U5-L3_LLM对话']:
    paths.append(PROJ / 'PPT内容设计' / f'{name}_PPT内容大纲.md')
paths.append(PROJ / 'PPT内容设计/U4-L1_U5-L1-L3_P4覆盖检查记录.md')
paths += [TASK / name for name in [
    '00-任务上下文.md', '02-产出清单与状态日志.md', '输入与本轮基线.json',
    'update_records.py', 'verify.py', '验证结果.json', 'archive.py', '共享文档本轮增量.patch',
]]
relative = {p.relative_to(ROOT).as_posix() for p in paths}
existing = set(filter(None, git('diff', '--cached', '--name-only', '-z').stdout.decode('utf-8').split('\0')))
if existing - relative:
    raise RuntimeError('暂存区含其他任务文件；保留原暂存区并停止归档。')
git('add', '--', *sorted(relative))
staged = set(filter(None, git('diff', '--cached', '--name-only', '-z').stdout.decode('utf-8').split('\0')))
assert staged == relative, '暂存范围不符'
git('diff', '--cached', '--check', '--', '.', ':(exclude)' + patch_path.relative_to(ROOT).as_posix())
print(git('-c', 'core.quotepath=false', 'diff', '--cached', '--stat').stdout.decode('utf-8'))
print(f'暂存范围核验通过：{len(staged)}个文件。未提交、未推送。')
