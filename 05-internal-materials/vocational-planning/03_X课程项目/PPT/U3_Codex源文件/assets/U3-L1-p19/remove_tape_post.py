"""Remove the long black post under the tape case by local background repair."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

B=Path(__file__).resolve().parent
src=Image.open(B/'source/scene-generated-v3.png').convert('RGB')
a=np.array(src)
mask=Image.new('L',src.size,0)
d=ImageDraw.Draw(mask)
# Tape case bottom is at y=727; retain the case, remove its post and floor base.
d.polygon([(1472,728),(1535,728),(1560,756),(1612,820),(1612,1600),(1410,1600),(1410,1378),(1466,1345),(1466,755)],fill=255)
# Clone adjacent cardboard/floor along the perspective of the carton bottom edge.
# This preserves the sharp diagonal edge rather than diffusing it across the mask.
yy,xx=np.indices(a.shape[:2],dtype=np.float32)
sx=1625+12*np.sin(xx/17)
sy=yy+(sx-xx)*.395
patch=cv2.remap(a,sx,sy,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
alpha=np.asarray(mask.filter(ImageFilter.GaussianBlur(7)),dtype=np.float32)/255
alpha[:728]=0
out=np.rint(a*(1-alpha[...,None])+patch*alpha[...,None]).astype(np.uint8)
Image.fromarray(out).save(B/'source/scene-no-tape-post.png')
mask.save(B/'source/tape-post-removal-mask.png')
