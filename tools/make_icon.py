#!/usr/bin/env python3
"""Puts the Aden "A" icon on the phone app slot used by Aden Modmenu (Room Sketch / "Study").
usage: make_icon.py <dumped romfs>/Layout/LMenuDeviceBtn.Nin_NX_NVN.zs assets/A_icon.png <out .zs>
Needs: zstd and astcenc on PATH (or ZSTD / ASTCENC environment variables)."""
import sys,os,struct
here=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,os.path.join(here,'lib')); sys.path.insert(0,here)
import sarcpack, flyt, bntx
from PIL import Image
src_zs, icon_png, out_zs = sys.argv[1:4]
tmp=os.path.join(os.path.dirname(os.path.abspath(out_zs)) or '.', '_icon_tmp'); os.makedirs(tmp,exist_ok=True)

outer=sarcpack.read(open(src_zs,'rb').read())
inner=sarcpack.read(outer['files'][0]['data'])
F={f['name']:f for f in inner['files']}

# ---------- texture: A icon in place of DeviceIconStudy, animated overlays made transparent ----------
d=bytearray(F['timg/__Combined.bntx']['data'])
ts={t.name.split('^')[0]:t for t in bntx.parse(d)}
bntx.import_png(d,ts['DeviceIconStudy'],icon_png)
for nm in ('DeviceStudyGrid','DeviceStudyObj00'):
    t=ts[nm]; p=os.path.join(tmp,nm+'.png'); Image.new('RGBA',(t.w,t.h),(0,0,0,0)).save(p); bntx.import_png(d,t,p)
t=ts['DeviceStudyObj01']; bntx.put_blocks(d,t,bntx.encode_bc4_const(t,0))
F['timg/__Combined.bntx']['data']=bytes(d)

# ---------- bflyt ----------
d=bytearray(F['blyt/LMenuDeviceBtn.bflyt']['data'])
hl,=struct.unpack_from('<H',d,6); o=hl
while d[o:o+4]!=b'txl1': o+=struct.unpack_from('<I',d,o+4)[0]
sz,=struct.unpack_from('<I',d,o+4); cnt,=struct.unpack_from('<H',d,o+8); base=o+12
offs=[struct.unpack_from('<I',d,base+4*i)[0] for i in range(cnt)]
names=[d[base+x:].split(b'\0')[0] for x in offs]
NEW=b'DeviceIconStudy^w'; assert NEW not in names
names.append(NEW); n=len(names)
tbl=bytearray(); strs=bytearray(); pos=4*n
for nm in names: tbl+=struct.pack('<I',pos+len(strs)); strs+=nm+b'\0'
body=struct.pack('<HH',n,0)+tbl+strs
while (8+len(body))%4: body+=b'\0'
sec=b'txl1'+struct.pack('<I',8+len(body))+body
d=d[:o]+sec+d[o+sz:]
newidx=n-1; print('new texture index',newidx)
ps,tex,mats=flyt.panes(bytes(d)); assert tex[newidx]=='DeviceIconStudy^w'
# material 83 (P_Study_01): texmap -> icon, colours -> identity
mo=[m for m in mats if m[1]=='P_Study_01'][0][0]
assert struct.unpack_from('<I',d,mo+28)[0]==0x15
struct.pack_into('<4B',d,mo+36,0,0,0,0)          # black colour
struct.pack_into('<4B',d,mo+40,255,255,255,255)  # white colour
assert struct.unpack_from('<H',d,mo+44)[0]==0x3b
struct.pack_into('<H',d,mo+44,newidx)
d[mo+46]=0x04; d[mo+47]=0x04                                   # clamp, like the normal icon (was repeat)
assert [round(x,3) for x in struct.unpack_from('<5f',d,mo+48)]==[0.5,0.0,0.0,2.0,1.0]
struct.pack_into('<5f',d,mo+48,0.0,0.0,0.0,1.0,1.0)           # texture transform: no shift, no 2x stretch
P={p['name']:p for p in ps}
p=P['P_Study_01']['off']
struct.pack_into('<3f',d,p+0x2c,0,0,0); d[p+9]=0   # centre origin (was bottom)
struct.pack_into('<2f',d,p+0x44,0.86,0.86); struct.pack_into('<2f',d,p+0x4c,148,148)
for nm in ('P_Study_00','P_Study_02'): d[P[nm]['off']+8]&=~1      # hide the rug and stool
struct.pack_into('<I',d,0x0c,len(d))
F['blyt/LMenuDeviceBtn.bflyt']['data']=bytes(d)

# ---------- SelectLoop: make P_Study_01 bounce in place ----------
a=bytearray(F['anim/LMenuDeviceBtn_SelectLoop.bflan']['data'])
hl,=struct.unpack_from('<H',a,6); o=hl
while a[o:o+4]!=b'pai1': o+=struct.unpack_from('<I',a,o+4)[0]
frames,loop,_,ntex,nent,entoff=struct.unpack_from('<HBBHHI',a,o+8)
for e in range(nent):
    eo,=struct.unpack_from('<I',a,o+entoff+4*e); E=o+eo
    if a[E:E+28].split(b'\0')[0]!=b'P_Study_01': continue
    for t in range(a[E+28]):
        to,=struct.unpack_from('<I',a,E+32+4*t); T=E+to
        for g in range(a[T+4]):
            go,=struct.unpack_from('<I',a,T+8+4*g); G=T+go
            idx,target,ctype,_,nk,_,ko=struct.unpack_from('<BBBBHHI',a,G); assert ctype==2
            for k in range(nk):
                K=G+ko+12*k; fr,v,s=struct.unpack_from('<3f',a,K)
                if target==0: v,s=0.0,0.0                       # no sliding sideways
                elif target==1: v,s=(v+7)*0.7,s*0.7            # hop up from rest, a bit smaller
                elif target==5: v,s=v*1.6,s*1.6                 # slightly bigger tilt
                struct.pack_into('<3f',a,K,fr,v,s)
            print('patched target',target,nk,'keys')
F['anim/LMenuDeviceBtn_SelectLoop.bflan']['data']=bytes(a)



outer['files'][0]['data']=sarcpack.write(inner)
open(out_zs,'wb').write(sarcpack.zs(sarcpack.write(outer)))
print('wrote',out_zs)
