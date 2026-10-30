from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[2]
T=Path(__file__).resolve().parent
P=Path('05-internal-materials/vocational-planning/03_X课程项目')


def git(*args,data=None):
    return subprocess.check_output(['git','-c','core.quotepath=false',*args],cwd=ROOT,input=data)


base=json.loads((T/'基线.json').read_text(encoding='utf-8'))
assert git('rev-parse','HEAD').decode().strip()==base['head']
assert not git('diff','--cached','--name-only').strip(), '暂存区非空，不覆盖'
shared=json.loads((T/'共享文档清单.json').read_text(encoding='utf-8'))
for rel in shared:
    payload=(T/'head-increment'/rel).read_bytes().replace(b'\r\n',b'\n')
    oid=git('hash-object','-w','--stdin',data=payload).decode().strip()
    git('update-index','--add','--cacheinfo','100644',oid,rel)
direct=[next((P/'notebooks').glob('U7-L1*.ipynb')),P/'_gen_L25.py',
        P/'实验验证/U7-L1_能力选择与初步方案修订.md']
direct += [T.relative_to(ROOT)/f for f in ['基线.json','共享文档清单.json','修订L1.py','同步文档.py',
            'L1测试段.md','离线核查.py','离线核查结果.json','完成记录.md','暂存本轮.py']]
git('add','--',*[p.as_posix() for p in direct])
staged=set(git('diff','--cached','--name-only').decode().splitlines())
assert staged==set(shared)|{p.as_posix() for p in direct}, '暂存路径超出范围'
git('diff','--cached','--check')
for rel in shared:
    assert git('show',':'+rel).replace(b'\r\n',b'\n')==(T/'head-increment'/rel).read_bytes().replace(b'\r\n',b'\n')
(T/'提交清单.json').write_text(json.dumps(sorted(staged),ensure_ascii=False,indent=2),encoding='utf-8')
print(git('diff','--cached','--stat').decode())
print('本轮已隔离暂存，未commit或push。')
