"""Build the four P5 review decks. Notebook JSON is read, never imported or run."""
from pathlib import Path
import re
import json
import math
import hashlib
import unicodedata
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.xmlchemy import OxmlElement
from content import CONTENT

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
FONT = 'Microsoft YaHei'
C = dict(blue='2563EB', teal='0EA5A4', amber='F59E0B', red='E5484D',
         ink='17212B', gray='6B7785', line='D8E0E8', pale='F4F6F9',
         bluebg='EFF6FF', tealbg='CCFBF1', amberbg='FFF7E6', redbg='FEF2F2', white='FFFFFF')
NAMES = ['U4-L1_转向来宾', 'U5-L1_语音识别', 'U5-L2_语音合成', 'U5-L3_LLM对话']
ASSET = PROJECT.parents[1] / '素材库/BOOSTER K1_正面视图.png'

def rgb(c): return RGBColor.from_string(C.get(c, c))
def box(s,x,y,w,h,fill=None,stroke=None,kind=MSO_SHAPE.RECTANGLE):
    q=s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill: q.fill.solid(); q.fill.fore_color.rgb=rgb(fill)
    else: q.fill.background()
    if stroke: q.line.color.rgb=rgb(stroke); q.line.width=Pt(1)
    else: q.line.fill.background()
    return q

def text(s,x,y,w,h,value,size=14.25,ink='ink',bold=False,align=PP_ALIGN.LEFT,font=FONT):
    q=s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf=q.text_frame; tf.clear(); tf.word_wrap=True
    tf.margin_left=tf.margin_right=0; tf.margin_top=tf.margin_bottom=0
    for i,ln in enumerate(str(value).split('\n')):
        p=tf.paragraphs[0] if not i else tf.add_paragraph()
        p.alignment=align; p.space_after=Pt(5); p.line_spacing=1.14
        r=p.add_run(); r.text=ln; r.font.name=font; r.font.size=Pt(size)
        r.font.bold=bold; r.font.color.rgb=rgb(ink)
        ea=OxmlElement('a:ea'); ea.set('typeface',FONT); r._r.get_or_add_rPr().append(ea)
    return q

def line(s,x1,y1,x2,y2,c='line',width=1.3,arrow=False):
    q=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    q.line.color.rgb=rgb(c); q.line.width=Pt(width)
    if arrow:
        end=OxmlElement('a:tailEnd'); end.set('type','triangle'); q.line._get_or_add_ln().append(end)
    return q

def path(s,pts,c='blue',width=1.4):
    # A single editable freeform for each waveform, in PowerPoint coordinates.
    pts=[(round(Inches(x)),round(Inches(y))) for x,y in pts]
    b=s.shapes.build_freeform(*pts[0]); b.add_line_segments(pts[1:],close=False)
    q=b.convert_to_shape(); q.fill.background(); q.line.color.rgb=rgb(c); q.line.width=Pt(width)
    return q

def badge(s,x,y,value,accent='blue'):
    box(s,x,y,.38,.38,accent,kind=MSO_SHAPE.OVAL)
    text(s,x,y+.06,.38,.25,value,11,'white',True,PP_ALIGN.CENTER)

def note(s,value,accent='blue'):
    if not value: return
    box(s,.73,6.04,11.85,.72,{'blue':'bluebg','teal':'tealbg','amber':'amberbg','red':'redbg'}.get(accent,'pale'),kind=MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s,.94,6.18,11.4,.46,value,12.75,'red' if accent=='red' else 'ink')

def theme(row):
    role=row['role']
    if any(v in role for v in ['思考','讨论','检查','总结','阅读','整理','评价']): return 'amber'
    if any(v in role for v in ['代码','操作','实践','实验','记录','收尾','编写']): return 'teal'
    return 'blue'

def base(p,row,total):
    s=p.slides.add_slide(p.slide_layouts[6]); s.background.fill.solid(); s.background.fill.fore_color.rgb=rgb('white')
    a=theme(row); label=row['section']; w=max(1.65,min(6.8,len(label)*.16+.4))
    box(s,.71,.31,w,.34,a,kind=MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s,.83,.355,w-.24,.25,label,11,'white',True,PP_ALIGN.CENTER)
    text(s,.71,.85,11.88,.59,row['title'],25.5,bold=True)
    text(s,.71,1.48,11.88,.37,row['subtitle'],13.5,'gray')
    text(s,11.77,7.08,.85,.23,f"{row['n']} / {total}",8.25,'gray',align=PP_ALIGN.RIGHT)
    return s,a

