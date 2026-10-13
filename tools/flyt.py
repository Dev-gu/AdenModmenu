import struct,sys
def panes(d):
    hl,=struct.unpack_from('<H',d,6); o=hl; depth=0; out=[]; tex=[]; mats=[]
    while o<len(d):
        mg=d[o:o+4]; sz,=struct.unpack_from('<I',d,o+4)
        if mg==b'txl1':
            c,=struct.unpack_from('<H',d,o+8); base=o+12
            for i in range(c):
                off,=struct.unpack_from('<I',d,base+4*i); tex.append(d[base+off:].split(b'\0')[0].decode())
        elif mg==b'mat1':
            c,=struct.unpack_from('<H',d,o+8)
            for i in range(c):
                mo,=struct.unpack_from('<I',d,o+12+4*i); mats.append((o+mo,d[o+mo:o+mo+28].split(b'\0')[0].decode()))
        elif mg==b'pas1': depth+=1
        elif mg==b'pae1': depth-=1
        elif mg in (b'pan1',b'pic1',b'txt1',b'wnd1',b'prt1',b'bnd1',b'scr1',b'ali1'):
            name=d[o+0x0c:o+0x24].split(b'\0')[0].decode()
            flags=d[o+8]; tr=struct.unpack_from('<3f',d,o+0x2c); rot=struct.unpack_from('<3f',d,o+0x38)
            sc=struct.unpack_from('<2f',d,o+0x44); size=struct.unpack_from('<2f',d,o+0x4c)
            p=dict(off=o,kind=mg.decode(),name=name,depth=depth,flags=flags,tr=tr,rot=rot,sc=sc,size=size)
            if mg==b'pic1':
                p['mat'],=struct.unpack_from('<H',d,o+0x64); p['ntc']=d[o+0x66]
                p['uv']=[struct.unpack_from('<8f',d,o+0x68+32*k) for k in range(p['ntc'])]
            out.append(p)
        o+=sz
    return out,tex,mats
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read(); ps,tex,mats=panes(d)
    pat=sys.argv[2] if len(sys.argv)>2 else ''
    for p in ps:
        if pat in p['name']:
            extra=''
            if 'mat' in p: extra=' mat=%d %s uv=%s'%(p['mat'],mats[p['mat']][1],[tuple(round(v,2) for v in u) for u in p['uv']])
            print('  '*p['depth']+'%s %s vis=%d tr=%s rot=%s sc=%s size=%s%s'%(p['kind'],p['name'],p['flags']&1,tuple(round(v,1) for v in p['tr']),tuple(round(v,1) for v in p['rot']),tuple(round(v,2) for v in p['sc']),tuple(round(v,1) for v in p['size']),extra))
