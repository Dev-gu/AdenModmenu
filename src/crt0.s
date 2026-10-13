/* Module header: rtld finds MOD0 through the word at +4. */
.section ".text.crt0","ax"
.global __module_start
.hidden __module_start
__module_start:
    b 1f
    .word __nx_mod0 - __module_start
    .ascii "ADEN-MODMENU-v01"
1:  ret

.section ".rodata.mod0","a"
.align 2
__nx_mod0:
    .ascii "MOD0"
    .word  __dynamic_start__        - __nx_mod0
    .word  __bss_start__            - __nx_mod0
    .word  __bss_end__              - __nx_mod0
    .word  __eh_frame_hdr_start__   - __nx_mod0
    .word  __eh_frame_hdr_end__     - __nx_mod0
    .word  aden_module_runtime      - __nx_mod0

/* Executable scratch space for hook trampolines (written via an RW alias). */
.section ".text.tramp","ax"
.align 12
.global aden_tramp_area
.hidden aden_tramp_area
aden_tramp_area:
    .space 0x8000
.global aden_tramp_area_end
.hidden aden_tramp_area_end
aden_tramp_area_end:
