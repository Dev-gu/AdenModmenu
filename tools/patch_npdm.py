# Allow all SVCs 0x00-0x7F in a main.npdm (ACI0 + ACID kernel caps).
import struct,sys
d=bytearray(open(sys.argv[1],'rb').read())
aci_off,aci_sz,acid_off,acid_sz=struct.unpack_from('<IIII',d,0x70)
def svc_desc(grp,mask): return ((grp&7)<<29)|((mask&0xFFFFFF)<<5)|0xF
def rebuild(base,fld):
    off,sz=struct.unpack_from('<II',d,base+fld); o=base+off
    caps=[struct.unpack_from('<I',d,o+i*4)[0] for i in range(sz//4)]
    keep=[c for c in caps if (c & 0x1F)!=0xF]
    new=[keep[0]]+[svc_desc(g,0xFFFFFF) for g in range(5)]+[svc_desc(5,0xFF)]+keep[1:]
    return o,sz,new
# ACI0 is the tail of the file; ACID kac is tail of ACID.
o1,sz1,new1=rebuild(acid_off,0x230)
grow1=len(new1)*4-sz1
assert acid_off+acid_sz==o1+sz1 and acid_off+acid_sz+grow1<=aci_off
assert d[o1+sz1:o1+sz1+grow1]==bytes(grow1)  # padding before ACI0
d[o1:o1+len(new1)*4]=b''.join(struct.pack('<I',c) for c in new1)
struct.pack_into('<I',d,acid_off+0x234,len(new1)*4)
struct.pack_into('<I',d,acid_off+0x204,acid_sz-0x100+grow1) # ACID size field (excludes sig)
struct.pack_into('<I',d,0x7C,acid_sz+grow1)
aci_off2=aci_off  # unchanged
o2,sz2,new2=rebuild(aci_off2,0x30)
assert o2+sz2==len(d)
d[o2:o2+sz2]=b''.join(struct.pack('<I',c) for c in new2)
struct.pack_into('<I',d,aci_off2+0x34,len(new2)*4)
struct.pack_into('<I',d,0x74,aci_sz+len(new2)*4-sz2)
open(sys.argv[2],'wb').write(d)
print('ok',len(d))
