import struct,subprocess
import os
ZSTD=os.environ.get('ZSTD','zstd')
def unzs(b):
    if b[:4]==b'\x28\xb5\x2f\xfd': return subprocess.run([ZSTD,'-dc'],input=b,capture_output=True,check=True).stdout
    return b
def zs(b):
    import tempfile,os
    with tempfile.NamedTemporaryFile(delete=False) as f: f.write(b); n=f.name
    out=subprocess.run([ZSTD,'-19','--no-check','-c','-q',n],capture_output=True,check=True).stdout
    os.unlink(n); return out
def read(data):
    data=unzs(data)
    hl,bom,size,doff,ver=struct.unpack_from('<HHIIH',data,4)
    o=hl; _,n,mult=struct.unpack_from('<HHI',data,o+4); o+=12
    ents=[struct.unpack_from('<IIII',data,o+16*i) for i in range(n)]
    o+=16*n; nt=o+8
    files=[]
    for h,attr,s,e in ents:
        name=data[nt+(attr&0xFFFF)*4:].split(b'\0')[0].decode() if attr>>24 else None
        # alignment guess from data start
        a=doff+s; al=1
        while al<0x2000 and a%(al*2)==0: al*=2
        files.append(dict(hash=h,name=name,data=data[doff+s:doff+e],align=al,attr=attr))
    return dict(mult=mult,ver=ver,files=files,doff=doff)
def write(sa):
    files=sa['files']; n=len(files)
    # name table
    nt=bytearray(); offs=[]
    for f in files:
        if f['name'] is None: offs.append(None); continue
        offs.append(len(nt)//4); nt+=f['name'].encode()+b'\0'
        while len(nt)%4: nt+=b'\0'
    hdr_len=0x14+0xC+16*n+8+len(nt)
    maxal=max([f['align'] for f in files]+[4]); maxal=min(maxal,0x2000)
    doff=(hdr_len+maxal-1)//maxal*maxal
    body=bytearray(); ents=bytearray()
    for f,no in zip(files,offs):
        al=max(4,min(f['align'],0x2000))
        while (doff+len(body))%al: body+=b'\0'
        s=len(body); body+=f['data']; e=len(body)
        attr=(0x01000000|no) if no is not None else 0
        ents+=struct.pack('<IIII',f['hash'],attr,s,e)
    out=bytearray(b'SARC'+struct.pack('<HHIIHH',0x14,0xFEFF,0,doff,sa['ver'],0))
    out+=b'SFAT'+struct.pack('<HHI',0xC,n,sa['mult'])+ents
    out+=b'SFNT'+struct.pack('<HH',8,0)+nt
    while len(out)<doff: out+=b'\0'
    out+=body
    struct.pack_into('<I',out,8,len(out))
    return bytes(out)
