from pathlib import Path
import ast,json,re,hashlib,nbformat,subprocess,copy,warnings
from pptx import Presentation
R=Path(__file__).resolve().parents[2];P=R/'05-internal-materials/vocational-planning/03_X课程项目';T=Path(__file__).resolve().parent
result=[]
task_files=set(json.loads((T/'学材变更清单.json').read_text(encoding='utf-8'))['files'])
def check(name,value):
 result.append({'check':name,'passed':bool(value)})
 if not value: print('FAIL',name)
audit=[]
files=[f for f in sorted((P/'notebooks').glob('U*.ipynb')) if re.match(r'^U[1-8]-L[1-4]_',f.name) and not f.stem.endswith(' 1')]
check('32份主Notebook',len(files)==32)
for f in files:
 n=json.loads(f.read_text(encoding='utf-8-sig'));old=json.loads((T/'before'/f.relative_to(R)).read_text(encoding='utf-8-sig'));code=f.name[:5]
 try:
  with warnings.catch_warnings():
   warnings.simplefilter('ignore');nbformat.validate(nbformat.from_dict(copy.deepcopy(n)))
  valid=True
 except Exception as e: valid=False;print(f.name,e)
 check(code+' Notebook结构',valid)
 # 任何原代码、输出与执行计数都不得因评价补齐发生变化。
 before=[c for c in old['cells'] if c['cell_type']=='code'];after=[c for c in n['cells'] if c['cell_type']=='code']
 check(code+' 所有代码格和执行信息保留',before==after)
 check(code+' 代码格原位置保留',[i for i,c in enumerate(n['cells']) if c['cell_type']=='code']==[i for i,c in enumerate(old['cells']) if c['cell_type']=='code'])
 text='\n'.join(''.join(c['source']) for c in n['cells'] if c['cell_type']=='markdown')
 ev=re.search(r'^#{2,3} [^\n]*学习评价\s*\n',text,re.M);check(code+' 独立学习评价标题',ev is not None)
 check(code+' 教师参考答案',bool(re.search(r'^> 参考答案',text,re.M)))
 ck=re.search(r'^### [^\n]*检查点[^\n]*\n([\s\S]*?)(?=\n### |\Z)',text,re.M)
 check(code+' 可勾选检查点',bool(ck and '- [__]' in ck.group(1)))
 check(code+' 思考题独立标示',bool(re.search(r'^### [^\n]*思考题',text,re.M)))
 if f.relative_to(R).as_posix() in task_files:
  gen=P/f'_gen_L{(int(code[1])-1)*4+int(code[4])}.py';a=ast.parse(gen.read_text(encoding='utf-8-sig'))
  snapshot=next(ast.literal_eval(x.value) for x in a.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='NOTEBOOK' for y in x.targets))
  check(code+' 生成器完整镜像',snapshot==n)
 audit.append({'lesson':code,'cells_before':len(old['cells']),'cells_after':len(n['cells']),'code_cells':len(after),'new_evaluation':len(n['cells'])>len(old['cells']),'changed':f.relative_to(R).as_posix() in task_files})

