from PIL import Image, ImageDraw
import math
S=4; N=180*S
BROWN=(78,62,53,255); YEL=(246,205,74,255); CREAM=(247,242,226,255); LEAF=(122,196,96,255); LEAFDK=(76,150,70,255)
img=Image.new('RGBA',(N,N),(0,0,0,0)); d=ImageDraw.Draw(img)
def P(x,y): return (x*S,y*S)
def stroke(a,b,w,c):
    d.line([P(*a),P(*b)],fill=c,width=int(w*S))
    for (x,y) in (a,b): r=w*S/2; d.ellipse([x*S-r,y*S-r,x*S+r,y*S+r],fill=c)
apex=(90,36); L=(42,150); R=(138,150)
# soft cream backing so the letter pops on any button colour
for a,b in ((apex,L),(apex,R)): stroke(a,b,46,CREAM)
stroke((60,112),(120,112),34,CREAM)
# the letter
stroke(apex,L,32,BROWN); stroke(apex,R,32,BROWN)
stroke((63,112),(117,112),20,YEL)
# leaf sprouting from the apex (Nook-style leaf)
def leaf(cx,cy,ang,ln,wd):
    pts=[]
    for i in range(41):
        t=i/40; x=ln*(t-0.5); y=wd*math.sin(math.pi*t)*0.5
        pts.append((x,y))
    pts+= [(ln*(0.5-i/40), -wd*math.sin(math.pi*(1-i/40))*0.5) for i in range(41)]
    ca,sa=math.cos(ang),math.sin(ang)
    return [P(cx+x*ca-y*sa, cy+x*sa+y*ca) for x,y in pts]
ang=math.radians(-40); cx,cy=110,24
d.polygon(leaf(cx,cy,ang,52,30),fill=CREAM)
d.polygon(leaf(cx,cy,ang,44,24),fill=LEAF)
ca,sa=math.cos(ang),math.sin(ang)
d.line([P(cx-20*ca,cy-20*sa),P(cx+16*ca,cy+16*sa)],fill=LEAFDK,width=3*S)
# little sparkle
def star(x,y,r,c):
    pts=[]
    for i in range(8):
        rr=r if i%2==0 else r*0.38; a=math.pi/4*i-math.pi/2
        pts.append(P(x+rr*math.cos(a),y+rr*math.sin(a)))
    d.polygon(pts,fill=c)
star(40,52,13,YEL); star(150,78,8,YEL)
img=img.resize((180,180),Image.LANCZOS)
img.save('assets/A_icon.png')
# preview on a few button colours
pv=Image.new('RGBA',(4*220,220),(40,40,40,255))
for i,c in enumerate([(247,242,226),(93,194,171),(240,170,90),(150,190,230)]):
    b=Image.new('RGBA',(200,200),(0,0,0,0)); ImageDraw.Draw(b).rounded_rectangle([0,0,199,199],60,fill=c+(255,))
    b.alpha_composite(img,(10,10)); pv.alpha_composite(b,(i*220+10,10))
pv.save('assets/A_preview.png')
