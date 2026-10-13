#include "sigs.h"
HIDDEN uptr g_sig_addr[SIG_COUNT];

static int match_at(const Sig* s, const u32* w){
    for(int j=0;j<s->n;j++) if((w[j]&s->m[j])!=s->v[j]) return 0;
    return 1;
}
static s64 sext(u64 v,int bits){ return (s64)(v<<(64-bits))>>(64-bits); }
/* decode adrp at pc and its paired add / ldr / str -> address it points at */
static uptr adrp_target(uptr pc){
    u32 x=*(u32*)pc; int rd=x&31;
    s64 imm=sext(((u64)((x>>5)&0x7FFFF)<<2)|((x>>29)&3),21);
    uptr page=(pc&~(uptr)0xFFF)+(imm<<12);
    for(int j=1;j<12;j++){
        u32 y=*(u32*)(pc+j*4);
        if((int)((y>>5)&31)!=rd) continue;
        if((y&0x7F800000)==0x11000000){ u32 o=(y>>10)&0xFFF; if((y>>22)&1) o<<=12; return page+o; }
        if((y&0x3B000000)==0x39000000){ u32 size=(y>>30)&3, v=(y>>26)&1, opc=(y>>22)&3; u32 sc=(v&&opc>=2)?4:size;
            return page+(((y>>10)&0xFFF)<<sc); }
    }
    return 0;
}
static int readable(uptr a){
    MemoryInfo mi; u32 pi;
    if(svcQueryMemory(&mi,&pi,a)) return 0;
    return (mi.perm&1) && mi.type!=0;
}
int aden_sigs_resolve(uptr text, uptr text_size){
    uptr hit[SIG_COUNT]; int cnt[SIG_COUNT];
    /* fast path: the version this was built from */
    int all=1;
    for(int i=0;i<SIG_COUNT;i++){
        const Sig* s=&g_sigs[i]; hit[i]=0; cnt[i]=0;
        if(s->off302+s->n*4<=text_size && match_at(s,(const u32*)(text+s->off302))){ hit[i]=text+s->off302; cnt[i]=1; }
        else all=0;
    }
    if(all) aden_log("game code matches 3.0.2 - using known locations");
    else {
        aden_log("game code differs from 3.0.2 - searching by fingerprint...");
        for(int i=0;i<SIG_COUNT;i++){ hit[i]=0; cnt[i]=0; }
        const u32* w=(const u32*)text; uptr nw=text_size/4;
        for(uptr k=0;k+48<nw;k++){
            u32 x=w[k];
            for(int i=0;i<SIG_COUNT;i++){
                const Sig* s=&g_sigs[i];
                if((x&s->m[0])!=s->v[0] || !match_at(s,w+k)) continue;
                if(cnt[i]++==0) hit[i]=text+k*4;
            }
        }
    }
    int bad=0;
    for(int i=0;i<SIG_COUNT;i++){
        const Sig* s=&g_sigs[i];
        if(cnt[i]!=1){ aden_log("  %s: %s", s->name, cnt[i]?"found more than once":"NOT FOUND"); bad++; continue; }
        uptr a=hit[i];
        if(s->is_data){
            a=adrp_target(hit[i]+s->adrp_word*4);
            if(!a || !readable(a)){ aden_log("  %s: pointer did not decode", s->name); bad++; continue; }
        }
        g_sig_addr[i]=a;
        aden_log("  %s -> main+%lx%s", s->name, a-text, (!s->is_data && hit[i]-text!=s->off302)?" (moved)":"");
    }
    return bad;
}
