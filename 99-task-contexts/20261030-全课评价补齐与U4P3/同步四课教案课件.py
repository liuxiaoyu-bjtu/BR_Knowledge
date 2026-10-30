from pathlib import Path
import json,re,runpy,pprint,hashlib
R=Path(__file__).resolve().parents[2];P=R/'05-internal-materials/vocational-planning/03_X课程项目';T=Path(__file__).resolve().parent
S=P/'PPT/U4L1_U5L1-L3_Codex源文件'

def quiz(nb):
 c=next(c for c in nb['cells'] if c['cell_type']=='markdown' and re.match(r'^## [六七]、学习评价',''.join(c['source'])))
 s=''.join(c['source']);return s.split('请独立作答；操作完成情况另按本课记录与检查点核对。\n\n')[1].split('\n\n> 参考答案')[0],s.split('\n> 参考答案')[1].split('\n> ',1)[1].strip()

positions={'U4-L1':26,'U5-L1':27,'U5-L2':27,'U5-L3':27}
for code,at in positions.items():
 nbfile=next((P/'notebooks').glob(code+'*.ipynb'));nb=json.loads(nbfile.read_text(encoding='utf-8'));qs,ans=quiz(nb)
 teacher=next((P/'教学设计').glob(code+'*'));s=teacher.read_text(encoding='utf-8-sig')
 # 先调整现有课件页码，插页后的所有投影定位和教学时间不遗漏。
 def pages(m):
  first=int(m.group(1));second=m.group(3)
  return '第'+str(first+(first>=at))+(m.group(2)+str(int(second)+(int(second)>=at)) if second else '')+'页'
 s=re.sub(r'第(\d+)([～–—\-](\d+))?页',lambda m: pages(m) if False else '第'+str(int(m.group(1))+(int(m.group(1))>=at))+(m.group(2)[0]+str(int(m.group(3))+(int(m.group(3))>=at)) if m.group(3) else '')+'页',s)
 if code in ('U5-L2','U5-L3'): s=s.replace('§六','§七')
 # 学习评价前补入独立测验；原过程评价与思考参考保持。
 a=s.index('## 六、学习评价');b=s.find('\n## 七',a);end=b if b>=0 else len(s)
 old=s[a+len('## 六、学习评价'):end].strip()
 if code=='U4-L1':old=old.replace('题目采用 Notebook §5.3检查点与§5.4思考题；教师结合§5.1、§5.2的实际记录判断，不另设计时达标题。','过程评价采用Notebook§5.3检查点与§5.4思考题，结合§5.1、§5.2实测判断。')
 qparts=re.split(r'\n\n(?=[123]\. )',qs);aparts=[x for x in re.split(r'(?=[123]\. )',ans) if x]
 tests='\n\n'.join(q+'\n\n**参考答案：** '+re.sub(r'^[123]\. ','',v) for q,v in zip(qparts,aparts))
 section='## 六、学习评价\n\n### 独立测验\n\n与Notebook新增学习评价逐题一致；学生课件仅显示题干，答案放教师备注，P6学生PDF删除答案。\n\n'+tests+'\n\n### 过程评价与思考参考\n\n'+old+'\n'
 s=s[:a]+section+s[end:]
 s=s.replace('Notebook保持原稿。','本次只补学习评价与检查点格式，代码和执行信息保留。')
 oldpages=27 if code in ('U4-L1','U5-L1') else 28
 s=s.replace(str(oldpages)+'页Codex审查版',str(oldpages+1)+'页Codex审查版')
 s+='\n> 2026-10-30评价补充：末环节留约2分钟独立完成三题，口头思考选一题、其余随记录课后补答；安全收尾时间保留。新增学习评价投影为第'+str(at)+'页；原后续页码已顺延，确认⑥仍待用户审阅。\n'
 teacher.write_text(s,encoding='utf-8',newline='\n')
 outline=next((P/'PPT内容设计').glob(code+'*_PPT内容大纲.md'));s=outline.read_text(encoding='utf-8-sig');lines=s.splitlines();out=[];inserted=False
 qcell=next(i+1 for i,c in enumerate(nb['cells']) if c['cell_type']=='markdown' and re.match(r'^## [六七]、学习评价',''.join(c['source'])))
 for line in lines:
  cols=[x.strip() for x in line.strip('|').split('|')]
  if line.startswith('|') and len(cols)==6 and cols[0].isdigit():
   n=int(cols[0])
   if n==at:
    out.append(f'| {at} | 学习评价 | 独立完成三道题 | —— 用本课概念判断实际情境 | 学习评价 | Notebook第{qcell}格全部三题原文；判断、填空、选择，保留作答空位。答案仅在讲者备注，约2分钟，过程能力仍按记录判断。 |');inserted=True
   if n>=at: cols[0]=str(n+1)
   line='| '+' | '.join(cols)+' |'
  out.append(line)
 assert inserted
 s='\n'.join(out)+'\n'
 # 旧扩展阅读的章号和格号顺延；原代码格号保持。
 if code in ('U5-L2','U5-L3'):
  s=s.replace('§六','§七').replace('§6全文','§7全文')
  oldcell=34 if code=='U5-L2' else 32
  s=s.replace(f'格{oldcell}§',f'格{oldcell+1}§').replace(f'格{oldcell} §',f'格{oldcell+1} §')
  s=re.sub(rf'第{oldcell}格(?=[^\n]*扩展阅读)',f'第{oldcell+1}格',s)
  # 页面清单的阅读依据通常为“格34§六”；全行再定向校正。
  s='\n'.join(re.sub(rf'格{oldcell}(?=[^0-9])',f'格{oldcell+1}',ln) if '阅读导引' in ln else ln for ln in s.splitlines())+'\n'
 s=re.sub(r'Notebook共\d+格',f'Notebook共{len(nb["cells"])}格',s)
 s+='\n> 2026-10-30：新增第'+str(at)+'页学习评价，三题与Notebook一致；本课现为'+str(28 if code in ('U4-L1','U5-L1') else 29)+'页。末环节分配约2分钟测验，思考题其余课后补答；教学设计投影定位及生成源同步。\n'
 outline.write_text(s,encoding='utf-8',newline='\n')

