"""Compose the reviewed teaching illustration and a versioned PPTX, preserving other slides."""
from pathlib import Path
import json, zipfile, math, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from xml.sax.saxutils import escape
from defusedxml import minidom

B=Path(__file__).resolve().parent; O=B/'source'
R=next(p for p in B.parents if (p/'INDEX.md').exists()); P=R/'05-internal-materials/vocational-planning/03_X课程项目/PPT'
DEST=P/'U3_Codex源文件/assets/U3-L1-p19'; DEST.mkdir(parents=True,exist_ok=True)
T='#0EA5A4';INK='#17212B';GRAY='#6B7785';WHITE='#FFFFFF'
fontpath='C:/Windows/Fonts/msyh.ttc'
def font(n):return ImageFont.truetype(fontpath,int(n))

# Replace the blank generated blade with a deterministic millimetre scale.
scene=Image.open(O/'scene-no-tape-post.png').convert('RGBA')
tape=Image.open(O/'tape-0-220cm-transparent.png').convert('RGBA').crop((80,40,5480,335))
src=[(0,0),(tape.width,0),(tape.width,tape.height),(0,tape.height)]
dst=[(574,752),(1454,657),(1454,685),(574,783)]
A=[];bb=[]
for (x,y),(u,v) in zip(dst,src):
    A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);bb.extend([u,v])
coeff=np.linalg.solve(np.array(A,float),np.array(bb,float))
warped=tape.transform(scene.size,Image.Transform.PERSPECTIVE,coeff,Image.Resampling.BICUBIC)
scene.alpha_composite(warped)
scene.convert('RGB').save(DEST/'scene-final.png')
detail=Image.open(O/'tape-0-220cm-transparent.png').convert('RGBA').crop((42,35,725,352))
detailbg=Image.new('RGB',detail.size,'white');detailbg.paste(detail,mask=detail.getchannel('A'))
detailbg.save(DEST/'tape-detail.png')
shutil.copy2(O/'depth-clean.png',DEST/'depth-clean.png')

# All annotations are also emitted as editable PowerPoint text and line objects.
W,H=3200,1260; nodes=[]
def img(name,x,y,w,h):nodes.append(dict(kind='image',file=name,x=x,y=y,w=w,h=h))
def txt(s,x,y,size=44,color=INK,bold=False,bg=None):
    box=ImageDraw.Draw(Image.new('RGB',(1,1))).textbbox((0,0),s,font=font(size))
    nodes.append(dict(kind='text',text=s,x=x,y=y,w=box[2]+22,h=size*1.45,size=size,color=color,bold=bold,bg=bg))
def line(x1,y1,x2,y2,color=T,width=4,dash=False):nodes.append(dict(kind='line',x=x1,y=y1,x2=x2,y2=y2,color=color,width=width,dash=dash))
def rect(x,y,w,h,fill,stroke=None):nodes.append(dict(kind='rect',x=x,y=y,w=w,h=h,fill=fill,stroke=stroke))
def dot(x,y):nodes.append(dict(kind='dot',x=x,y=y,r=8,fill=T))
img('scene-final.png',0,64,1760,1173)
txt('实验摆位 · 侧面观察',0,0,48,bold=True)
txt('目标深度示意 · K1视角',1830,0,48,bold=True)
img('depth-clean.png',1830,90,1370,1027.5)

# Camera ray and displaced tape zero reference. This identifies planes, not a calibrated metric.
sf=1760/2496
def pp(x,y):return x*sf,64+y*sf
cam=pp(515,606); target=pp(1443,486); hook=pp(574,770)
line(*cam,*target,T,4,True)
line(cam[0],cam[1],hook[0],hook[1],T,3,True)
dot(*cam)
tx,ty=target
line(tx-17,ty,tx+17,ty,T,4);line(tx,ty-17,tx,ty+17,T,4)
txt('K1相机',425,350,44,T,True,WHITE)
line(425,413,*cam,T,3)
txt('纸箱正面',970,260,44,T,True,WHITE)
line(1000,321,*target,T,3)
txt('后方瓶子',1430,240,42,INK,False,WHITE)
line(1550,302,*pp(2310,560),T,3)
txt('机身固定',24,760,42,INK,False,WHITE)
line(160,823,*pp(230,1160),T,3)
txt('卷尺：相机参考面 → 纸箱正面',460,660,42,T,True,WHITE)
line(650,655,*pp(1010,720),T,3)

# A magnified excerpt makes the real 1 mm/1 cm scale legible at slide size.
rect(470,900,720,305,WHITE,'#D8E0E8')
txt('尺带刻度细节',490,910,38,INK,True)
img('tape-detail.png',490,970,680,190)
txt('距离读数由学生现场填写',490,1163,34,GRAY)

