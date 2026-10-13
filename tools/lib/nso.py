import struct,sys,ctypes
lz=ctypes.CDLL(sys.argv[3])
d=open(sys.argv[1],'rb').read()
flags=struct.unpack_from('<I',d,0xC)[0]
segs=[struct.unpack_from('<III',d,0x10+i*0x10) for i in range(3)]
csz=struct.unpack_from('<III',d,0x60)
bss=struct.unpack_from('<I',d,0x3C)[0]
print('flags',hex(flags),'segs',[tuple(map(hex,s)) for s in segs],'bss',hex(bss))
print('build id',d[0x40:0x60].hex())
end=segs[2][1]+segs[2][2]
img=bytearray(end)
for i,(fo,mo,sz) in enumerate(segs):
    raw=d[fo:fo+csz[i]]
    if flags&(1<<i):
        out=ctypes.create_string_buffer(sz)
        r=lz.LZ4_decompress_safe(raw,out,len(raw),sz); assert r==sz,r
        raw=out.raw
    img[mo:mo+sz]=raw[:sz]
open(sys.argv[2],'wb').write(img)
print('written',hex(len(img)))
