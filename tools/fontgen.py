"""Rebuild a Japanese BMFont (.fnt + DXT5 .dds) with Hangul glyphs.

Keeps the original glyphs for Latin, punctuation and the controller-button icons,
drops kana/kanji, and renders the requested Korean characters with a TTF font.
"""
import struct, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import bmfont, dxt5

def is_cjk_drop(cp):
    return 0x3040 <= cp < 0x3100 or 0x3400 <= cp < 0xa000 or 0xf900 <= cp < 0xfb00

def ksx1001_hangul():
    out = []
    for cp in range(0xac00, 0xd7a4):
        try:
            if len(chr(cp).encode('euc-kr')) == 2: out.append(cp)
        except UnicodeEncodeError: pass
    return out

def render_glyph(font, ch, pad, outline, yshift, mono_adv=None):
    """Return (rgba ndarray, xoffset, yoffset_from_top, xadvance) in BMFont terms (top = line top)."""
    asc, desc = font.getmetrics()
    l, t, r, b = font.getbbox(ch, anchor='ls')
    adv = round(font.getlength(ch))
    if mono_adv: adv = mono_adv
    if r <= l or b <= t:
        return None, 0, 0, adv
    w = r - l + 2 * pad; h = b - t + 2 * pad
    im = Image.new('L', (w, h), 0)
    ImageDraw.Draw(im).text((pad - l, pad - t), ch, font=font, fill=255, anchor='ls')
    glyph = np.array(im)
    if outline > 0:
        halo = im.filter(ImageFilter.MaxFilter(2 * outline + 1)).filter(ImageFilter.GaussianBlur(0.8))
        a = np.maximum(np.array(halo), glyph)
    else:
        a = glyph
    rgba = np.dstack([glyph, glyph, glyph, a])
    return rgba, l - pad, t - pad, adv

def pack(glyphs, width, spacing=1):
    """Shelf packer. glyphs: list of (key, w, h). Returns {key: (x, y)}, height."""
    pos = {}; x = y = rowh = 0
    for key, w, h in sorted(glyphs, key=lambda g: -g[2]):
        if x + w > width:
            x = 0; y += rowh + spacing; rowh = 0
        pos[key] = (x, y); x += w + spacing; rowh = max(rowh, h)
    return pos, y + rowh

def build(orig_fnt, orig_dds, ttf, size, chars, out_fnt, out_dds, base_adjust=0, ttf_index=0,
          variation=None, outline=2, keep_ascii=True, max_height=2048, extra_fonts=()):
    m = bmfont.parse(open(orig_fnt, 'rb').read())
    atlas = np.array(Image.open(orig_dds).convert('RGBA'))
    base = m['base']
    font = ImageFont.truetype(ttf, size, index=ttf_index)
    if variation: font.set_variation_by_axes(variation)
    items = {}  # cp -> (rgba, xoff, yoff, xadv)
    for c in m['chars']:
        cp, x, y, w, h, xo, yo, xa, pg, chn = c
        if is_cjk_drop(cp): continue
        if not keep_ascii and 0x21 <= cp < 0x7f: continue
        items[cp] = (atlas[y:y + h, x:x + w].copy(), xo, yo, xa)
    # keyboard/mouse key-cap icons that only exist in the EFIGS fonts (U+21xx, U+FFxx)
    for efnt, edds in extra_fonts:
        em = bmfont.parse(open(efnt, 'rb').read())
        eat = np.array(Image.open(edds).convert('RGBA'))
        for cp, x, y, w, h, xo, yo, xa, pg, chn in em['chars']:
            if cp >= 0xff00 or (cp >= 0x2100 and cp not in items):
                items[cp] = (eat[y:y + h, x:x + w].copy(), xo, yo + base - em['base'], xa)
    hangul_adv = round(font.getlength('가'))
    for cp in sorted(set(chars)):
        if cp in items and not (0xac00 <= cp < 0xd7a4 or 0x3130 <= cp < 0x3190): continue
        rgba, xo, top, xa = render_glyph(font, chr(cp), outline + 1, outline, 0)
        if rgba is None and cp != 0x20: continue
        if rgba is None: rgba = np.zeros((1, 1, 4), np.uint8)
        items[cp] = (rgba, xo, base + top + base_adjust, xa)
    missing = [cp for cp in chars if cp not in items and cp > 0x20]
    keys = [(cp, it[0].shape[1], it[0].shape[0]) for cp, it in items.items()]
    width = m['w']
    pos, height = pack(keys, width)
    height = (height + 3) // 4 * 4
    if height > max_height: raise RuntimeError(f'atlas overflow: {len(items)} glyphs need {height}px')
    out = np.zeros((height, width, 4), np.uint8)
    chars_blk = []
    for cp in sorted(items):
        rgba, xo, yo, xa = items[cp]
        x, y = pos[cp]; h, w = rgba.shape[:2]
        out[y:y + h, x:x + w] = rgba
        chars_blk.append(struct.pack('<IHHHHhhhBB', cp, x, y, w, h, xo, yo, xa, 0, 15))
    # rebuild .fnt: same info block, common with new scaleH, page name kept, new chars, no kerning
    blocks = dict(m['blocks'])
    common = bytearray(blocks[2]); struct.pack_into('<H', common, 6, height); blocks[2] = bytes(common)
    blocks[4] = b''.join(chars_blk)
    blocks.pop(5, None)
    fnt = bytearray(b'BMF\x03')
    for t in sorted(blocks):
        fnt += struct.pack('<BI', t, len(blocks[t])) + blocks[t]
    open(out_fnt, 'wb').write(fnt)
    open(out_dds, 'wb').write(dxt5.dds(out))
    return dict(glyphs=len(items), height=height, missing=missing, hangul_adv=hangul_adv)