for code,at in {'U4-L1':26,'U5-L1':27,'U5-L2':27,'U5-L3':27}.items():
 f=next((P/'PPT').glob(code+'*_Codex审查版.pptx'));pr=Presentation(f);old=Presentation(T/'before'/f.relative_to(R));check(code+' PPT只新增一页',len(pr.slides)==len(old.slides)+1)
 nb=json.loads(next((P/'notebooks').glob(code+'*.ipynb')).read_text(encoding='utf-8'))
 c=next(c for c in nb['cells'] if re.match(r'^## [六七]、学习评价',''.join(c['source'])));s=''.join(c['source']);qs=s.split('请独立作答；操作完成情况另按本课记录与检查点核对。\n\n')[1].split('\n\n> 参考答案')[0];questions=re.split(r'\n\n(?=[123]\. )',qs)
 student='\n'.join(sh.text for sh in pr.slides[at-1].shapes if sh.has_text_frame)
 clean=lambda x:re.sub(r'\s|`','',x)
 for i,q in enumerate(questions):check(code+f' PPT第{i+1}题原文',clean(q) in clean(student))
 check(code+' 答案仅在备注','参考答案' not in student and '参考答案' in pr.slides[at-1].notes_slide.notes_text_frame.text)
 teach=next((P/'教学设计').glob(code+'*')).read_text(encoding='utf-8')
 for i,q in enumerate(questions):check(code+f' 教案第{i+1}题原文',q in teach)
 # 重新生成前后，原页面的文字除页码、阅读章号外应一致。
 def visible(slide):
  values=[s.text for s in slide.shapes if s.has_text_frame]
  return [re.sub(r'\d+ / \d+','PAGE',s).replace('课后阅读 §六','课后阅读 §七') for s in values]
 for i,slide in enumerate(old.slides):
  newindex=i+(i>=at-1);check(code+f' 原第{i+1}页文字保留',visible(slide)==visible(pr.slides[newindex]))

for code in ['U4-L2','U4-L3','U4-L4']:
 nb=json.loads(next((P/'notebooks').glob(code+'*.ipynb')).read_text(encoding='utf-8'));f=next((P/'教学设计').glob(code+'*'));s=f.read_text(encoding='utf-8')
 check(code+' 教学提示','> 教学提示：' in s)
 for h in ['一、课时目标','二、重难点','三、环节时间轴','四、教学环节详解','五、板书设计','六、学习评价']:check(code+' '+h,'## '+h in s)
 times=re.findall(r'^\| (\d+)–(\d+)min \|',s,re.M);check(code+' 45分钟时间轴',bool(times and times[0][0]=='0' and times[-1][1]=='45' and all(times[i][1]==times[i+1][0] for i in range(len(times)-1))))
 goals=''.join(nb['cells'][0]['source']).split('**课程目标**')[1].strip();check(code+' 目标完全一致',goals in s)
 c=next(c for c in nb['cells'] if ''.join(c['source']).startswith('## 六、学习评价'));body=''.join(c['source']).split('请独立作答；操作完成情况另按本课记录与检查点核对。\n\n')[1].split('\n\n> 参考答案')[0]
 for i,q in enumerate(re.split(r'\n\n(?=[123]\. )',body)):check(code+f' 评价第{i+1}题一致',q in s)
 check(code+' 未登记④通过','待用户确认④' in s or '补验后再确认本稿④' in s)
check('L2第9格用户原文保留',json.loads(next((P/'notebooks').glob('U4-L2*.ipynb')).read_text(encoding='utf-8'))['cells'][8]==json.loads(next((T/'before'/P.relative_to(R)/'notebooks').glob('U4-L2*.ipynb')).read_text(encoding='utf-8'))['cells'][8])
copyfile=P/'notebooks/U5-L2/U5-L2_语音合成.ipynb'
distributed=json.loads(copyfile.read_text(encoding='utf-8'));main=json.loads((P/'notebooks/U5-L2_语音合成.ipynb').read_text(encoding='utf-8'));prior=json.loads((T/'before'/copyfile.relative_to(R)).read_text(encoding='utf-8'))
check('U5-L2发放副本逐格源一致',[c['source'] for c in distributed['cells']]==[c['source'] for c in main['cells']])
check('U5-L2发放副本执行信息保留',[c for c in distributed['cells'] if c['cell_type']=='code']==[c for c in prior['cells'] if c['cell_type']=='code'])
try:nbformat.validate(nbformat.from_dict(copy.deepcopy(distributed)));valid=True
except Exception:valid=False
check('U5-L2发放副本结构',valid)
data={'checks':len(result),'passed':sum(x['passed'] for x in result),'failed':[x for x in result if not x['passed']],'audit':audit,'results':result,'robot_executed':False}
(T/'离线核查结果.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('Checks:',len(result),'Passed:',data['passed'],'Failed:',len(data['failed']))
if data['failed']:raise SystemExit(1)
