#include "aden.h"
#include "sigs.h"
/* Nook Phone integration: Aden Modmenu borrows phone app id 16 ("Room Sketch",
   a Happy Home Paradise app) and replaces what tapping it does. */
#define OFF(x) (g_main_base+(x))
#define APP_ADEN 16
volatile int g_aden_open_request;

typedef struct { const void* vt; const char* s; } SeadStr;

/* isAppAvailable(ctx, id): always show our app */
static u64 (*o_appavail)(void*, u32);
static u64 h_appavail(void* ctx, u32 id){
    if(id==APP_ADEN) return 1;
    return o_appavail(ctx,id);
}
/* event flag check by name: pretend the Room Sketch intro was already seen */
static u64 (*o_evcheck)(void*, SeadStr*);
static u64 h_evcheck(void* ctx, SeadStr* name){
    if(name && name->s && strcmp(name->s,"NoticeAboutRoomSketch")==0) return 1;
    return o_evcheck(ctx,name);
}
/* app launch handler for id 16. Result: {u32 menuId; s32 nextState; u8 hasNextState}.
   Setting only hasNextState (nextState stays -1) makes the phone put itself away
   with no app, the same path the Camera app uses before starting. */
static void h_launch_aden(u8* result){
    result[8]=1;
    g_aden_open_request=1;
    aden_log("Aden Modmenu app tapped");
}
void aden_phone_install(void){
    aden_hook(SIGA(APPAVAIL),(void*)h_appavail,(void**)&o_appavail);
    aden_hook(SIGA(EVCHECK),(void*)h_evcheck,(void**)&o_evcheck);
    aden_hook(SIGA(LAUNCH16),(void*)h_launch_aden,NULL);
}
