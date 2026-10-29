"""仅核查课稿及沙箱生成；不导入SDK、不执行学生代码。"""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import re
import runpy
import tempfile
from urllib.parse import unquote
import warnings
import nbformat

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[1]
C=ROOT/'05-internal-materials/vocational-planning/03_X课程项目'
REL='05-internal-materials/vocational-planning/03_X课程项目/notebooks/U4-L2_走近来宾.ipynb'
base=json.loads((TASK/'基线.json').read_text(encoding='utf-8'))
path=ROOT/REL
current_bytes=path.read_bytes()
nb=json.loads(current_bytes)
old=json.loads((TASK/'before'/REL).read_text(encoding='utf-8'))
assert len(nb['cells'])==36
count=0
for i,(before,after) in enumerate(zip(old['cells'],nb['cells']),1):
    assert {k:v for k,v in before.items() if k not in ['source','id']}=={k:v for k,v in after.items() if k not in ['source','id']},i
    if 'id' in before:assert before['id']==after['id'],i
    else:assert isinstance(after.get('id'),str),i
    if before['cell_type']=='code':
        assert {k:v for k,v in before.items() if k!='id'}=={k:v for k,v in after.items() if k!='id'},('原代码被改',i)
        ast.parse(''.join(after['source']),filename=f'U4-L2-cell{i}')
        count+=1
assert count==10
assert {k:v for k,v in old.items() if k!='cells'}=={k:v for k,v in nb.items() if k!='cells'}
with warnings.catch_warnings(record=True) as seen:
    nbformat.validate(nbformat.from_dict(nb))
    format_notes=[str(w.message) for w in seen]

diff=runpy.run_path(str(C/'_diffcheck_u2.py'))
regen=runpy.run_path(str(C/'_regen_from_nb.py'))
with tempfile.TemporaryDirectory(prefix='u4l2_roundtrip_') as sandbox:
    generated=diff['run_gen'](str(C/'_gen_L14.py'),sandbox)
    assert json.loads(Path(generated).read_text(encoding='utf-8'))==nb
with tempfile.TemporaryDirectory(prefix='u4l2_reverse_') as sandbox:
    p=Path(sandbox);(p/'notebooks').mkdir()
    regen['build'](str(p/'_gen_L14.py'),str(path),regen['DOC']['_gen_L14.py'])
    runpy.run_path(str(p/'_gen_L14.py'),run_name='__main__')
    assert json.loads((p/'notebooks'/path.name).read_text(encoding='utf-8'))==nb
assert path.read_bytes()==current_bytes
external_changes=[]
for rel,digest in base['protected'].items():
    current=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    if current!=digest:external_changes.append({'file':rel,'baseline':digest,'current':current})
    if '/U4-' in rel or rel.endswith('X课程大纲-v4.md'):assert current==digest,rel

section=''.join(nb['cells'][35]['source'])
assert not any(x in section for x in ['STEP 09','STEP 11','STEP 04 检查','STEP 09 停靠后'])
assert all(x in section for x in ['STEP 04','STEP 05','STEP 06','STEP 07','STEP 08'])
assert ''.join(nb['cells'][34]['source'])==''.join(old['cells'][34]['source'])
all_markdown='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='markdown')
assert 'distance = k × h_ratio' not in all_markdown
assert 'distance = k ÷ h_ratio' in all_markdown

missing=[]
def links(text,parent,label):
    for match in re.finditer(r'!?\[[^\]\n]*\]\(([^\n]+?)\)',text):
        target=match.group(1).strip().strip('<>')
        if re.match(r'^[a-zA-Z]+:',target) or target.startswith('#'):continue
        target=unquote(target.split('#')[0])
        if target and not (parent/target).exists():missing.append({'file':label,'link':target})
for rel in base['shared']:
    links((ROOT/rel).read_text(encoding='utf-8'),(ROOT/rel).parent,rel)
    links((TASK/'head-increment'/rel).read_text(encoding='utf-8'),(ROOT/rel).parent,'HEAD增量:'+rel)
report=C/'实验验证/U4-L2_重开发回读与第五部分同步.md'
links(report.read_text(encoding='utf-8'),report.parent,report.name)
links((TASK/'00-任务上下文.md').read_text(encoding='utf-8'),TASK,'任务上下文')
links(all_markdown,path.parent,path.name)

tool_rel='05-internal-materials/vocational-planning/03_X课程项目/_regen_from_nb.py'
previous=(TASK/'before'/tool_rel).read_text(encoding='utf-8')
now=(ROOT/tool_rel).read_text(encoding='utf-8')
patch=''.join(difflib.unified_diff(previous.splitlines(keepends=True),now.splitlines(keepends=True),
                               fromfile='a/'+tool_rel,tofile='b/'+tool_rel,n=0))
(TASK/'维护工具本轮增量.patch').write_text(patch,encoding='utf-8',newline='\n')
out={'cells':36,'markdown_cells':26,'code_cells':count,'original_code_and_outputs_preserved':True,
     'metadata_preserved':True,'missing_cell_ids_completed':True,'student_exercise_preserved':True,'nbformat_valid':True,
     'format_notes':format_notes,'generator_roundtrip':True,'reverse_roundtrip':True,
     'protected_checked':len(base['protected']),'external_changes_not_written_or_staged':external_changes,
     'u4_l1_l3_l4_and_v4_unchanged':True,'step_references_valid':True,
     'missing_links':missing,'robot_executed':False,'phase_advanced':False}
(TASK/'离线核查结果.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
if missing:raise SystemExit(1)