# 生成源保留所有旧页面内容，只增加测验渲染与位置映射。
content=(S/'content.py').read_text(encoding='utf-8')
content=content.replace('课后阅读 §六','课后阅读 §七')
content+='\n# 2026-10-30：插入独立测验，既有页顺延。题目从Notebook读取。\nQUIZ_POSITIONS = '+repr(positions)+'\nfor _lesson, _at in QUIZ_POSITIONS.items():\n    CONTENT[_lesson] = {_n + (_n >= _at): _spec for _n, _spec in CONTENT[_lesson].items()}\n    CONTENT[_lesson][_at] = dict(kind="quiz", note="")\n'
(S/'content.py').write_text(content,encoding='utf-8',newline='\n')
build=(S/'build.py').read_text(encoding='utf-8')
build=build.replace("['思考','讨论','检查','总结','阅读','整理']","['思考','讨论','检查','总结','阅读','整理','评价']")
build=build.replace("expected=27 if lesson in ('U4-L1','U5-L1') else 28","expected=28 if lesson in ('U4-L1','U5-L1') else 29")
build=build.replace("l[2:].strip()) for l in", "re.sub(r'^\\[__\\]\\s*', '', l[2:].strip())) for l in")
marker='def main():\n'
extra='''def quiz_questions(nb):
    source = next(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='markdown' and re.match(r'^## [六七]、学习评价', ''.join(c['source'])))
    body = source.split('请独立作答；操作完成情况另按本课记录与检查点核对。\\n\\n')[1].split('\\n\\n> 参考答案')[0]
    return [re.sub(r'`([^`]*)`', r'\\1', q) for q in re.split(r'\\n\\n(?=[123]\\. )', body)]

def render_quiz(s, nb, accent):
    y = 2.15
    for question, height in zip(quiz_questions(nb), [0.85, 1.10, 2.30]):
        box(s, .75, y, 11.85, height, 'amberbg', kind=MSO_SHAPE.ROUNDED_RECTANGLE)
        text(s, .98, y+.10, 11.38, height-.15, question, 14.25)
        y += height + .15

'''
assert marker in build;build=build.replace(marker,extra+marker)
build=build.replace("elif k=='checks': assessment", "elif k=='quiz': render_quiz(s,nb,a)\n                elif k=='checks': assessment")
build=build.replace("in ('checks','questions'):","in ('checks','questions','quiz'):")
(S/'build.py').write_text(build,encoding='utf-8',newline='\n')
print('已同步四课教学设计、大纲与课件生成源')
