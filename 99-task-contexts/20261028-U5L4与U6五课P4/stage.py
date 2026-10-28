from pathlib import Path
import json,subprocess,difflib,hashlib
ROOT=Path(__file__).resolve().parents[2];TASK=Path(__file__).resolve().parent
CP=Path('05-internal-materials/vocational-planning/03_X课程项目')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
assert not git('diff','--cached','--name-only').strip(),'存在其他暂存，停止混入'
scope={'__file__':str(TASK/'update_records.py')}
exec(compile((TASK/'update_records.py').read_text(encoding='utf-8-sig').split('patch=[];changed=[]')[0],str(TASK/'update_records.py'),'exec'),scope)
review_rows=json.loads((TASK/'状态补丁核查.json').read_text(encoding='utf-8'))
base_commit=git('rev-parse','HEAD').decode().strip()
expected_index={};chunks=[]
for row in review_rows:
 rel=row['path'];base=git('show','HEAD:'+rel).decode('utf-8').replace('\r\n','\n')
 after=scope['update'](rel,base)
 # 新HEAD已单独提交U7；仅将同一五课状态变更应用在其上，逐行保留U7。
 for line in base.splitlines():
  if 'U7' in line and '五课' not in line and line not in after.splitlines():
   assert '本表核对全部32课' in line
   suffix='2026-10-28另按用户要求'+line.split('2026-10-28另按用户要求')[1]
   assert suffix in after
 expected_index[rel]=after
 chunks+=difflib.unified_diff(base.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel)
(TASK/'当前HEAD状态增量.patch').write_bytes(''.join(chunks).encode('utf-8'))
(TASK/'提交基线.json').write_text(json.dumps({'head':base_commit,'shared_expected_sha256':{r:hashlib.sha256(s.encode('utf-8')).hexdigest() for r,s in expected_index.items()}},ensure_ascii=False,indent=2),encoding='utf-8')
assert git('rev-parse','HEAD').decode().strip()==base_commit
patch=str(TASK/'当前HEAD状态增量.patch')
subprocess.run(['git','apply','--cached','--check','--whitespace=nowarn',patch],cwd=ROOT,check=True)
subprocess.run(['git','apply','--cached','--whitespace=nowarn',patch],cwd=ROOT,check=True)
M=json.loads((TASK/'页面与覆盖映射.json').read_text(encoding='utf-8'))
paths=[CP/'PPT内容设计'/d['filename'] for d in M.values()]+[CP/'PPT内容设计/U5-L4_U6_P4覆盖检查记录.md']
artifacts=['00-任务上下文.md','01-执行提示词.md','02-产出清单与状态日志.md','prepare.py','build.py','verify.py','update_records.py','prepare_status_patch.py','apply_reviewed_status.py','输入指纹.json','页面与覆盖映射.json','校验结果.json','状态补丁核查.json','提交基线.json','stage.py']
paths += [(TASK/name).relative_to(ROOT) for name in artifacts]
assert all((ROOT/p).is_file() for p in paths)
git('add','--',*map(str,paths))
subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
expected_shared={row['path'] for row in json.loads((TASK/'状态补丁核查.json').read_text(encoding='utf-8'))}
names=set(git('-c','core.quotepath=false','diff','--cached','--name-only').decode('utf-8').splitlines())
assert names==expected_shared|{p.as_posix() for p in paths},names
for rel in expected_shared:
 # 只暂存基于HEAD的本轮状态增量；从暂存结果删除本轮变动后应恢复原HEAD。
 index=git('show',':'+rel).decode('utf-8').replace('\r\n','\n')
 assert index==expected_index[rel],'暂存内容混入：'+rel
print(git('-c','core.quotepath=false','diff','--cached','--stat').decode('utf-8'))
print('暂存范围核对通过：',len(names),'个文件；无Notebook、生成器、PPTX或U7任务内容。')
(TASK/'待提交文件.json').write_text(json.dumps(sorted(names),ensure_ascii=False,indent=2),encoding='utf-8')
