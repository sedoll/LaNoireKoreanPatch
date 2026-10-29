"""Minimal DXT5 (BC3) encoder/DDS writer for font atlases (numpy, vectorised per block)."""
import numpy as np, struct

def _blocks(a):  # (H,W,C) -> (nb,16,C)
    h, w, c = a.shape
    return a.reshape(h // 4, 4, w // 4, 4, c).swapaxes(1, 2).reshape(-1, 16, c)

def encode(rgba):
    rgba = np.asarray(rgba, dtype=np.uint8)
    h, w, _ = rgba.shape
    assert h % 4 == 0 and w % 4 == 0
    b = _blocks(rgba).astype(np.int32)
    nb = b.shape[0]
    # alpha: 8-level mode, a0 > a1
    al = b[:, :, 3]
    a0 = al.max(1); a1 = al.min(1)
    same = a0 == a1
    a1n = np.where(same & (a0 > 0), a0 - 1, a1); a0n = np.where(same & (a0 == 0), 1, a0)
    a0, a1 = a0n, a1n
    pal = np.stack([a0, a1] + [((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)], 1)  # (nb,8)
    ai = np.abs(al[:, :, None] - pal[:, None, :]).argmin(2).astype(np.uint64)  # (nb,16)
    abits = np.zeros(nb, np.uint64)
    for i in range(16): abits |= ai[:, i] << np.uint64(3 * i)
    # colour: grayscale-friendly endpoints along luminance (min/max of each channel)
    rgb = b[:, :, :3]
    lum = rgb.sum(2)
    imax = lum.argmax(1); imin = lum.argmin(1)
    cmax = rgb[np.arange(nb), imax]; cmin = rgb[np.arange(nb), imin]
    def to565(c): return ((c[:, 0] * 31 + 127) // 255 << 11) | ((c[:, 1] * 63 + 127) // 255 << 5) | ((c[:, 2] * 31 + 127) // 255)
    def from565(v): return np.stack([((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31], 1)
    c0 = to565(cmax); c1 = to565(cmin)
    swap = c0 < c1
    c0, c1 = np.where(swap, c1, c0), np.where(swap, c0, c1)
    eq = c0 == c1
    p0 = from565(c0); p1 = from565(c1)
    cp = np.stack([p0, p1, (2 * p0 + p1) // 3, (p0 + 2 * p1) // 3], 1)  # (nb,4,3)
    ci = ((rgb[:, :, None, :] - cp[:, None, :, :]) ** 2).sum(3).argmin(2).astype(np.uint32)
    ci = np.where(eq[:, None], 0, ci)
    cbits = np.zeros(nb, np.uint32)
    for i in range(16): cbits |= ci[:, i] << np.uint32(2 * i)
    out = np.zeros((nb, 16), np.uint8)
    out[:, 0] = a0; out[:, 1] = a1
    for k in range(6): out[:, 2 + k] = (abits >> np.uint64(8 * k)) & np.uint64(0xff)
    out[:, 8] = c0 & 0xff; out[:, 9] = c0 >> 8; out[:, 10] = c1 & 0xff; out[:, 11] = c1 >> 8
    for k in range(4): out[:, 12 + k] = (cbits >> np.uint32(8 * k)) & 0xff
    return out.tobytes()

def dds(rgba):
    rgba = np.asarray(rgba); h, w, _ = rgba.shape
    data = encode(rgba)
    hdr = struct.pack('<4s7I44x', b'DDS ', 124, 0x81007, h, w, len(data), 0, 0)
    pf = struct.pack('<2I4s5I', 32, 4, b'DXT5', 0, 0, 0, 0, 0)
    caps = struct.pack('<5I', 0x1000, 0, 0, 0, 0)
    return hdr + pf + caps + data