def cover(p,row,total,name):
    s,a=base(p,dict(row,title='',subtitle='',section=row['section']),total)
    text(s,.75,2.08,8,.76,row['title'],34.5,bold=True)
    text(s,.75,2.99,8,.65,row['subtitle'],16.5,'gray')
    unit='U4 · 视觉引导运动' if name.startswith('U4') else 'U5 · 语音交互'
    text(s,.75,6.35,7,.31,unit,14.25,'blue',True)
    text(s,.75,6.69,7,.25,name.split('_')[0]+'  /  具身智能应用开发',12.75,'gray')
    s.shapes.add_picture(str(ASSET),Inches(9.1),Inches(1.07),height=Inches(5.62))
    text(s,9.05,6.74,3.3,.23,'K1 外观 · 产品渲染图',9.5,'gray',align=PP_ALIGN.CENTER)
    return s

def parse_outline(path):
    rows=[]
    for ln in path.read_text(encoding='utf-8').splitlines():
        cells=[c.strip() for c in ln.strip('|').split('|')]
        if ln.startswith('|') and len(cells)==6 and cells[0].isdigit():
            rows.append(dict(zip(['n','section','title','subtitle','role','core'],[int(cells[0])]+cells[1:])))
    assert [r['n'] for r in rows]==list(range(1,len(rows)+1))
    return rows

def extract(nb,spec):
    cells=spec['cell'] if isinstance(spec['cell'],list) else [spec['cell']]
    all_lines=[]; mapped=[]; found=set()
    for cid in cells:
        cell=nb['cells'][cid-1]; assert cell['cell_type']=='code'
        src=''.join(cell['source']).splitlines(); selected=[]
        for i,ln in enumerate(src):
            hit=[k for k in spec['keys'] if ln.startswith(k)]
            if hit: selected.append((i,ln)); found.update(hit)
        prior=-2
        for i,ln in selected:
            if all_lines and i>prior+1: all_lines.append('...')
            all_lines.append(ln); mapped.append(dict(cell=cid,line=i+1,text=ln)); prior=i
    missing=set(spec['keys'])-found
    assert not missing, f'Unmatched code selectors: {missing}'
    return all_lines,mapped