# The depth image itself is unmodified grayscale; overlays are semantic annotations.
cx,cy=1830+1370/2,90+1027.5/2
line(cx-24,cy,cx+24,cy,T,5);line(cx,cy-24,cx,cy+24,T,5)
txt('(W//2, H//2)',cx+35,cy+24,39,T,True)
txt('正面同距，灰度一致',2225,395,44,INK,True)
txt('瓶子更远',2910,430,38,'#FFFFFF')
line(3030,493,3070,540,'#FFFFFF',3)
for i in range(460):
    g=round(255*(1-i/459));rect(1830+i,1140,1,30,'#%02X%02X%02X'%(g,g,g))
txt('近',1830,1171,37);txt('远',2250,1171,37)
txt('越近越白，越远越黑',2380,1138,42,INK,True)
txt('彩色坐标未确认配准时不可套用',1830,1210,40,GRAY)

# Raster export, used as the insertable illustration and high-resolution QA reference.
canvas=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(canvas)
for n in nodes:
    k=n['kind'];x=n['x'];y=n['y']
    if k=='image':
        im=Image.open(DEST/n['file']).convert('RGB').resize((round(n['w']),round(n['h'])),Image.Resampling.LANCZOS);canvas.paste(im,(round(x),round(y)))
    elif k=='text':
        if n['bg']:d.rounded_rectangle((x-8,y-2,x+n['w'],y+n['h']-7),radius=6,fill=n['bg'])
        d.text((x,y-6),n['text'],font=font(n['size']),fill=n['color'],stroke_width=1 if n['bold'] else 0)
    elif k=='rect':d.rectangle((x,y,x+n['w'],y+n['h']),fill=n['fill'],outline=n['stroke'],width=2)
    elif k=='dot':d.ellipse((x-n['r'],y-n['r'],x+n['r'],y+n['r']),fill=n['fill'])
    elif k=='line':
        if n['dash']:
            dx=n['x2']-x;dy=n['y2']-y;dist=math.hypot(dx,dy)
            for v in np.arange(0,dist,24):
                end=min(v+13,dist);d.line((x+dx*v/dist,y+dy*v/dist,x+dx*end/dist,y+dy*end/dist),fill=n['color'],width=n['width'])
        else:d.line((x,y,n['x2'],n['y2']),fill=n['color'],width=n['width'])
canvas.save(DEST/'U3-L1-p19-illustration.png',dpi=(300,300))

# Preserve the existing deck package and replace only slide 19's diagram group.
source=O/'base-deck.pptx'
output=P/'U3-L1_机器人的眼睛_第19页实物插图审阅版.pptx'
NSP='http://schemas.openxmlformats.org/presentationml/2006/main'
NSA='http://schemas.openxmlformats.org/drawingml/2006/main'
NSR='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
with zipfile.ZipFile(source) as z:parts={x:z.read(x) for x in z.namelist()}
doc=minidom.parseString(parts['ppt/slides/slide19.xml'])
tree=doc.getElementsByTagNameNS(NSP,'spTree')[0]
for el in list(tree.childNodes):
    if el.nodeType==el.ELEMENT_NODE:
        ids=el.getElementsByTagNameNS(NSP,'cNvPr')
        if ids and int(ids[0].getAttribute('id'))>=7:tree.removeChild(el)
rels=minidom.parseString(parts['ppt/slides/_rels/slide19.xml.rels'])
media={}; nextid=100
scale=11.89*914400/W;ox=.72*914400;oy=2.22*914400
def emu(v):return str(round(v*scale))
def frag(xml):return minidom.parseString(f'<root xmlns:p="{NSP}" xmlns:a="{NSA}" xmlns:r="{NSR}">{xml}</root>').documentElement.firstChild
def color(c):return c.replace('#','')
def fill(c):return f'<a:solidFill><a:srgbClr val="{color(c)}"/></a:solidFill>'
def xfrm(x,y,w,h,flip=''):
    return f'<a:xfrm{flip}><a:off x="{round(ox+x*scale)}" y="{round(oy+y*scale)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
