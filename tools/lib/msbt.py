import struct,sys
def parse(d):
    assert d[:8]==b'MsgStdBn'
    bom=d[8:10]; assert bom==b'\xff\xfe'
    nsec=struct.unpack_from('<H',d,0xE)[0]
    o=0x20; secs=[]
    for i in range(nsec):
        mg=d[o:o+4]; sz=struct.unpack_from('<I',d,o+4)[0]
        secs.append([mg,bytearray(d[o+0x10:o+0x10+sz])])
        o+=0x10+sz; o=(o+15)&~15
    return d[:0x20],secs
def labels(lbl1):
    n=struct.unpack_from('<I',lbl1,0)[0]; res={}
    for i in range(n):
        cnt,off=struct.unpack_from('<II',lbl1,4+i*8)
        p=off
        for j in range(cnt):
            l=lbl1[p]; name=lbl1[p+1:p+1+l].decode(); idx=struct.unpack_from('<I',lbl1,p+1+l)[0]
            res[name]=idx; p+=1+l+4
    return res
def texts(txt2):
    n=struct.unpack_from('<I',txt2,0)[0]
    offs=list(struct.unpack_from('<%dI'%n,txt2,4))+[len(txt2)]
    return [bytes(txt2[offs[i]:offs[i+1]]) for i in range(n)]
def build_txt2(ts):
    n=len(ts); hdr=4+4*n; out=bytearray(struct.pack('<I',n)); off=hdr; body=b''
    for t in ts: out+=struct.pack('<I',off); off+=len(t); body+=t
    return out+body
def write(hdr,secs):
    out=bytearray(hdr)
    for mg,b in secs:
        out+=mg+struct.pack('<I',len(b))+bytes(8)+b
        while len(out)%16: out+=b'\xab'
    struct.pack_into('<I',out,0x12,len(out))
    return bytes(out)
def show(t):
    # decode UTF-16 with control tags shown
    s=[];i=0
    while i<len(t):
        c=struct.unpack_from('<H',t,i)[0]
        if c==0xE: 
            grp,typ,sz=struct.unpack_from('<HHH',t,i+2); s.append('<%d.%d:%s>'%(grp,typ,t[i+8:i+8+sz].hex())); i+=8+sz; continue
        if c==0: break
        s.append(chr(c)); i+=2
    return ''.join(s)
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read(); h,secs=parse(d)
    sd={m:b for m,b in secs}
    L=labels(sd[b'LBL1']); T=texts(sd[b'TXT2'])
    for k,v in sorted(L.items(),key=lambda x:x[1]): print(k,repr(show(T[v])))
