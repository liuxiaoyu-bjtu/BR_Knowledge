from pathlib import Path
import json,re,hashlib,subprocess
from p4_content import LESSONS
from build_p4 import source_parts,text

ROOT=Path(__file__).resolve().parents[2]
TASK=Path(__file__).resolve().parent
P=ROOT/'05-internal-materials/vocational-planning/03_X课程项目'
results=[]


def check(name, condition):
    results.append({'check':name,'passed':bool(condition)})


baseline=json.loads((TASK/'基线.json').read_text(encoding='utf-8'))
manifest=json.loads((TASK/'页面与覆盖清单.json').read_text(encoding='utf-8'))
total_pages=total_cells=total_code=total_cp=total_thinking=0
for code,d in LESSONS.items():
    m=manifest[code]
    nb_file=next((P/'notebooks').glob(code+'_*.ipynb'))
    n=json.loads(nb_file.read_text(encoding='utf-8'))
    outline=P/'PPT内容设计'/m['file'];s=outline.read_text(encoding='utf-8')
    mapping={int(k):v for k,v in m['mapping'].items()}
    check(code+'源格数',m['cells']==len(n['cells']))
    check(code+'源代码格数',m['code_cells']==sum(c['cell_type']=='code' for c in n['cells']))
    pages=re.search(r'## 二、逐页设计\n([\s\S]+?)\n## 三、',s).group(1)
    page_rows=[l for l in pages.splitlines() if re.match(r'^\| \d+ \|',l)]
    check(code+'页号连续', [int(l.split('|')[1]) for l in page_rows]==list(range(1,m['pages']+1)))
    for i,c in enumerate(n['cells'],1):
        check(f'{code}第{i}格有页面',bool(mapping[i]) and all(1<=p<=m['pages'] for p in mapping[i]))
        for p in mapping[i]:
            check(f'{code}第{i}格与第{p}页双向一致', i in d['pages'][p-1][4])
        if c['cell_type']=='code':check(f'{code}第{i}代码格列入专表',i in d['code_focus'])
    check(code+'代码专表未虚增',set(d['code_focus'])=={i for i,c in enumerate(n['cells'],1) if c['cell_type']=='code'})
    cps,thinking,tables,evaluation,answers=source_parts(n,d)
    check(code+'检查点原文保留',cps in s)
    check(code+'思考题原文保留',thinking in s)
    check(code+'评价题干选项完整',evaluation in s)
    check(code+'教师答案单列',answers in s.split('### 教师讲者备注，学生页面不显示',1)[1])
    check(code+'页表没有参考答案', '参考答案（教师留存' not in pages)
    for i,table in enumerate(tables,1):check(f'{code}原记录表{i}完整',table.strip() in s)
    goals=re.findall(r'(?m)^\d+\. (.+)$',text(n['cells'][0]))
    for i,goal in enumerate(goals,1):check(f'{code}目标{i}原文保留',goal.replace('|','／') in s)
    check(code+'时间从0到45且连续', d['times'][0][0]==0 and d['times'][-1][1]==45 and all(d['times'][i][1]==d['times'][i+1][0] for i in range(len(d['times'])-1)))
    class_pages=[j for a,b,part,start,end in d['times'] for j in range(start,end+1)]
    check(code+'课堂页面连续无重叠',class_pages==list(range(1,d['times'][-1][4]+1)))
    if d['reading_cell']:
        check(code+'课后阅读单独安排',d['pages'][-1][2]=='课后阅读' and class_pages[-1]==m['pages']-1)
    design=P/'教学设计'/f'{code}_{d["name"]}_教学设计.md'
    original=(TASK/'before'/design.relative_to(ROOT)).read_text(encoding='utf-8')
    current=design.read_text(encoding='utf-8')
    # §三到§四教学时长和全部活动保留；只允许L2一处过期状态说明及末环节清单名称更新。
    original=re.sub(r'(?m)^> 2026-10-30：[^\n]+$', '> STATUS',original,count=1)
    current=re.sub(r'(?m)^> 2026-11-02：[^\n]+$', '> STATUS',current,count=1)
    if code=='U4-L2':
        original=original.replace('第16、19格新增停止路径仍待用户定向真机补验；补验完成前，本教师稿不作为这两格已通过P2的证明。','第16、19格停止路径随本次用户明确确认登记P2通过；保留现有程序和原执行记录，不另补写测试输出。').replace('保留参数、程序版本、退出原因和待补验清单。','保留参数、程序版本、退出原因和个人尚未完成的实操清单。')
    check(code+'已确认教案仅更新阶段文字',original==current)
    check(code+'⑤仍待确认','待确认⑤' in s and '尚未制作P5课件' in s)
    for target in re.findall(r'\]\(([^)]+)\)',s):
        if not re.match(r'^(?:https?://|#)',target):check(code+'文件链接 '+target, (outline.parent/target.split('#')[0]).resolve().exists())
    total_pages+=m['pages'];total_cells+=m['cells'];total_code+=m['code_cells'];total_cp+=m['checkpoints'];total_thinking+=m['thinking_questions']

for rel,meta in baseline.items():
    if rel.endswith('.ipynb') or re.search(r'/_gen_L\d+\.py$',rel):
        check('源文件字节保留 '+rel,hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==meta['sha256'])

check('84页、90格、30代码、12检查、12思考', (total_pages,total_cells,total_code,total_cp,total_thinking)==(84,90,30,12,12))
progress=(P/'X课程当前进度.md').read_text(encoding='utf-8')
distribution=progress.split('## 1. 当前分布',1)[1].split('## 2.',1)[0]
check('全课阶段合计32',sum(int(x) for x in re.findall(r'(?m)^\| [^|]+ \| (\d+) \|',distribution))==32)
check('无当前P2补验或待④分布', 'P2待定向补验 | 1' not in distribution and '待④ | 2' not in distribution)
for code,d in LESSONS.items():
    row=next(l for l in progress.splitlines() if l.startswith('| ['+code+' '))
    check(code+'当前进度P4且③④登记', 'P4逐页大纲' in row and '③④登记' in row and '确认⑤后进入P5' in row)
for folder,pattern,wanted in [('教学设计','U*-L*_教学设计.md',24),('PPT内容设计','U*-L*_PPT内容大纲.md',24),('PPT','U*-L*.pptx',21)]:
    found={re.match(r'(U\d+-L\d+)_',f.name).group(1) for f in (P/folder).glob(pattern)}
    check(folder+'课程覆盖数',len(found)==wanted)
check('用户确认原文可查','U4-L2、L3、L4的P2、P3均确认，可以进行P4' in (P/'PPT内容设计/U4-L2-L3-L4_P4覆盖检查记录.md').read_text(encoding='utf-8'))
check('暂存区未夹带其他工作',not subprocess.check_output(['git','diff','--cached','--name-only']).strip())
failed=[r for r in results if not r['passed']]
summary={'checks':len(results),'passed':len(results)-len(failed),'failed':failed,'totals':{'pages':total_pages,'cells':total_cells,'code_cells':total_code,'goals':9,'checkpoints':total_cp,'thinking_questions':total_thinking,'evaluation_items':9},'results':results}
(TASK/'离线核查结果.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='results'},ensure_ascii=False))
if failed:raise SystemExit(1)
