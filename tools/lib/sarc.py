import sys,struct,os,subprocess
import os
ZSTD=os.environ.get('ZSTD','zstd')
def unsarc(data,out):
    if data[:4]==b'\x28\xb5\x2f\xfd': data=subprocess.run([ZSTD,"-dc"],input=data,capture_output=True,check=True).stdout
    assert data[:4]==b'SARC',data[:4]
    hl,bom,size,doff=struct.unpack_from('<HHII',data,4)
    o=hl; assert data[o:o+4]==b'SFAT'; _,n,mult=struct.unpack_from('<HHI',data,o+4); o+=12
    ents=[struct.unpack_from('<IIII',data,o+16*i) for i in range(n)]
    o+=16*n; assert data[o:o+4]==b'SFNT'; nt=o+8
    res=[]
    for h,attr,s,e in ents:
        name=data[nt+(attr&0xFFFF)*4:].split(b'\0')[0].decode() if attr>>24 else '%08x'%h
        p=os.path.join(out,name); os.makedirs(os.path.dirname(p) or '.',exist_ok=True)
        open(p,'wb').write(data[doff+s:doff+e]); res.append(name)
    return res
if __name__=='__main__':
    for n in unsarc(open(sys.argv[1],'rb').read(),sys.argv[2]): print(n)
