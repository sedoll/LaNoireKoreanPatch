"""Dump every StringTableString (English + IDs) from the game into extract/strings.jsonl."""
import json, os, sys, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from common import *
import atbstr, bigpc

out = sys.argv[1]
os.makedirs(os.path.dirname(out), exist_ok=True)
rows = []
def dump(src, blob):
    for i, r in enumerate(atbstr.records(blob)):
        en = atbstr.text(blob, r['fields']['en'])
        rows.append(dict(src=src, n=i, id=r['id'], en=en, ja=atbstr.text(blob, r['fields']['ja'])))

d, ents, names, tail = wad_read(WAD)
i = names.index(ROOT_ATB)
dump('wad:' + ROOT_ATB, d[ents[i][1]:ents[i][1] + ents[i][2]])
for bn in BIG_SOURCES:
    b = bigpc.Big(PC + bn)
    for e in b.entries:
        if b.read(e, first_only=True)[:4] != b'ATB\x04': continue
        dump(f'big:{bn}:{e.hash:08x}', b.read(e))
with open(out, 'w', encoding='utf-8') as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(len(rows), 'records,', len({r['en'] for r in rows}), 'unique english')
