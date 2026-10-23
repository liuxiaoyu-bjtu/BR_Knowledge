"""只暂存本轮交付；共享文件以本轮增量留档，不夹带其他任务修改。"""
import subprocess
from revise import ROOT, TASK, PROJ, NB

paths = [next(NB.glob(f'U5-L{i}_*.ipynb')) for i in range(1,4)]
paths += [NB/'U5-L2/U5-L2_语音合成.ipynb', NB/'U5-L2/sound_lab.py',
          NB/'U5-L2/fonts/wqy-microhei.ttc', NB/'_外挂附件清单.md']
paths += [PROJ/f'_gen_L{i}.py' for i in (17,18,19)]
paths += [PROJ/'实验验证/U5-L1-L2-L3_P2复核与修改方案.md',
          PROJ/'实验验证/U5_语音SDK能力核验记录.md']
paths += [TASK/name for name in ('revise.py','finalize.py','verify.py','archive.py',
          '验证结果.json','02-产出清单与状态日志.md','共享文档本轮增量.patch')]
relative = [p.relative_to(ROOT).as_posix() for p in paths]

def git(*args):
    return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,check=True)

existing=git('diff','--cached','--name-only','-z').stdout.decode('utf-8').split('\0')
if set(filter(None,existing))-set(relative):
    raise RuntimeError('暂存区含其他文件，停止归档，不重置用户暂存区。')
git('add','--',*relative)
staged=set(filter(None,git('diff','--cached','--name-only','-z').stdout.decode('utf-8').split('\0')))
if staged != set(relative):
    raise RuntimeError('实际暂存范围与本轮清单不同。')
git('diff','--cached','--check','--','.',':(exclude)'+(TASK/'共享文档本轮增量.patch').relative_to(ROOT).as_posix())
print(git('-c','core.quotepath=false','diff','--cached','--stat').stdout.decode('utf-8'))
print(f'暂存范围核验通过：{len(staged)}个文件；未提交、未推送。')