def shapegeom(kind='rect'):return f'<a:prstGeom prst="{kind}"><a:avLst/></a:prstGeom>'
for n in nodes:
    sid=nextid;nextid+=1;k=n['kind'];x=n['x'];y=n['y']
    if k=='image':
        name=n['file']
        if name not in media:
            rid='rIdP19_'+str(len(media)+1);target='p19-'+name
            media[name]=rid;parts['ppt/media/'+target]=(DEST/name).read_bytes()
            rel=rels.createElement('Relationship');rel.setAttribute('Id',rid);rel.setAttribute('Type',NSR+'/image');rel.setAttribute('Target','../media/'+target);rels.documentElement.appendChild(rel)
        xml=f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{escape(name)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="{media[name]}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr>{xfrm(x,y,n["w"],n["h"])}{shapegeom()}</p:spPr></p:pic>'
    elif k=='line':
        x2,y2=n['x2'],n['y2'];xx,yy=min(x,x2),min(y,y2);ww,hh=max(abs(x2-x),.1),max(abs(y2-y),.1)
        flip=(' flipH="1"' if x2<x else '')+(' flipV="1"' if y2<y else '')
        dash='<a:prstDash val="dash"/>' if n['dash'] else ''
        xml=f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{sid}" name="annotation line {sid}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr><p:spPr>{xfrm(xx,yy,ww,hh,flip)}{shapegeom("line")}<a:ln w="{emu(n["width"])}">{fill(n["color"])}{dash}</a:ln></p:spPr></p:cxnSp>'
    else:
        w=n.get('w',n.get('r',0)*2);h=n.get('h',n.get('r',0)*2)
        if k=='dot':x-=n['r'];y-=n['r']
        spfill='<a:noFill/>';ln='<a:ln><a:noFill/></a:ln>';text=''
        if k in ('rect','dot'):spfill=fill(n['fill'])
        if k=='rect' and n['stroke']:ln=f'<a:ln w="{emu(2)}">{fill(n["stroke"])}</a:ln>'
        if k=='text':
            if n['bg']:spfill=fill(n['bg'])
            sz=round(n['size']*scale/914400*72*100)
            text=f'<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"/><a:lstStyle/><a:p><a:pPr marL="0" marR="0"/><a:r><a:rPr lang="zh-CN" sz="{sz}" b="{int(n["bold"])}">{fill(n["color"])}<a:latin typeface="微软雅黑"/><a:ea typeface="微软雅黑"/><a:cs typeface="微软雅黑"/></a:rPr><a:t>{escape(n["text"])}</a:t></a:r><a:endParaRPr lang="zh-CN" sz="{sz}"/></a:p></p:txBody>'
        xml=f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{escape(n.get("text",k))}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>{xfrm(x,y,w,h)}{shapegeom("ellipse" if k=="dot" else "rect")}{spfill}{ln}</p:spPr>{text}</p:sp>'
    tree.appendChild(doc.importNode(frag(xml),True))
# Short visible disclaimer in the original footer zone; constructed imagery is not experimental evidence.
nodes_json={'canvas':[W,H],'body_inch':[.72,2.22,11.89,H/W*11.89],'annotations':nodes,'source_pptx':source.name,'output_pptx':output.name}
(DEST/'layout.json').write_text(json.dumps(nodes_json,ensure_ascii=False,indent=2),encoding='utf-8')
disclaimer='教学构造示意；非真机实拍或实测结果。'
sid=nextid
xml=f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="illustration disclaimer"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{round(.75*914400)}" y="{round(7.02*914400)}"/><a:ext cx="{round(9*914400)}" cy="{round(.29*914400)}"/></a:xfrm>{shapegeom()}<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr lIns="0" tIns="0" rIns="0" bIns="0"/><a:lstStyle/><a:p><a:r><a:rPr lang="zh-CN" sz="950">{fill(GRAY)}<a:latin typeface="微软雅黑"/><a:ea typeface="微软雅黑"/></a:rPr><a:t>{disclaimer}</a:t></a:r></a:p></p:txBody></p:sp>'
tree.appendChild(doc.importNode(frag(xml),True))
parts['ppt/slides/slide19.xml']=doc.toxml(encoding='UTF-8')
parts['ppt/slides/_rels/slide19.xml.rels']=rels.toxml(encoding='UTF-8')
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in parts.items():z.writestr(name,data)
with zipfile.ZipFile(source) as a,zipfile.ZipFile(output) as b:
    changed=[n for n in a.namelist() if a.read(n)!=b.read(n)]
assert changed==['ppt/slides/slide19.xml','ppt/slides/_rels/slide19.xml.rels'],changed
qa={'changed_existing_parts':changed,'all_other_existing_parts_identical':True,'slide_count':29,'scene_source':'sensenova-u1.5-lite reference image edits; constructed illustration','ruler_ticks':'deterministic millimetre ticks; not experiment readings','native_annotations':True,'depth_qa':json.loads((O/'geometry-qa.json').read_text(encoding='utf-8'))}
qa['depth_qa']['scene_generation']='completed; third reference-conditioned edit selected'
(DEST/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved illustration:',DEST/'U3-L1-p19-illustration.png')
print('Saved revised deck:',output)
print('Other 28 slides and all original media are byte-identical.')
