from pathlib import Path
import difflib,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
TASK=Path(__file__).resolve().parent
scope={'__file__':str(TASK/'update_records.py')}
exec(compile((TASK/'update_records.py').read_text(encoding='utf-8-sig').split('patch=[];changed=[]')[0],str(TASK/'update_records.py'),'exec'),scope)
update=scope['update']; files=[];wp=[];hp=[]
for rel in scope['SHARED']:
 if '/notebooks/' in rel or '/教学设计/' in rel or '/_gen_' in rel:continue
 raw=(ROOT/rel).read_bytes();old=raw.decode('utf-8').replace('\r\n','\n');new=update(rel,old)
 assert old!=new,rel
 # 已只读核对的外部变化都属于U7；逐行验证这些记录不被删除或改写。
 old_u7=[l for l in old.splitlines() if 'U7' in l and '五课' not in l]
 new_u7=new.splitlines()
 for line in old_u7:
  if line not in new_u7:
   # 五课与U7共用首段时，仅替换五课子句，完整保留U7更新句。
   assert '本表核对全部32课' in line
   suffix=line.split('2026-10-28另按用户要求')[1]
   assert '2026-10-28另按用户要求'+suffix in new
 out=TASK/'reviewed-status'/rel;out.parent.mkdir(parents=True,exist_ok=True)
 out.write_bytes(new.replace('\n','\r\n').encode('utf-8') if b'\r\n' in raw else new.encode('utf-8'))
 files.append({'path':rel,'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'u7_records_preserved':True})
 wp+=difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel)
 head=(TASK/'head'/rel).read_text(encoding='utf-8');newhead=update(rel,head)
 hp+=difflib.unified_diff(head.splitlines(keepends=True),newhead.splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel)
 print(rel,'候选差异',len(list(difflib.unified_diff(old.splitlines(),new.splitlines(),n=0))),'行；U7原文保留')
(TASK/'工作区精确状态.patch').write_bytes(''.join(wp).encode('utf-8'))
(TASK/'提交状态增量.patch').write_bytes(''.join(hp).encode('utf-8'))
(TASK/'状态补丁核查.json').write_text(json.dumps(files,ensure_ascii=False,indent=2),encoding='utf-8')
print('仅生成独立候选与精确补丁；尚未写入共享文档。')
