"""仅在任务沙箱运行八课生成器；不执行Notebook、不连接机器人。"""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
import runpy
import tempfile
from urllib.parse import unquote

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
COURSE = ROOT/'05-internal-materials/vocational-planning/03_X课程项目'
NB = COURSE/'notebooks'
before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in NB.glob('*.ipynb')}
diff = runpy.run_path(str(COURSE/'_diffcheck_u2.py'))
regen = runpy.run_path(str(COURSE/'_regen_from_nb.py'))
results=[]
try:
    import nbformat
except ImportError:
    nbformat=None

for number in range(25,33):
    gen_name=f'_gen_L{number}.py'
    name=next(name for gen,name in diff['PAIRS'] if gen==gen_name)
    original=json.loads((NB/name).read_text(encoding='utf-8'))
    if nbformat is not None:
        nbformat.validate(nbformat.from_dict(original))
    with tempfile.TemporaryDirectory(prefix='v5_gen_check_') as folder:
        generated=diff['run_gen'](str(COURSE/gen_name),folder)
        assert json.loads(Path(generated).read_text(encoding='utf-8'))==original
    # 回写和重跑都定向到沙箱，只比较新八课。
    with tempfile.TemporaryDirectory(prefix='v5_regen_check_') as folder:
        target=Path(folder)/gen_name
        (Path(folder)/'notebooks').mkdir()
        regen['build'](str(target),str(NB/name),regen['DOC'][gen_name])
        runpy.run_path(str(target),run_name='__main__')
        restored=json.loads((Path(folder)/'notebooks'/name).read_text(encoding='utf-8'))
        assert restored==original
    results.append({'file':name,'generator_roundtrip':True,'reverse_roundtrip':True,
                    'nbformat_validated':nbformat is not None})
for name,digest in before.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name

shared=json.loads((TASK/'共享文档清单.json').read_text(encoding='utf-8'))
paths=[ROOT/p for p in shared if p.endswith('.md')]
paths += [COURSE/'X课程大纲-v5.md',COURSE/'实验验证/U7_U8_v5重构与验证清单.md',
          NB/'x_lab/README.md',TASK/'00-任务上下文.md',TASK/'sdk-evidence/README.md']
missing=[]
def check_links(text,parent,label):
    for match in re.finditer(r'!?\[[^\]\n]*\]\(([^\n]+?)\)',text):
        target=match.group(1).strip().strip('<>')
        if re.match(r'^[a-zA-Z]+:',target) or target.startswith('#'):
            continue
        target=unquote(target.split('#')[0])
        if target and not (parent/target).exists():
            missing.append({'file':label,'target':target})
for path in paths:
    check_links(path.read_text(encoding='utf-8'),path.parent,str(path.relative_to(ROOT)))
for row in results:
    nb=json.loads((NB/row['file']).read_text(encoding='utf-8'))
    for c in nb['cells']:
        if c['cell_type']=='markdown':
            check_links(''.join(c['source']),NB,row['file'])
for rel in shared:
    p=TASK/'head-increment'/rel
    if rel.endswith('.md'):
        check_links(p.read_text(encoding='utf-8'),(ROOT/rel).parent,'HEAD增量:'+rel)

# 两个维护脚本原本未纳入Git；仅存本轮补丁，不将全部旧代码夹带进提交。
patch=[]
for rel in json.loads((TASK/'本地维护工具.json').read_text(encoding='utf-8')):
    old=(TASK/'before'/rel).read_text(encoding='utf-8')
    current=(ROOT/rel).read_text(encoding='utf-8')
    ast.parse(current)
    patch.extend(difflib.unified_diff(old.splitlines(keepends=True),current.splitlines(keepends=True),
                                    fromfile='a/'+rel,tofile='b/'+rel,n=0))
(TASK/'维护工具本轮增量.patch').write_text(''.join(patch),encoding='utf-8',newline='\n')
out={'eight_lessons':results,'notebooks_unchanged':True,'missing_links':missing,
     'robot_executed':False}
(TASK/'维护与链接核查结果.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
if missing:raise SystemExit(1)
