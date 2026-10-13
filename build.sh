#!/bin/bash
# Builds out/subsdk9 (the mod) from src/.
# Needs: clang + ld.lld (LLVM 15 or newer) and elf2nso from switch-tools
#        (https://github.com/switchbrew/switch-tools). Set ELF2NSO if it isn't on PATH.
set -e
cd "$(dirname "$0")"
ELF2NSO=${ELF2NSO:-elf2nso}
mkdir -p build out
CF="--target=aarch64-none-elf -march=armv8-a+crc+crypto -mtune=cortex-a57 -O2 -fPIC -ffreestanding -fno-builtin -nostdlib -nostdinc -fvisibility=hidden -ffunction-sections -fdata-sections -fno-asynchronous-unwind-tables -fno-unwind-tables -fno-stack-protector -fno-omit-frame-pointer -mno-outline-atomics -Wall -Werror -Wno-unused-function -Wno-unused-command-line-argument -isystem $(clang -print-resource-dir)/include"
rm -f build/*.o
for f in src/*.c src/*.s; do clang $CF -c "$f" -o "build/$(basename "$f").o"; done
ld.lld -shared -T src/link.ld --gc-sections -z text -z now --no-undefined-version --build-id=sha1 -init=aden_module_init -o build/aden.elf build/*.o
"$ELF2NSO" build/aden.elf out/subsdk9 >/dev/null
echo "built out/subsdk9 ($(stat -c %s out/subsdk9) bytes)"
