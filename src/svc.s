.text
.macro FN name
    .global \name
    .hidden \name
    .type \name, %function
    .align 2
\name:
.endm

//  (MemoryInfo*, u32* pageinfo, u64 addr) 
FN svcQueryMemory
    str x1, [sp, #-16]!
    svc 0x6
    ldr x2, [sp], #16
    str w1, [x2]
    ret
FN svcExitThread
    svc 0xA
    ret
FN svcStartThread
    svc 0x9
    ret
//  (Handle*, entry, arg, stack_top, prio, cpu) 
FN svcCreateThread
    str x0, [sp, #-16]!
    svc 0x8
    ldr x2, [sp], #16
    str w1, [x2]
    ret
FN svcCloseHandle
    svc 0x16
    ret
//  (s32* idx, const Handle*, s32 count, u64 timeout) 
FN svcWaitSynchronization
    str x0, [sp, #-16]!
    svc 0x18
    ldr x2, [sp], #16
    str w1, [x2]
    ret
FN svcSendSyncRequest
    svc 0x21
    ret
FN svcOutputDebugString
    svc 0x27
    ret
//  (u64* out, u32 id0, Handle, u64 id1) 
FN svcGetInfo
    str x0, [sp, #-16]!
    svc 0x29
    ldr x2, [sp], #16
    str x1, [x2]
    ret
//  (Handle* srv, Handle* cli, u32, u64) 
FN svcCreateSession
    stp x0, x1, [sp, #-16]!
    svc 0x40
    ldp x3, x4, [sp], #16
    str w1, [x3]
    str w2, [x4]
    ret
//  (s32* idx, const Handle*, s32, Handle, u64) 
FN svcReplyAndReceive
    str x0, [sp, #-16]!
    svc 0x43
    ldr x2, [sp], #16
    str w1, [x2]
    ret
//  (void* dst, Handle proc, u64 src, u64 size) 
FN svcMapProcessMemory
    svc 0x74
    ret
FN svcUnmapProcessMemory
    svc 0x75
    ret
FN armGetTls
    mrs x0, tpidrro_el0
    ret
//  (rw_addr, rx_addr, size) 
FN aden_cache_flush
    mov x3, #0
1:  add x4, x0, x3
    dc cvau, x4
    add x3, x3, #64
    cmp x3, x2
    b.lo 1b
    dsb ish
    mov x3, #0
2:  add x4, x1, x3
    ic ivau, x4
    add x3, x3, #64
    cmp x3, x2
    b.lo 2b
    dsb ish
    isb
    ret
