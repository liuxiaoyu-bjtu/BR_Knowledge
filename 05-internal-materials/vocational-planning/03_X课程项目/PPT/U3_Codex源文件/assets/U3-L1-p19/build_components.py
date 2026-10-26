"""Exact depth and tape components; not an AI-generated experiment illustration."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / 'source'
OUT.mkdir(exist_ok=True)
W,H = 1440,1080
f = W/(2*np.tan(np.deg2rad(30)))
u,v = np.meshgrid(np.arange(W),np.arange(H))
dx,dy = (u-W/2)/f, (v-H/2)/f
z = np.full((H,W),4.0)
ids = np.zeros((H,W),dtype=np.uint8)

def merge(t,mask,idx):
    global z,ids
    mask = mask & np.isfinite(t) & (t>0) & (t<z)
    z[mask]=t[mask]
    ids[mask]=idx

# The image records axial depth Z, rather than radial ray length.
with np.errstate(divide='ignore',invalid='ignore'):
    floor = .6/dy
merge(floor,dy>0,1)
front=np.full_like(z,1.8)
merge(front,(abs(dx*1.8)<=.5)&(dy*1.8>=-.4)&(dy*1.8<=.6),2)

# Opaque bottle: lathe segments, x=1.03m, z=2.65m, floor y=.6m.
cx,cz=1.03,2.65
segments=[(-.22,-.14,.058,.058),(-.14,-.02,.058,.13),(-.02,.6,.13,.13)]
for y0,y1,r0,r1 in segments:
    a=(r1-r0)/(y1-y0)
    b=r0-a*y0
    A=dx**2+1-(a*dy)**2
    B=-2*(cx*dx+cz+a*dy*b)
    C=cx**2+cz**2-b*b
    disc=B*B-4*A*C
    for sign in [-1,1]:
        t=(-B+sign*np.sqrt(np.maximum(disc,0)))/(2*A)
        yy=dy*t
        merge(t,(disc>=0)&(yy>=y0)&(yy<=y1),3)
# Bottle cap upper disk, only if visible from the camera.
with np.errstate(divide='ignore',invalid='ignore'):
    t=-.22/dy
    capmask=((dx*t-cx)**2+(t-cz)**2<=.058**2)
merge(t,capmask,3)
near,far=.8,4.2
gray=np.rint(255*np.clip((far-z)/(far-near),0,1)).astype('uint8')
Image.fromarray(gray).save(OUT/'depth-clean.png')
np.save(OUT/'depth-z-metres.npy',z.astype('float32'))
Image.fromarray(ids).save(OUT/'geometry-object-ids.png')

fontpath='C:/Windows/Fonts/msyh.ttc'
def font(n): return ImageFont.truetype(fontpath,n)
T=(14,165,164)
im=Image.new('RGB',(1600,1410),'white')
d=ImageDraw.Draw(im)
d.text((40,22),'深度图：中心点落在纸箱正面',font=font(42),fill=(23,33,43))
im.paste(Image.fromarray(gray).convert('RGB'),(80,100))
px,py=80+W//2,100+H//2
d.line((px-22,py,px+22,py),fill=T,width=4)
d.line((px,py-22,px,py+22),fill=T,width=4)
d.text((px+32,py-34),'(W/2, H/2)',font=font(30),fill=T)
for i in range(600):
    g=round(255*(1-i/599))
    d.line((80+i,1210,80+i,1255),fill=(g,g,g))
d.text((80,1264),'近',font=font(29),fill=(23,33,43))
d.text((645,1264),'远',font=font(29),fill=(23,33,43))
d.text((760,1212),'灰度仅由距离决定',font=font(30),fill=(23,33,43))
d.text((80,1335),'深度可视化示意，近白远黑；非真机实测截图。',font=font(27),fill=(107,119,133))
im.save(OUT/'depth-annotated.png')

# An actual regular scale. Millimetres are exact even when downsampled.
tw,th=6600,350
tape=Image.new('RGBA',(tw+160,th+130),(255,255,255,0))
td=ImageDraw.Draw(tape)
td.rounded_rectangle((40,35,tw+120,th+35),radius=12,fill=(244,198,57),outline=(104,80,17),width=5)
for mm in range(2201):
    x=80+mm*3
    length=96 if mm%100==0 else 70 if mm%10==0 else 48 if mm%5==0 else 29
    td.line((x,40,x,40+length),fill=(28,30,30),width=3 if mm%10==0 else 2)
    if mm%100==0:
        label=str(mm//10)
        td.text((x,160),label,font=font(64),fill=(184,40,33) if mm%1000==0 else (28,30,30),anchor='mm')
    elif mm%10==0:
        td.text((x,135),str((mm//10)%10),font=font(22),fill=(28,30,30),anchor='mm')
td.text((80,260),'cm',font=font(38),fill=(28,30,30))
tape.save(OUT/'tape-0-220cm-transparent.png')

face=gray[ids==2]
bottle=gray[ids==3]
qa={'canvas':[W,H],'depth_kind':'axial camera Z; ideal pinhole model',
    'gray_mapping':{'near_metres':near,'far_metres':far,'formula':'round(255*clip((far-Z)/(far-near),0,1))'},
    'center_object':'carton front','center_z_m':float(z[H//2,W//2]),
    'front_gray_min':int(face.min()),'front_gray_max':int(face.max()),
    'bottle_gray_min':int(bottle.min()),'bottle_gray_max':int(bottle.max()),
    'carton_top':'not visible in camera view; front plane covers optical axis',
    'ruler':'0-220 cm; one tick every 1 mm; not an experimental reading',
    'scene_generation':'selected reference-conditioned v3 scene is assembled separately'}
assert face.min()==face.max()
assert ids[H//2,W//2]==2
assert z[H//2,W//2]==1.8
assert bottle.max()<face.min()
(OUT/'geometry-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(qa,ensure_ascii=False,indent=2))
