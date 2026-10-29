"""out.wad.pc reader/writer (stdlib only)."""
import struct

def wad_read(path):
    f = open(path, 'rb'); d = f.read()
    n, = struct.unpack_from('<I', d, 4)
    ents = [list(struct.unpack_from('<3I', d, 8 + 12 * i)) for i in range(n)]
    last = max(ents, key=lambda e: e[1]); p = last[1] + last[2]
    names = []
    for _ in range(n):
        l, = struct.unpack_from('<H', d, p); names.append(d[p + 2:p + 2 + l].decode('latin1')); p += 2 + l
    return d, ents, names, d[p:]

def wad_write(path, d, ents, names, tail, replace):
    """replace: {name: bytes}. Rebuilds the WAD contiguously in the original data order."""
    order = sorted(range(len(ents)), key=lambda i: ents[i][1])
    pos = 8 + 12 * len(ents)
    blobs = []
    new = [list(e) for e in ents]
    start = min(e[1] for e in ents)
    gap0 = d[pos:start]  # keep any header padding as-is
    pos = start
    for i in order:
        data = replace.get(names[i])
        if data is None: data = d[ents[i][1]:ents[i][1] + ents[i][2]]
        new[i][1] = pos; new[i][2] = len(data); blobs.append(data); pos += len(data)
    with open(path, 'wb') as f:
        f.write(d[:8])
        for e in new: f.write(struct.pack('<3I', *e))
        f.write(gap0)
        for b in blobs: f.write(b)
        for nm in names:
            b = nm.encode('latin1'); f.write(struct.pack('<H', len(b))); f.write(b)
        f.write(tail)
