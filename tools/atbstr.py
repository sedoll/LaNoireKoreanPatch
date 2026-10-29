"""Locate StringTableString records inside an ATB blob and rewrite one language field."""
import struct, re

LANGS = {bytes.fromhex('0002832c'): 'en', bytes.fromhex('5ece75af'): 'fr', bytes.fromhex('a14034a2'): 'de',
         bytes.fromhex('cf69b957'): 'it', bytes.fromhex('6e41970a'): 'ja', bytes.fromhex('75f166eb'): 'ru',
         bytes.fromhex('34f51834'): 'es'}
LANG_HASH = {v: k for k, v in LANGS.items()}
ID_FIELD = b'\x08\xee\x2c\x93\xe5'
ORDER = ['en', 'fr', 'de', 'it', 'ja', 'ru', 'es']

def records(d):
    """Yield dicts: id, fields {lang: (len_off, data_off, length)}, end offset (pointing at terminator)."""
    for m in re.finditer(re.escape(ID_FIELD), d):
        p = m.end()
        ln, = struct.unpack_from('<H', d, p)
        if ln in (0, 0xffff) or ln > 512: continue
        sid = d[p + 2:p + 2 + ln]
        try: sid = sid.decode('ascii')
        except UnicodeDecodeError: continue
        p += 2 + ln
        fields = {}
        while p + 7 <= len(d) and d[p] == 0x0b and d[p + 1:p + 5] in LANGS:
            lang = LANGS[d[p + 1:p + 5]]
            l, = struct.unpack_from('<H', d, p + 5)
            dl = 0 if l in (0, 0xffff) else l
            fields[lang] = (p + 5, p + 7, dl)
            p += 7 + dl
        if 'en' not in fields: continue
        yield dict(id=sid, start=m.start(), fields=fields, end=p, term=d[p] if p < len(d) else None)

def text(d, f):
    _, o, l = f
    return d[o:o + l].decode('utf-8')

def patch(d, repl, lang='ja'):
    """repl: {record_start: new_text}. Returns new blob with the given language field replaced."""
    out = []; last = 0
    edits = []
    for r in records(d):
        if r['start'] in repl:
            f = r['fields'].get(lang)
            if f is None: raise ValueError(f"no {lang} field for {r['id']}")
            edits.append((f, repl[r['start']]))
    for (lo, do, l), new in sorted(edits, key=lambda e: e[0][0]):
        b = new.encode('utf-8')
        if len(b) > 0xfffe: raise ValueError('string too long')
        out.append(d[last:lo]); out.append(struct.pack('<H', len(b))); out.append(b)
        last = do + l
    out.append(d[last:])
    return b''.join(out), len(edits)
