# Renames phone app label 0018 ("Room Sketch") to "Aden Modmenu" in LayoutMsg archives.
import sys,os,struct
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'lib'))
import sarcpack,msbt
# usage: make_text.py <dumped romfs>/Message <out dir> USen EUen ...
SRC=sys.argv[1]
OUT=sys.argv[2]
NEW={'0018':'Aden Modmenu'}
for lang in sys.argv[3:]:
    fn='LayoutMsg_%s.sarc.zs'%lang
    raw=open(os.path.join(SRC,fn),'rb').read()
    sa=sarcpack.read(raw)
    assert sarcpack.write(sa)==sarcpack.unzs(raw)
    for f in sa['files']:
        if f['name']=='MenuDevice.msbt':
            h,secs=msbt.parse(f['data'])
            assert msbt.write(h,secs)==f['data'], 'msbt roundtrip'
            sd={m:b for m,b in secs}
            L=msbt.labels(sd[b'LBL1']); T=msbt.texts(sd[b'TXT2'])
            for lab,txt in NEW.items():
                T[L[lab]]=txt.encode('utf-16-le')+b'\0\0'
            for s in secs:
                if s[0]==b'TXT2': s[1]=msbt.build_txt2(T)
            f['data']=msbt.write(h,secs)
            sd2={m:b for m,b in msbt.parse(f['data'])[1]}
            print(lang,'0018 ->',msbt.show(msbt.texts(sd2[b'TXT2'])[L['0018']]))
    os.makedirs(OUT,exist_ok=True)
    open(os.path.join(OUT,fn),'wb').write(sarcpack.zs(sarcpack.write(sa)))
