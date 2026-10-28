from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
CP = Path('05-internal-materials/vocational-planning/03_X课程项目')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

assert not git('diff', '--cached', '--name-only').strip(), '已有其他暂存内容，停止，禁止混入本轮'
git('apply', '--cached', '--check', '--whitespace=nowarn', str(TASK / '提交状态增量.patch'))
git('apply', '--cached', '--whitespace=nowarn', str(TASK / '提交状态增量.patch'))
paths = [CP / '教学设计' / (key + '_' + title + '_教学设计.md') for key, title in [
    ('U5-L4', '语音会话管理'), ('U6-L1', '动作的来源'), ('U6-L2', '动作录制与回放'),
    ('U6-L3', '视频动作训练'), ('U6-L4', '动作编排')]]
paths += [CP / '实验验证/U5-L4_U6_P3教学设计覆盖检查记录.md',
          CP / 'notebooks/U6-L2_动作录制与回放.ipynb', CP / 'notebooks/U6-L4_动作编排.ipynb']
paths += [CP / f'_gen_L{i}.py' for i in (20,21,22,23,24)]
paths += [p.relative_to(ROOT) for p in TASK.iterdir() if p.is_file() and p.suffix != '.patch']
assert all((ROOT / p).is_file() for p in paths)
git('add', '--', *map(str, paths))
git('diff', '--cached', '--check')
names = git('-c', 'core.quotepath=false', 'diff', '--cached', '--name-only').decode('utf-8').splitlines()
expected_shared = {'AGENTS.md', 'INDEX.md', 'CHANGELOG.md',
    '05-internal-materials/vocational-planning/README.md',
    '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md',
    (CP / 'X课程当前进度.md').as_posix(), (CP / 'X课程开发计划-v4.md').as_posix(),
    (CP / '实验验证/U5-L4_P2复核与定稿记录.md').as_posix(),
    (CP / '实验验证/U6_单元重构与动作编排核验.md').as_posix()}
assert set(names) == expected_shared | {p.as_posix() for p in paths}, names
print(git('-c', 'core.quotepath=false', 'diff', '--cached', '--stat').decode('utf-8'))
print('暂存范围核对通过：', len(names), '个文件，无PPT、无其他课程Notebook、无备份')
