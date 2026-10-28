from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[2];TASK=Path(__file__).resolve().parent
rows=json.loads((TASK/'状态补丁核查.json').read_text(encoding='utf-8'))
for row in rows:
 assert row['u7_records_preserved']
 assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['before_sha256'],'补丁核查后文档又变动，停止：'+row['path']
patch=str(TASK/'工作区精确状态.patch')
subprocess.run(['git','apply','--check','--whitespace=nowarn',patch],cwd=ROOT,check=True)
subprocess.run(['git','apply','--whitespace=nowarn',patch],cwd=ROOT,check=True)
for row in rows:
 # Git按仓库属性处理行尾，核查文本与已审候选一致。
 assert (ROOT/row['path']).read_text(encoding='utf-8')==(TASK/'reviewed-status'/row['path']).read_text(encoding='utf-8')
print('已应用8份文档的五课状态精确补丁；U7新增记录逐行保留。')
