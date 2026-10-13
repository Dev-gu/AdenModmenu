import struct,zlib
def load(path):
    d=open(path,'rb').read()
    n,esz,nf=struct.unpack_from('<IIH',d,0)
    fields=[struct.unpack_from('<II',d,0x1C+i*8) for i in range(nf)]
    base=0x1C+nf*8
    fields.sort(key=lambda f:f[1])
    rows=[d[base+i*esz:base+(i+1)*esz] for i in range(n)]
    sizes={}
    for i,(h,o) in enumerate(fields):
        nxt=fields[i+1][1] if i+1<len(fields) else esz
        sizes[h]=(o,nxt-o)
    return rows,sizes
def crc(name): return zlib.crc32(name.encode())&0xffffffff
