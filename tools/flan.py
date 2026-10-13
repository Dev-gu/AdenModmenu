import struct,sys
def dump(d,filt=None):
    hl,=struct.unpack_from('<H',d,6); o=hl; res=[]
    while o<len(d):
        mg=d[o:o+4]; sz,=struct.unpack_from('<I',d,o+4)
        if mg==b'pai1':
            frames,loop,_,ntex,nent,entoff=struct.unpack_from('<HBBHHI',d,o+8)
            for e in range(nent):
                eo,=struct.unpack_from('<I',d,o+entoff+4*e); E=o+eo
                name=d[E:E+28].split(b'\0')[0].decode(); ntag=d[E+28]; typ=d[E+29]
                if filt and not any(f in name for f in filt): continue
                print('pane',name,'frames',frames,'loop',loop)
                for t in range(ntag):
                    to,=struct.unpack_from('<I',d,E+32+4*t); T=E+to
                    tag=d[T:T+4].decode(); ngrp=d[T+4]
                    for g in range(ngrp):
                        go,=struct.unpack_from('<I',d,T+8+4*g); G=T+go
                        idx,target,ctype,_,nk,_,ko=struct.unpack_from('<BBBBHHI',d,G)
                        keys=[]
                        for k in range(nk):
                            if ctype==2: keys.append(struct.unpack_from('<3f',d,G+ko+12*k))
                            else: keys.append(struct.unpack_from('<fHH',d,G+ko+8*k))
                        print('   ',tag,'target',target,'type',ctype,[tuple(round(v,2) for v in k) for k in keys])
        o+=sz
if __name__=='__main__': dump(open(sys.argv[1],'rb').read(),sys.argv[2:] or None)
