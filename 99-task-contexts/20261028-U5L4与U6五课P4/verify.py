from pathlib import Path
import ast,hashlib,json,re
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[2];TASK=Path(__file__).resolve().parent
CP=ROOT/'05-internal-materials/vocational-planning/03_X课程项目'
M=json.loads((TASK/'页面与覆盖映射.json').read_text(encoding='utf-8'))
F=json.loads((TASK/'输入指纹.json').read_text(encoding='utf-8'))
checks=[]
def check(ok,msg):
 assert ok,msg
 checks.append(msg)
counts={'pages':0,'cells':0,'code':0,'objectives':0,'checks':0,'questions':0,'evaluation':0}
for key,d in M.items():
 doc=CP/'PPT内容设计'/d['filename'];text=doc.read_text(encoding='utf-8')
 nb=json.loads((CP/'notebooks'/d['notebook']).read_text(encoding='utf-8'))
 for group in ['notebooks','教学设计']:
  path=(CP/group/d['notebook']) if group=='notebooks' else (CP/group/f'{key}_{d["title"]}_教学设计.md')
  rel=path.relative_to(ROOT).as_posix()
  check(hashlib.sha256(path.read_bytes()).hexdigest()==F[rel],key+' '+group+'与输入指纹一致')
 page_rows=[l for l in text.splitlines() if re.match(r'^\| \d+ \|',l)]
 main_rows=page_rows[:d['page_count']]
 check([int(l.split('|')[1]) for l in main_rows]==list(range(1,d['page_count']+1)),key+'页号连续')
 check(all(p['chapter'] and p['title'] and p['subtitle'].startswith('—— ') for p in d['pages']),key+'三层标题齐全')
 check(set(map(int,d['coverage']))==set(range(1,len(nb['cells'])+1)) and all(d['coverage'].values()),key+'全部源格定位')
 check(all(1<=cell<=len(nb['cells']) for p in d['pages'] for cell in p['cells']),key+'无越界格号')
 actual_code={i for i,c in enumerate(nb['cells'],1) if c['cell_type']=='code'}
 mapped_code={cell for page,cell,desc in d['code_map']}
 check(actual_code==mapped_code,key+'代码格全部覆盖且无误指')
 check(all(1<=page<=d['page_count'] for page,cell,desc in d['code_map']),key+'代码页面均存在')
 for n in actual_code:
  ast.parse(''.join(nb['cells'][n-1]['source']))
 check(True,key+'现有代码语法可解析；未执行')
 clock=0
 for start,end,pages,activity in d['times']:
  if not isinstance(start,int):continue
  check(start==clock and end>start,key+'教学时间'+str(start)+'～'+str(end))
  clock=end
 check(clock==45,key+'课堂时间合计45分钟')
 teacher=(CP/'教学设计'/f'{key}_{d["title"]}_教学设计.md').read_text(encoding='utf-8')
 teacher_intervals=[tuple(map(int,m)) for m in re.findall(r'^\| (\d+)–(\d+)min \|',teacher,re.M)]
 expected=[(a,b) for a,b,pages,act in d['times'] if isinstance(a,int)]
 check(teacher_intervals==expected,key+'环节时长与确认教师稿一致')
 for category in ['objective','checks','questions','evaluation']:
  for item in d['items'][category]:check(item in text,key+' '+category+'原文保留 '+item[:18])
 check(all(item in teacher for item in d['items']['objective']),key+'三目标与教师稿一致')
 student_items=text.split('## 七、学生页逐字内容')[1]
 check('答案：' not in student_items and '> 参考答案' not in student_items,key+'学生逐字题目无答案')
 for t in ['check_pages','question_pages','evaluation_pages']:
  check(all(1<=p<=d['page_count'] for p in d['item_pages'][t]),key+' '+t+'有效')
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if target.startswith(('http:','https:','#')):continue
  check((doc.parent/unquote(target.split('#')[0])).exists(),key+'引用存在 '+target)
 for cat in ['objective','checks','questions','evaluation']:
  counts[{'objective':'objectives'}.get(cat,cat)]+=len(d['items'][cat])
 counts['pages']+=d['page_count'];counts['cells']+=d['cell_count'];counts['code']+=d['code_count']
for rel,sha in F.items():
 if '/_gen_' in rel:check(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha,'生成器保留 '+Path(rel).name)
check(counts=={'pages':134,'cells':96,'code':20,'objectives':15,'checks':18,'questions':14,'evaluation':16},'总计数量一致')
report=CP/'PPT内容设计/U5-L4_U6_P4覆盖检查记录.md'
for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
 check((report.parent/unquote(target)).exists(),'报告引用存在 '+target)
# 已审查的U7记录逐行保留；不把它们计入本次提交。
for row in json.loads((TASK/'状态补丁核查.json').read_text(encoding='utf-8')):
 path=ROOT/row['path'];text=path.read_text(encoding='utf-8')
 check(text==(TASK/'reviewed-status'/row['path']).read_text(encoding='utf-8'),'状态补丁一致 '+row['path'])
progress=(CP/'X课程当前进度.md').read_text(encoding='utf-8')
for key in M:
 line=next(l for l in progress.splitlines() if l.startswith('| ['+key+' '))
 check('P4逐页内容大纲已完成，待确认⑤' in line and '④通过' in line,key+'逐课状态更新')
plan=(CP/'X课程开发计划-v4.md').read_text(encoding='utf-8')
for key in M:
 u,l=key.split('-');line=next(row for row in plan.splitlines() if row.startswith('| '+u+' | '+l+' |'))
 check('P4大纲完成待⑤' in line,key+'计划逐课行更新')
result={'result':'通过','checks':len(checks),'counts':counts,'source_files_unchanged':15,'no_robot_execution':True,'no_pptx_produced':True,'details':checks}
(TASK/'校验结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='details'},ensure_ascii=False,indent=2))
