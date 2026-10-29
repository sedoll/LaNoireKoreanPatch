import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import bmfont, numpy as np
from PIL import Image
def render(fnt, dds, lines, out, scale=1.0):
    m = bmfont.parse(open(fnt, 'rb').read())
    at = np.array(Image.open(dds).convert('RGBA')).astype(float) / 255
    ch = {c[0]: c for c in m['chars']}
    W = 1400; H = m['lineh'] * len(lines) + 20
    img = np.zeros((H, W, 3)); img[:] = (0.55, 0.6, 0.65)
    for li, s in enumerate(lines):
        x = 10; y0 = 10 + li * m['lineh']
        for c in s:
            g = ch.get(ord(c))
            if not g: x += 10; continue
            cp, gx, gy, w, h, xo, yo, xa, pg, chn = g
            px, py = x + xo, y0 + yo
            if px < 0 or py < 0 or px + w > W or py + h > H: x += xa; continue
            src = at[gy:gy + h, gx:gx + w]
            a = src[..., 3:4]; rgb = src[..., :3]
            reg = img[py:py + h, px:px + w]
            reg[:] = reg * (1 - a) + 0 * a          # outline (black) from alpha
            reg[:] = reg * (1 - rgb) + rgb          # glyph (white) from rgb
            x += xa
    Image.fromarray((img * 255).astype(np.uint8)).save(out)
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    render(sys.argv[1], sys.argv[2], sys.argv[4:], sys.argv[3])
