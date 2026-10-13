#!/usr/bin/env python3
"""Minimal BNTX texture tool: list / export (to PNG) / import (from PNG, same size+format).
Supports ASTC (via astcenc) and BC4. Textures are Tegra block-linear swizzled."""
import struct, sys, os, subprocess, tempfile
import numpy as np
from PIL import Image

ASTCENC = os.environ.get('ASTCENC', 'astcenc')
ASTC_BLK = {0x2d: (4, 4), 0x2e: (5, 4), 0x2f: (5, 5), 0x30: (6, 5), 0x31: (6, 6), 0x32: (8, 5), 0x33: (8, 6), 0x34: (8, 8)}

class Tex:
    pass

def parse(d):
    out = []
    i = 0
    while True:
        i = d.find(b'BRTI', i)
        if i < 0: break
        t = Tex(); t.hdr = i
        t.mips, = struct.unpack_from('<H', d, i + 0x16)
        t.fmt, = struct.unpack_from('<I', d, i + 0x1c)
        t.w, t.h, _, _, t.blkh = struct.unpack_from('<IIIII', d, i + 0x24)
        t.size, = struct.unpack_from('<I', d, i + 0x50)
        t.comp, = struct.unpack_from('<I', d, i + 0x58)
        no, = struct.unpack_from('<Q', d, i + 0x60)
        nl, = struct.unpack_from('<H', d, no); t.name = d[no + 2:no + 2 + nl].decode()
        po, = struct.unpack_from('<Q', d, i + 0x70)
        t.data, = struct.unpack_from('<Q', d, po)
        out.append(t); i += 4
    return out

def fmtinfo(fmt):
    ty = fmt >> 8
    if ty in ASTC_BLK: return ASTC_BLK[ty] + (16,)
    if ty == 0x1a or ty == 0x1d: return (4, 4, 8)      # BC1 / BC4
    if ty in (0x1b, 0x1c, 0x1e, 0x20): return (4, 4, 16)
    if ty == 0x0b: return (1, 1, 4)
    raise ValueError('format %x' % fmt)

def _addr(xb, y, wgobs, bh):
    # xb = x in bytes; bh = block height in GOBs
    gob = (y // (8 * bh)) * 512 * bh * wgobs + (xb // 64) * 512 * bh + ((y % (8 * bh)) // 8) * 512
    return gob + ((xb % 64) // 32) * 256 + ((y % 8) // 2) * 64 + ((xb % 32) // 16) * 32 + (y % 2) * 16 + (xb % 16)

def offsets(t):
    bw, bhp, bpp = fmtinfo(t.fmt)
    wb = (t.w + bw - 1) // bw; hb = (t.h + bhp - 1) // bhp
    wgobs = (wb * bpp + 63) // 64
    bh = 1 << t.blkh
    offs = np.zeros((hb, wb), dtype=np.int64)
    for y in range(hb):
        for x in range(wb):
            offs[y, x] = _addr(x * bpp, y, wgobs, bh)
    return wb, hb, bpp, offs

def get_blocks(d, t):
    wb, hb, bpp, offs = offsets(t)
    out = bytearray()
    for y in range(hb):
        for x in range(wb):
            a = t.data + offs[y, x]; out += d[a:a + bpp]
    return bytes(out)

def put_blocks(d, t, blocks):
    wb, hb, bpp, offs = offsets(t)
    assert len(blocks) == wb * hb * bpp
    assert offs.max() + bpp <= t.size, 'swizzle exceeds image size'
    k = 0
    for y in range(hb):
        for x in range(wb):
            a = t.data + offs[y, x]; d[a:a + bpp] = blocks[k:k + bpp]; k += bpp

def srgb(t): return (t.fmt & 0xff) == 0x06

def astc_header(t):
    bw, bh, _ = fmtinfo(t.fmt)
    return struct.pack('<I3B', 0x5CA1AB13, bw, bh, 1) + t.w.to_bytes(3, 'little') + t.h.to_bytes(3, 'little') + (1).to_bytes(3, 'little')

def decode_bc4(blocks, w, h):
    wb = (w + 3) // 4; img = np.zeros((((h + 3) // 4) * 4, wb * 4), np.uint8)
    for bi in range(len(blocks) // 8):
        b = blocks[bi * 8:bi * 8 + 8]; r0, r1 = b[0], b[1]
        if r0 > r1: pal = [r0, r1] + [((7 - i) * r0 + i * r1) // 7 for i in range(1, 7)]
        else: pal = [r0, r1] + [((5 - i) * r0 + i * r1) // 5 for i in range(1, 5)] + [0, 255]
        bits = int.from_bytes(b[2:8], 'little')
        by, bx = divmod(bi, wb)
        for p in range(16):
            img[by * 4 + p // 4, bx * 4 + p % 4] = pal[(bits >> (3 * p)) & 7]
    return Image.fromarray(img[:h, :w], 'L')

def export(d, t, png):
    blocks = get_blocks(d, t)
    ty = t.fmt >> 8
    if ty in ASTC_BLK:
        with tempfile.TemporaryDirectory() as td:
            a = os.path.join(td, 'x.astc'); open(a, 'wb').write(astc_header(t) + blocks)
            subprocess.run([ASTCENC, '-ds' if srgb(t) else '-dl', a, png], check=True, stdout=subprocess.DEVNULL)
    elif ty == 0x1d:
        decode_bc4(blocks, t.w, t.h).save(png)
    else:
        raise ValueError('export fmt %x' % t.fmt)

def encode_bc4_const(t, v):
    wb, hb, bpp, _ = offsets(t)
    return bytes([v, v, 0, 0, 0, 0, 0, 0]) * (wb * hb)

def import_png(d, t, png):
    ty = t.fmt >> 8
    if ty in ASTC_BLK:
        bw, bh, _ = fmtinfo(t.fmt)
        with tempfile.TemporaryDirectory() as td:
            a = os.path.join(td, 'x.astc')
            subprocess.run([ASTCENC, '-cs' if srgb(t) else '-cl', png, a, '%dx%d' % (bw, bh), '-exhaustive'], check=True, stdout=subprocess.DEVNULL)
            raw = open(a, 'rb').read()
        hdr = astc_header(t); assert raw[:16] == hdr, 'size mismatch: %r vs %r' % (raw[:16], hdr)
        put_blocks(d, t, raw[16:])
    else:
        raise ValueError('import fmt %x' % t.fmt)

if __name__ == '__main__':
    cmd, f = sys.argv[1], sys.argv[2]
    d = bytearray(open(f, 'rb').read()); ts = parse(d)
    if cmd == 'list':
        for t in ts: print(t.name, hex(t.fmt), t.w, t.h, 'blkh', t.blkh, 'size', t.size, 'comp', hex(t.comp))
    elif cmd == 'export':
        for t in ts:
            if t.name.split('^')[0].split('+')[0] in sys.argv[4:]: export(d, t, os.path.join(sys.argv[3], t.name.split('^')[0].split('+')[0] + '.png'))
