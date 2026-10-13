#include "aden.h"
/* Code hooking: code pages are read+execute only, so we map a second, writable
   view of the same memory with svcMapProcessMemory and patch through that. */
extern char aden_tramp_area[], aden_tramp_area_end[];
static Handle s_proc;
typedef struct { uptr rx, rw, size; } Alias;
static Alias s_alias[8]; static int s_nalias;
static u32* s_tramp_rw; static u32* s_tramp_rx; static u32 s_tramp_used; /* in words */

/* ---- current process handle ---- */
static u8 s_thread_stack[0x2000] __attribute__((aligned(0x1000)));
static void recv_thread(void* arg){
    Handle srv=(Handle)(uptr)arg; s32 idx;
    memset(armGetTls(),0,0x10);
    svcReplyAndReceive(&idx,&srv,1,0,~0UL);
    s_proc=((u32*)armGetTls())[3];
    svcCloseHandle(srv);
    svcExitThread();
    for(;;);
}
static int get_proc_handle(void){
    u64 h=0;
    if(svcGetInfo(&h,65000,0,0)==0 && h){ s_proc=(Handle)h; aden_log("proc handle via mesosphere info: %x",s_proc); return 0; }
    Handle srv,cli,th; Result r;
    if((r=svcCreateSession(&srv,&cli,0,0))){ aden_log("CreateSession failed %x",r); return -1; }
    if((r=svcCreateThread(&th,(void*)recv_thread,(void*)(uptr)srv,s_thread_stack+sizeof s_thread_stack,0x20,-2))){ aden_log("CreateThread failed %x",r); return -1; }
    svcStartThread(th);
    static const u32 msg[4]={0,0x80000000,2,CUR_PROCESS_HANDLE};
    memcpy(armGetTls(),msg,16);
    svcSendSyncRequest(cli);
    svcCloseHandle(cli);
    s32 idx; svcWaitSynchronization(&idx,&th,1,~0UL);
    svcCloseHandle(th);
    aden_log("proc handle via IPC trick: %x",s_proc);
    return s_proc?0:-1;
}

/* ---- find unmapped address space ---- */
static uptr find_free(u64 size){
    u64 base=0,len=0; svcGetInfo(&base,12,CUR_PROCESS_HANDLE,0); svcGetInfo(&len,13,CUR_PROCESS_HANDLE,0);
    uptr a=base+len/2;  /* upper half of the ASLR region */
    MemoryInfo mi; u32 pi;
    while(a<base+len){
        if(svcQueryMemory(&mi,&pi,a)) return 0;
        if(mi.type==0){
            uptr s=ALIGN_UP(a+0x200000,0x200000), e=mi.addr+mi.size;
            if(e>s && e-s>=size+0x200000) return s;
        }
        a=mi.addr+mi.size;
    }
    return 0;
}

static int map_alias(uptr rx, u64 size){
    rx=ALIGN_DOWN(rx,PAGE); size=ALIGN_UP(size,PAGE);
    uptr rw=find_free(size); if(!rw){ aden_log("no free VA for %lx",size); return -1; }
    uptr a=rx;
    while(a<rx+size){
        MemoryInfo mi; u32 pi; svcQueryMemory(&mi,&pi,a);
        uptr end=mi.addr+mi.size; if(end>rx+size) end=rx+size;
        Result r=svcMapProcessMemory((void*)(rw+(a-rx)),s_proc,a,end-a);
        if(r){ aden_log("MapProcessMemory(%lx,%lx) failed %x (type %x perm %x)",a,end-a,r,mi.type,mi.perm); return -1; }
        a=end;
    }
    s_alias[s_nalias++]=(Alias){rx,rw,size};
    aden_log("alias %lx..%lx -> %lx",rx,rx+size,rw);
    return 0;
}
static u32* rw_of(uptr rx){
    for(int i=0;i<s_nalias;i++) if(rx>=s_alias[i].rx && rx<s_alias[i].rx+s_alias[i].size) return (u32*)(s_alias[i].rw+(rx-s_alias[i].rx));
    return NULL;
}