def compare(s,items,a):
    n=len(items); cols=2 if n in (2,4) else 3 if n==3 else 1
    w=(11.85-(cols-1)*.45)/cols
    for i,item in enumerate(items):
        x=.75+(i%cols)*(w+.45); y=2.32+(i//cols)*1.70
        badge(s,x,y,str(i+1),a)
        head,sep,body=str(item).partition('\n')
        text(s,x+.55,y+.02,w-.55,.57,head,16.5,a,True)
        text(s,x,y+.68,w,1.0 if n<=3 else .90,body if sep else '',14.25)

def flow(s,items,a):
    n=len(items); gap=.28; w=(11.85-gap*(n-1))/n
    for i,item in enumerate(items):
        x=.75+i*(w+gap)
        badge(s,x,2.65,str(i+1),a)
        box(s,x,3.25,w,1.30,{'blue':'bluebg','teal':'tealbg','amber':'amberbg'}[a],kind=MSO_SHAPE.ROUNDED_RECTANGLE)
        text(s,x+.12,3.68,w-.24,.70,item,14.25,bold=True,align=PP_ALIGN.CENTER)
        if i<n-1: line(s,x+w+.035,3.90,x+w+gap-.04,3.90,a,1.5,True)

def table(s,headers,data,a):
    n=len(headers); weights=[1]*n
    if n>=3: weights=[.85]+[1.6]*(n-1)
    if headers[0]=='选读配置': weights=[4.7,3.5,3.65]
    total=sum(weights); widths=[11.85*w/total for w in weights]
    y=2.35; headh=.68; rh=min(.70,2.75/max(1,len(data)))
    x=.75
    for i,h in enumerate(headers):
        box(s,x,y,widths[i],headh,{'blue':'bluebg','teal':'tealbg','amber':'amberbg'}[a])
        text(s,x+.13,y+.14,widths[i]-.26,.49,h,12.75,a,True); x+=widths[i]
    y+=headh
    for r,row in enumerate(data):
        x=.75
        for i,v in enumerate(row):
            if r%2==0: box(s,x,y,widths[i],rh,'pale')
            text(s,x+.13,y+.15,widths[i]-.26,rh-.18,str(v),12.75)
            x+=widths[i]
        line(s,.75,y+rh,12.6,y+rh,'line',.7); y+=rh

def render_code(s,spec,lines,a):
    columns=max(sum(2 if unicodedata.east_asian_width(ch) in ('W','F') else 1 for ch in ln) for ln in lines)
    long=columns>70 or len(lines)>13
    x=.75; y=2.28; w=11.85 if long else 7.65
    size=10.5 if columns>124 or len(lines)>16 else 12
    h=min(3.48,max(2.25,len(lines)*size*1.22/72+.46))
    box(s,x,y,w,h,'pale',kind=MSO_SHAPE.ROUNDED_RECTANGLE)
    codebox=text(s,x+.20,y+.17,w-.4,h-.28,'\n'.join(lines),size,font='Consolas')
    codebox.text_frame.word_wrap=False
    for p in codebox.text_frame.paragraphs: p.space_after=Pt(0); p.line_spacing=Pt(size*1.22)
    cid=str(spec['cell']); text(s,x,y-.30,w,.24,'Notebook · 第'+cid+'格 · 关键摘录',10.5,'gray')
    if long:
        text(s,.77,y+h+.12,11.7,.78,'  /  '.join(spec['items']),12.75)
    else:
        for i,item in enumerate(spec['items']):
            badge(s,8.86,2.47+i*1.38,str(i+1),a)
            text(s,9.39,2.50+i*1.38,3.10,1.12,item,14.25,bold=i==0)

def wave(s,x,y,w,h,f=440,mode='sine',samples=False):
    line(s,x,y+h/2,x+w,y+h/2,'line',.8)
    line(s,x,y,x,y+h,'line',.8)
    pts=[]
    for i in range(161):
        t=i/160*.01; phase=f*t
        if mode=='square': val=1 if math.sin(2*math.pi*phase)>=0 else -1
        elif mode=='sawtooth': val=2*(phase%1)-1
        elif mode=='bell': val=(math.sin(2*math.pi*phase)+.5*math.sin(4*math.pi*phase))*math.exp(-20*t)
        else: val=math.sin(2*math.pi*phase)
        pts.append((x+w*i/160,y+h/2-val*h*.29))
    path(s,pts,'blue',1.5)
    if samples:
        for px,py in pts[::4]: box(s,px-.025,py-.025,.05,.05,'teal',kind=MSO_SHAPE.OVAL)

def big_formula(s,items,a):
    box(s,.75,2.50,11.85,1.06,{'blue':'bluebg','teal':'tealbg','amber':'amberbg'}[a],kind=MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s,1.02,2.82,11.3,.55,items[0],22.5,a,True,PP_ALIGN.CENTER)
    for i,item in enumerate(items[1:]):
        text(s,.90+i*5.9,4.10,5.5,.84,item,16.5,bold=True)

def assessment(s,items,a,questions=False):
    n=len(items); y=2.35
    for i,item in enumerate(items):
        if questions:
            h=1.32 if n>1 else 2.10; f=18 if n==1 else 16.5
            box(s,.75,y,11.85,h,'amberbg',kind=MSO_SHAPE.ROUNDED_RECTANGLE)
            text(s,1.02,y+.23,11.25,h-.30,item,f)
        else:
            h=.78 if n==4 else 1.02
            box(s,.79,y+.13,.23,.23,None,'amber')
            text(s,1.20,y,11.1,h-.06,item,14.25)
        y+=h+.16
    if questions:
        text(s,.78,5.42,11.8,.4,'结合本课代码与实际观察说明依据。',13.5,'gray')

def render_special(s,k,items,a):
    if k in ('formula','pcm','tonebytes'): big_formula(s,items,a)
    elif k=='offset':
        box(s,.85,2.30,7.4,3.05,'pale','line')
        line(s,4.55,2.30,4.55,5.35,'gray',1)
        box(s,6.1,3.0,.70,1.5,None,'teal'); box(s,6.31,2.75,.28,.26,'teal')
        line(s,4.55,4.92,6.45,4.92,'blue',2,True)
        text(s,3.73,2.46,1.8,.30,'画面中线',12,'gray')
        text(s,5.06,4.44,2,.30,'error > 0',14.25,'blue',True)
        for i,t in enumerate(items): text(s,8.75,2.55+i*.93,3.8,.85,t,16.5 if i==0 else 14.25,bold=i==0)
    elif k=='axes':
        for i,(lab,direction) in enumerate([('画面坐标 x','right'),('头部水平角 yaw','left')]):
            x=1+i*5.9; text(s,x,2.35,5,.4,lab,16.5,'blue',True)
            box(s,x+1.8,3.31,.8,.9,'pale','line',MSO_SHAPE.OVAL)
            if direction=='right': line(s,x+.5,4.55,x+4.4,4.55,'blue',2,True)
            else: line(s,x+4.4,4.55,x+.5,4.55,'blue',2,True)
            text(s,x+.5,4.94,4.5,.6,items[i],14.25)
        text(s,1,5.60,11,.35,items[2],13.5,'gray')
    elif k=='headbody':
        box(s,2.2,3.5,2.5,1.4,'pale','line',MSO_SHAPE.OVAL)
        box(s,3,3.65,.9,.9,'bluebg','blue',MSO_SHAPE.OVAL)
        line(s,3.45,4.10,3.45,2.48,'blue',2,True)
        line(s,3.45,4.10,5.55,2.65,'teal',2,True)
        start=-math.pi/2; end=math.atan2(-1.45,2.1)
        path(s,[(3.45+1.12*math.cos(start+(end-start)*i/24),4.10+1.12*math.sin(start+(end-start)*i/24)) for i in range(25)],'teal',1.5)
        text(s,3.95,3.04,.5,.4,'θ',16.5,'teal')
        box(s,5.35,2.42,.3,.3,'teal',kind=MSO_SHAPE.OVAL)
        text(s,1.25,2.18,2.1,.4,'身体正前方',13.5,'blue')
        text(s,5.28,2.08,2.3,.4,'目标方向',13.5,'teal')
        text(s,4.03,4.30,3.0,.7,'头相对身体的角度',13.5)
        text(s,8.1,2.66,4.2,2.4,'头相对身体转动\n\n身体转动后，身体朝向也会改变。',18)
    elif k=='feedback':
        for x,y,w,t in [(.85,2.6,2.55,items[0]),(4.5,2.6,3.3,items[1]),(9,2.6,3.3,items[2]),(9,4.45,3.3,items[3])]:
            box(s,x,y,w,.85,'bluebg',kind=MSO_SHAPE.ROUNDED_RECTANGLE); text(s,x+.12,y+.27,w-.24,.4,t,16.5,bold=True,align=PP_ALIGN.CENTER)
        text(s,.95,3.68,2.5,.4,'循环前，仅一次',12,'gray')
        line(s,3.4,3.03,4.5,3.03,'blue',1.5,True); line(s,7.8,3.03,9,3.03,'blue',1.5,True)
        line(s,10.65,3.45,10.65,4.45,'blue',1.5,True)
        line(s,9,4.87,6.15,4.87,'blue',1.5); line(s,6.15,4.87,6.15,3.45,'blue',1.5,True)
        text(s,4.7,5.3,3.1,.4,'下一轮使用新画面',12,'gray')
    elif k in ('sampling','samplingrate'):
        wave(s,1.0,2.8,7.0,2.1,samples=True)
        text(s,1.0,5.17,7,.35,'时间 →   连续曲线与离散样点：概念示意',12,'gray')
        for i,t in enumerate(items): text(s,8.75,2.65+i*.96,3.75,.78,t,16.5 if k=='samplingrate' else 14.25,bold=i==0)
    elif k=='chunks':
        wave(s,1,2.45,11.2,1.2)
        for i in range(10):
            box(s,1+i*1.12,4.02,1.0,.55,'tealbg','teal'); text(s,1+i*1.12,4.18,1,.3,str(i+1),12,'teal',True,PP_ALIGN.CENTER)
        for i,t in enumerate(items): text(s,.95+i*4,5.07,3.85,.5,t,14.25,bold=True)
    elif k=='queue':
        text(s,.9,2.7,2.2,.7,items[0],18,'blue',True)
        for i in range(5):
            box(s,4+i*.72,3.08,.62,1.04,'bluebg','blue'); text(s,4+i*.72,3.40,.62,.35,str(i+1),14.25,'blue',True,PP_ALIGN.CENTER)
        line(s,3.05,3.6,3.77,3.6,'blue',1.5,True); line(s,7.75,3.6,8.45,3.6,'blue',1.5,True)
        text(s,4.1,4.56,3.6,.4,items[1],16.5,bold=True)
        text(s,8.8,3.28,3.6,.9,items[2],16.5,bold=True)
    elif k=='files':
        for i,t in enumerate(items):
            box(s,1.02,2.42+i*.93,.44,.54,'tealbg','teal')
            text(s,1.8,2.50+i*.93,10,.54,t,18,font='Consolas')
        text(s,8.1,5.25,4.1,.35,'同一发放目录，保留相对位置',13.5,'gray')
    elif k=='waves':
        for i,(lab,mode) in enumerate(zip(items,['sine','square','sawtooth','bell'])):
            x=.88+(i%2)*6; y=2.23+(i//2)*1.77
            text(s,x,y,5.3,.3,lab,13.5,'blue',True)
            wave(s,x+.3,y+.40,4.9,.9,mode=mode)
            text(s,x+.3,y+1.32,4.9,.25,'0                                      10 ms',10.5,'gray')
    elif k=='async':
        for i,t in enumerate(items[:2]):
            y=2.55+i*1.25; text(s,.9,y,11.5,.43,t,16.5,bold=True)
            line(s,1.2,y+.75,11.7,y+.75,'line',1.5,True)
            box(s,2,y+.57,6 if i==0 else 1.1,.36,'bluebg','blue')
            text(s,8.3 if i==0 else 3.4,y+.53,3.5,.48,'工作完成后返回' if i==0 else '先返回句柄，任务继续',12.75,'blue')
        text(s,.92,5.38,11,.42,items[2],14.25,'gray')
    elif k=='session':
        text(s,.9,2.38,11.6,.55,items[0],22.5,'blue',True)
        line(s,1,4.06,12,4.06,'blue',2,True)
        for i,t in enumerate(['启动会话','第1轮问答','第2轮问答','请求取消','确认终态']):
            x=1.1+i*2.55; box(s,x,3.95,.22,.22,'blue',kind=MSO_SHAPE.OVAL); text(s,x-.67,4.48,1.95,.6,t,13.5,align=PP_ALIGN.CENTER)
        text(s,1,3.26,10.6,.4,'同一个持续任务跨越多轮问答',16.5,bold=True)
        text(s,1,5.37,11,.4,items[2],16.5,'blue',True)
    elif k in ('promptlab','promptmine'):
        labels=['身份与语气','已知资料','回答范围','限制与处理']
        for i,(lab,t) in enumerate(zip(labels,items)):
            y=2.25+i*.83
            text(s,.8,y+.12,1.75,.4,lab,13.5,'teal',True)
            box(s,2.85,y,9.75,.70,'pale',kind=MSO_SHAPE.ROUNDED_RECTANGLE)
            text(s,3.04,y+.12,9.35,.50,t,13.5)
    elif k=='context':
        for i,t in enumerate(items[:3]):
            y=2.40+i*1.0; box(s,1,y,4.25,.65,'bluebg',kind=MSO_SHAPE.ROUNDED_RECTANGLE)
            text(s,1.2,y+.20,3.85,.4,t,16.5,bold=True)
            line(s,5.4,y+.33,7.15,3.73,'blue',1.5,True)
        box(s,7.6,3.12,4.6,1.30,'pale',kind=MSO_SHAPE.ROUNDED_RECTANGLE)
        text(s,7.85,3.51,4.1,.6,items[3],18,bold=True)
    elif k=='revision':
        table(s,['修改记录','本组填写'],[[t,''] for t in items],a)
    elif k=='tokens':
        flow(s,items,a); text(s,1,5.23,11,.45,'文字按片段逐步生成；片段不一定等于一个汉字或一个词。',14.25,'gray')
    else: raise ValueError(k)

def section_bullets(nb,heading):
    source='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='markdown')
    m=re.search(r'###\s+[\d.]+\s*'+heading+r'\s*\n([\s\S]*?)(?=\n#{1,3}\s|\Z)',source)
    assert m,heading
    return [re.sub(r'`([^`]*)`',r'\1',re.sub(r'^\[__\]\s*', '', l[2:].strip())) for l in m.group(1).splitlines() if l.startswith('- ')]

def quiz_questions(nb):
    source = next(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='markdown' and re.match(r'^## [六七]、学习评价', ''.join(c['source'])))
    body = source.split('请独立作答；操作完成情况另按本课记录与检查点核对。\n\n')[1].split('\n\n> 参考答案')[0]
    return [re.sub(r'`([^`]*)`', r'\1', q) for q in re.split(r'\n\n(?=[123]\. )', body)]

def render_quiz(s, nb, accent):
    y = 2.15
    for question, height in zip(quiz_questions(nb), [0.85, 1.10, 2.30]):
        box(s, .75, y, 11.85, height, 'amberbg', kind=MSO_SHAPE.ROUNDED_RECTANGLE)
        text(s, .98, y+.10, 11.38, height-.15, question, 14.25)
        y += height + .15

def main():
    manifest=[]
    for name in NAMES:
        lesson=name.split('_')[0]; outline=PROJECT/'PPT内容设计'/(name+'_PPT内容大纲.md')
        nbpath=PROJECT/'notebooks'/(name+'.ipynb'); nbbytes=nbpath.read_bytes(); nb=json.loads(nbbytes)
        rows_=parse_outline(outline); expected=28 if lesson in ('U4-L1','U5-L1') else 29
        assert len(rows_)==expected
        p=Presentation(); p.slide_width=Inches(13.3333333); p.slide_height=Inches(7.5)
        p.core_properties.title=name; p.core_properties.subject='P5审查版；确认⑥待用户审阅'
        p.core_properties.author='Booster Robotics'; page_map=[]
        teacher=(PROJECT/'教学设计'/(name+'_教学设计.md')).read_text(encoding='utf-8')
        for row in rows_:
            n=row['n']; mapping=[]
            if n==1: s=cover(p,row,len(rows_),name); spec={'kind':'cover'}
            else:
                spec=CONTENT[lesson][n]; s,a=base(p,row,len(rows_)); k=spec['kind']
                if k=='compare': compare(s,spec['items'],a)
                elif k=='flow': flow(s,spec['items'],a)
                elif k=='table': table(s,spec['headers'],spec['data'],a)
                elif k=='code':
                    lines,mapping=extract(nb,spec); render_code(s,spec,lines,a)
                elif k=='quiz': render_quiz(s,nb,a)
                elif k=='checks': assessment(s,section_bullets(nb,'检查点'),a)
                elif k=='questions': assessment(s,[section_bullets(nb,'思考题')[i] for i in spec['items']],a,True)
                else: render_special(s,k,spec.get('items',()),a)
                note(s,spec.get('note',''),'red' if lesson=='U4-L1' and (n==3 or row['section']=='安全收尾') else a)
            notes=f"P4来源：{outline.name} 第{n}页。\n内容蓝本：{row['core']}\nNotebook：{nbpath.name}（格号从1计，包含Markdown）。\n"
            if mapping: notes+='代码逐行出处：\n'+'\n'.join(f"格{v['cell']} 行{v['line']}：{v['text']}" for v in mapping)+'\n代码中的 ... 表示省略，完整代码在 Notebook。\n'
            notes+='图示：PowerPoint原生形状，可编辑；概念示意，不代表实验实测。\n'
            if n==1: notes+='外观图来源：05-internal-materials/素材库/BOOSTER K1_正面视图.png；素材台账标为产品渲染图，非真机实拍；仅等比缩放。公开分发授权范围待核。\n'
            if spec['kind'] in ('checks','questions','quiz'):
                m=re.search(r'(?m)^##\s*六[、.．][\s\S]*?(?=^##\s*七|\Z)',teacher)
                if m: notes+='教师评价与参考（不在学生页展示）：\n'+m.group(0)
            faq=re.search(r'(?m)^##\s*[^\n]*FAQ[^\n]*\n([\s\S]*?)(?=^##\s|\Z)',teacher)
            if faq: notes+='教师FAQ备查：\n'+faq.group(1)
            s.notes_slide.notes_text_frame.text=notes
            page_map.append(dict(page=n,title=row['title'],role=row['role'],layout=spec['kind'],code=mapping))
        out=PROJECT/'PPT'/(name+'_Codex审查版.pptx'); p.save(out)
        item=dict(name=name,output=str(out),slides=len(p.slides),notebook_sha256=hashlib.sha256(nbbytes).hexdigest(),pages=page_map)
        (HERE/(name+'_page-map.json')).write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding='utf-8')
        dump='\n\n'.join('## '+str(i+1)+' '+rows_[i]['title']+'\n\n'+'\n'.join(q.text for q in slide.shapes if q.has_text_frame) for i,slide in enumerate(p.slides))
        (HERE/(name+'_成品文字提取.md')).write_text(dump,encoding='utf-8')
        manifest.append(item); print(out,len(p.slides))
    (HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__': main()
