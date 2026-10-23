"""只暂存本轮交付；共享文件增量留档，保留其他任务的工作区修改。"""
import subprocess
from revise import ROOT, TASK, PROJ, NB

paths = [NB, PROJ / '_gen_L20.py']
paths += [PROJ / '实验验证' / name for name in (
    'U5-L4_教学审阅与真机验证建议.md',
    'U5_语音SDK能力核验记录.md',
    'U5-L4_真机问题复评与重构建议.md',
)]
paths += [TASK / name for name in (
    'revise.py', 'records.py', 'verify.py', 'archive.py',
    '前三课基线指纹.json', '验证结果.json',
    '02-产出清单与状态日志.md', '共享文档本轮增量.patch',
)]
relative = [p.relative_to(ROOT).as_posix() for p in paths]


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, check=True)


existing = set(filter(None, git('diff', '--cached', '--name-only', '-z').stdout.decode('utf-8').split('\0')))
if existing - set(relative):
    raise RuntimeError('暂存区含其他文件，停止归档，不重置用户暂存区。')

git('add', '--', *relative)
staged = set(filter(None, git('diff', '--cached', '--name-only', '-z').stdout.decode('utf-8').split('\0')))
if staged != set(relative):
    raise RuntimeError('实际暂存范围与本轮清单不同。')

git('diff', '--cached', '--check', '--', '.',
    ':(exclude)' + (TASK / '共享文档本轮增量.patch').relative_to(ROOT).as_posix())
print(git('-c', 'core.quotepath=false', 'diff', '--cached', '--stat').stdout.decode('utf-8'))
print(f'暂存范围核验通过：{len(staged)}个文件；未提交、未推送。')
