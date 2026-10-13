#pragma once
#include "nn.h"
/* Code fingerprints: the mod finds its hook points by pattern instead of fixed
   addresses, so it can work on game versions other than the one it was built from. */
typedef struct { const char* name; int is_data; const u32* v; const u32* m; int n; int adrp_word; u32 off302; } Sig;
enum { SIG_APPAVAIL, SIG_EVCHECK, SIG_LAUNCH16, SIG_DBGDRAW, SIG_TW_SETUP, SIG_U8TO16, SIG_TW_PRINT,
       SIG_FONT_A, SIG_FONT_B, SIG_TW_VT, SIG_TW_SETUP_ARG, SIG_PRIM_MGR, SIG_COUNT };
extern const Sig g_sigs[SIG_COUNT];
extern uptr g_sig_addr[SIG_COUNT];
#define SIGA(x) (g_sig_addr[SIG_##x])
int aden_sigs_resolve(uptr text, uptr text_size);   /* 0 = everything found */
