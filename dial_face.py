"""Printable vintage dial face — true scale on A4. Print at 100% / 'actual size'."""
import math, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Circle, Polygon
FONT='/usr/share/fonts/truetype/freefont/FreeSerif.ttf'
fp=fm.FontProperties(fname=FONT) if __import__('os').path.exists(FONT) else fm.FontProperties(family='serif')
R=90; INK='#3b2a1a'; PAPER='#efe4c8'
ROMAN=["XII","I","II","III","IIII","V","VI","VII","VIII","IX","X","XI"]
mm=1/25.4
fig=plt.figure(figsize=(210*mm,297*mm)); ax=fig.add_axes([0,0,1,1])
ax.set_xlim(-105,105); ax.set_ylim(-148.5,148.5); ax.set_aspect('equal'); ax.axis('off')
ax.add_patch(Circle((0,0),R,fc=PAPER,ec=INK,lw=0.6))
for r,w in [(85,1.4),(82,0.9),(77,0.9),(56,0.6),(14,0.5)]:
    ax.add_patch(Circle((0,0),r,fill=False,ec=INK,lw=w))
for i in range(60):
    a=math.radians(90-i*6); big=i%5==0
    ax.plot([77*math.cos(a),82*math.cos(a)],[77*math.sin(a),82*math.sin(a)],color=INK,lw=2.6 if big else 0.8,solid_capstyle='butt')
    if big:
        pts=[(r*math.cos(a+da),r*math.sin(a+da)) for r,da in [(83.2,0),(84,0.012),(84.8,0),(84,-0.012)]]
        ax.add_patch(Polygon(pts,fc=INK,ec=INK,lw=0.3))
# pt size so cap height ~ 12 mm
for h,t in enumerate(ROMAN):
    a=90-h*30; x,y=66*math.cos(math.radians(a)),66*math.sin(math.radians(a))
    ax.text(x,y,t,fontproperties=fp,fontsize=44,color=INK,ha='center',va='center',rotation=a-90,rotation_mode='anchor')
ax.text(0,-30,"ANNO MMXXVI",fontproperties=fp,fontsize=9,color=INK,ha='center',va='center')
ax.add_patch(Circle((0,0),3.1,fc='white',ec=INK,lw=0.4))           # 6.2 mm centre hole guide
ax.plot([-50,50],[-120,-120],color='k',lw=0.8); ax.text(0,-124,"100 mm — check with a ruler after printing",fontsize=7,ha='center')
fig.savefig('out/dial_face_A4.pdf'); fig.savefig('out/dial_face_preview.png',dpi=110)
