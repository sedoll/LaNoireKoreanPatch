import struct, zlib, os

def align(x, a): return (x + a - 1) & ~(a - 1)

class Entry:
    __slots__ = ('hash', 'off', 'size1', 'size2', 'size3', 'raw_off')

class Big:
    def __init__(self, path):
        self.path = path
        self.f = open(path, 'rb')
        self.f.seek(0, 2); self.fsize = self.f.tell()
        self.f.seek(self.fsize - 4)
        tsz, = struct.unpack('<I', self.f.read(4))
        self.table_off = self.fsize - tsz
        self.f.seek(self.table_off)
        self.atype, n = struct.unpack('<2I', self.f.read(8))
        self.entries = []
        for _ in range(n):
            e = Entry()
            e.hash, e.raw_off, e.size1, e.size2, e.size3 = struct.unpack('<5I', self.f.read(20))
            e.off = e.raw_off << 4
            self.entries.append(e)

    def seg_header(self, e):
        f = self.f; f.seek(e.off)
        hdr = f.read(12)
        if hdr[:4] != b'sges':
            return None
        typ, nch, u0, u1, u2, u3 = struct.unpack('<2H4B', hdr[4:])
        objs = struct.unpack(f'<{u0}I', f.read(4 * u0)) if u0 else ()
        chunks = []
        pos = align(e.off + 12 + 4 * u0 + 4 * nch, 16)
        for _ in range(nch):
            sz, fl, co = struct.unpack('<H2B', f.read(4))
            sz += 0x10000 * co
            chunks.append((pos, sz, fl)); pos += sz
        return dict(type=typ, u=(u0, u1, u2, u3), objs=objs, chunks=chunks, end=pos)

    def read(self, e, first_only=False):
        h = self.seg_header(e)
        f = self.f
        if h is None:
            size = e.size3 or (e.size1 + e.size2)
            f.seek(e.off); return f.read(min(size, 4096) if first_only else size)
        out = []
        for pos, sz, fl in h['chunks']:
            f.seek(pos); raw = f.read(sz)
            out.append(zlib.decompress(raw, -15) if fl & 0x10 else raw)
            if first_only: break
        return b''.join(out)

CHUNK = 0x20000

def make_segs(data):
    """Serialise data as a 'sges' type-7 entry of deflated 128 KiB chunks (same layout as the originals)."""
    comp = []
    for i in range(0, len(data), CHUNK):
        c = zlib.compressobj(9, zlib.DEFLATED, -15)
        z = c.compress(data[i:i + CHUNK]) + c.flush()
        comp.append(z + b'\0' * (align(len(z), 16) - len(z)))
    hdr = b'sges' + struct.pack('<2H4B', 7, len(comp), 0, 0, 0, 0)
    for z in comp:
        assert len(z) < 0x1000000
        hdr += struct.pack('<H2B', len(z) & 0xffff, 0x10, len(z) >> 16)
    hdr += b'\0' * (align(len(hdr), 16) - len(hdr))
    return hdr + b''.join(comp)

def append_entries(path, new_data):
    """new_data: {hash: decompressed bytes}. Appends new segs blobs after the old data and
    writes a fresh table; untouched entries keep pointing at their original bytes."""
    b = Big(path)
    f = b.f; f.seek(b.table_off); old_table = f.read()
    f.close()
    by_hash = {e.hash: e for e in b.entries}
    with open(path, 'r+b') as w:
        pos = align(b.table_off, 16)
        w.seek(b.table_off); w.write(b'\0' * (pos - b.table_off))
        for h, data in new_data.items():
            e = by_hash[h]
            blob = make_segs(data)
            w.seek(pos); w.write(blob)
            e.raw_off = pos >> 4; e.size1 = len(data); e.size2 = 0; e.size3 = len(blob)
            pos = align(pos + len(blob), 16)
            w.write(b'\0' * (pos - w.tell()))
        tbl = struct.pack('<2I', b.atype, len(b.entries))
        for e in b.entries:
            tbl += struct.pack('<5I', e.hash, e.raw_off, e.size1, e.size2, e.size3)
        tbl += old_table[8 + 20 * len(b.entries):-4]  # keep whatever trailer the original had
        tbl += struct.pack('<I', len(tbl) + 4)
        w.seek(pos); w.write(tbl); w.truncate()
