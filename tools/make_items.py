# Builds sd:/aden/items.txt  ->  "<hex id>\t<category>\t<name>" for every named item.
import sys,os,glob,re
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'lib'))
import msbt
src=sys.argv[1]; out=sys.argv[2]
items={}
for fn in sorted(glob.glob(os.path.join(src,'Item','STR_ItemName_*.msbt'))):
    cat=re.match(r'STR_ItemName_\d+_(\w+)\.msbt',os.path.basename(fn)).group(1)
    h,secs=msbt.parse(open(fn,'rb').read()); sd={m:b for m,b in secs}
    L=msbt.labels(sd[b'LBL1']); T=msbt.texts(sd[b'TXT2'])
    for lab,idx in L.items():
        m=re.match(r'(.+)_(\d+)$',lab)
        if not m: continue
        iid=int(m.group(2))
        name=re.sub(r'<[^>]*>','',msbt.show(T[idx])).strip()
        if not name: continue
        items[iid]=(cat,name)
# clothing: group name + color variant, labels '<grp>_<Kind>_<itemid>'
def load(fn):
    h,secs=msbt.parse(open(fn,'rb').read()); sd={m:b for m,b in secs}
    L=msbt.labels(sd[b'LBL1']); T=msbt.texts(sd[b'TXT2'])
    return {l:re.sub(r'<[^>]*>','',msbt.show(T[i])).strip() for l,i in L.items()}
for fn in sorted(glob.glob(os.path.join(src,'Outfit','GroupColor','STR_OutfitGroupColor_*.msbt'))):
    kind=re.match(r'STR_OutfitGroupColor_(\w+)\.msbt',os.path.basename(fn)).group(1)
    names=load(os.path.join(src,'Outfit','GroupName','STR_OutfitGroupName_%s.msbt'%kind))
    for lab,color in load(fn).items():
        m=re.match(r'(\w+?)_\w+_(\d+)$',lab)
        if not m: continue
        grp,iid=m.group(1),int(m.group(2))
        base=names.get(grp)
        if base and iid not in items: items[iid]=(kind,'%s (%s)'%(base,color) if color else base)
with open(out,'w',encoding='utf-8') as f:
    f.write('# Aden Modmenu item list: hex id, category, name\n')
    for iid in sorted(items):
        c,n=items[iid]; f.write('%04X\t%s\t%s\n'%(iid,c,n))
print(len(items),'items')