HIDDEN int aden_hook_init(void){
    if(get_proc_handle()) return -1;
    /* main's .text */
    if(map_alias(g_main_base, g_main_text_size)) return -1;
    if(map_alias((uptr)aden_tramp_area, aden_tramp_area_end-aden_tramp_area)) return -1;
    s_tramp_rx=(u32*)aden_tramp_area; s_tramp_rw=rw_of((uptr)aden_tramp_area);
    extern void nnMain(void); uptr nm=(uptr)&nnMain;
    if(*(u32*)rw_of(nm)!=*(u32*)nm){ aden_log("alias mismatch!"); return -1; }
    aden_log("hooking ready");
    return 0;
}

HIDDEN int aden_patch32(uptr site, u32 insn){
    u32* w=rw_of(site); if(!w) return -1;
    *w=insn; aden_cache_flush((uptr)w,site,4); return 0;
}

/* trampoline emitter */
static u32 T_n; static u32* T_rw; static uptr T_rx;
static void emit(u32 v){ T_rw[T_n++]=v; }
static void emit64(u64 v){ emit((u32)v); emit((u32)(v>>32)); }
static uptr here(void){ return T_rx+T_n*4; }
static void emit_absjump(uptr to){ emit(0x58000051); emit(0xD61F0220); emit64(to); } /* ldr x17,#8; br x17 */
static s64 sext(u64 v,int bits){ return (s64)(v<<(64-bits))>>(64-bits); }

static int relocate(u32 ins, uptr pc){
    if((ins&0x9F000000)==0x90000000){ /* adrp */
        int rd=ins&31; s64 imm=sext(((ins>>5)&0x7FFFF)<<2|((ins>>29)&3),21)<<12;
        emit(0x58000040|rd); emit(0x14000003); emit64(ALIGN_DOWN(pc,PAGE)+imm); return 0; /* ldr xd,#8; b #12 */
    }
    if((ins&0x9F000000)==0x10000000){ /* adr */
        int rd=ins&31; s64 imm=sext(((ins>>5)&0x7FFFF)<<2|((ins>>29)&3),21);
        emit(0x58000040|rd); emit(0x14000003); emit64(pc+imm); return 0;
    }
    if((ins&0xFC000000)==0x14000000){ emit_absjump(pc+(sext(ins&0x3FFFFFF,26)<<2)); return 0; } /* b */
    if((ins&0xFC000000)==0x94000000){ /* bl */
        emit(0x58000071); emit(0xD63F0220); emit(0x14000003); emit64(pc+(sext(ins&0x3FFFFFF,26)<<2)); return 0;
    }
    if((ins&0xFF000010)==0x54000000 || (ins&0x7E000000)==0x34000000 || (ins&0x7E000000)==0x36000000 ||
       (ins&0x3B000000)==0x18000000) return -1; /* b.cond / cbz / tbz / ldr literal: unsupported */
    emit(ins); return 0;
}

HIDDEN int aden_hook(uptr site, void* fn, void** orig){
    u32* w=rw_of(site);
    if(!w){ if(map_alias(ALIGN_DOWN(site,PAGE),0x2000)==0) w=rw_of(site); }
    if(!w){ aden_log("hook %lx: not mapped",site); return -1; }
    s64 d=(s64)((uptr)fn-site); int nwords = (d>=-0x8000000 && d<0x8000000) ? 1 : 4;
    if(orig){
        T_rw=s_tramp_rw+s_tramp_used; T_rx=(uptr)(s_tramp_rx+s_tramp_used); T_n=0;
        uptr start=here();
        for(int i=0;i<nwords;i++) if(relocate(((u32*)site)[i], site+i*4)){ aden_log("hook %lx: can't relocate insn %d (%x)",site,i,((u32*)site)[i]); return -1; }
        emit_absjump(site+nwords*4);
        aden_cache_flush((uptr)T_rw,T_rx,T_n*4);
        s_tramp_used+=T_n; while(s_tramp_used&3) s_tramp_used++;
        *orig=(void*)start;
    }
    if(nwords==1){ w[0]=0x14000000|((d>>2)&0x3FFFFFF); }
    else { w[0]=0x58000051; w[1]=0xD61F0220; w[2]=(u32)(uptr)fn; w[3]=(u32)((uptr)fn>>32); }
    aden_cache_flush((uptr)w,site,nwords*4);
    aden_log("hooked %lx (main+%lx) -> %p [%d words]",site,site-g_main_base,fn,nwords);
    return 0;
}
