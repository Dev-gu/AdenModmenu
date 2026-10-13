#include "nn.h"
/* Log lines go to svcOutputDebugString immediately, and to sd:/aden/log.txt
   once the SD card is mounted (earlier lines are buffered and written then). */
static char s_early[16384]; static u32 s_early_len;
static int  s_sd; static s64 s_off;
static volatile int s_lock;
#define LOG_PATH "adensd:/aden/log.txt"

static void lock(void){ while(__atomic_exchange_n(&s_lock,1,__ATOMIC_ACQUIRE)); }
static void unlock(void){ __atomic_store_n(&s_lock,0,__ATOMIC_RELEASE); }

static void sd_write(const char* s, u32 n){
    FsFile f; if(nn_fs_OpenFile(&f, LOG_PATH, FS_WRITE|FS_APPEND)) return;
    FsWriteOption o={1}; nn_fs_WriteFile(f, s_off, s, n, &o); s_off+=n; nn_fs_CloseFile(f);
}
HIDDEN int aden_sd_ready(void){ return s_sd; }
HIDDEN void aden_log_attach_sd(void){
    if(s_sd) return;
    Result r = nn_fs_MountSdCardForDebug("adensd");
    if(r) r = nn_fs_MountSdCard("adensd");
    if(r){ char b[64]; int n=aden_snprintf(b,64,"[aden] SD mount failed %x\n",r); svcOutputDebugString(b,n); return; }
    nn_fs_CreateDirectory("adensd:/aden");
    nn_fs_DeleteFile(LOG_PATH);
    nn_fs_CreateFile(LOG_PATH, 0);
    lock(); s_sd=1; s_off=0; sd_write(s_early, s_early_len); unlock();
}
HIDDEN void aden_log(const char* fmt, ...){
    char b[512]; int n=aden_snprintf(b,sizeof b,"[%lu] ",nn_os_GetSystemTick()/19200);
    __builtin_va_list ap; __builtin_va_start(ap,fmt);
    n+=aden_vsnprintf(b+n,sizeof b-n-1,fmt,ap); __builtin_va_end(ap);
    if(n>(int)sizeof b-2) n=sizeof b-2;
    b[n++]='\n'; b[n]=0;
    svcOutputDebugString(b,n);
    lock();
    if(s_sd) sd_write(b,n);
    else if(s_early_len+n<sizeof s_early){ memcpy(s_early+s_early_len,b,n); s_early_len+=n; }
    unlock();
}
