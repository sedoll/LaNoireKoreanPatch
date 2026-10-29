"""Split source/strings.jsonl (from extract.py) into translation batches source/batches/bNNN.jsonl.

Unique English strings in game order, ~35-45k characters per batch, tag-only strings skipped.
The keys (sha1 of the English text) are what translation/*.jsonl refer to.
"""
import hashlib, json, os, re, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = re.compile(r'\[[^\]]*\]')

rows = [json.loads(l) for l in open(os.path.join(HERE, 'source', 'strings.jsonl'), encoding='utf-8')]
seen, order = set(), []
for r in rows:
    k = hashlib.sha1(r['en'].encode('utf-8')).hexdigest()[:12]
    if k in seen or not TAG.sub('', r['en']).strip(): continue
    seen.add(k); order.append(dict(k=k, id=r['id'], en=r['en'], src=r['src']))

batches, cur, size = [], [], 0
for u in order:
    if size >= 35000 and (cur and cur[-1]['src'] != u['src'] or size >= 45000):
        batches.append(cur); cur, size = [], 0
    cur.append(u); size += len(u['en'])
if cur: batches.append(cur)

os.makedirs(os.path.join(HERE, 'source', 'batches'), exist_ok=True)
for i, b in enumerate(batches):
    with open(os.path.join(HERE, 'source', 'batches', f'b{i:03d}.jsonl'), 'w', encoding='utf-8') as f:
        for u in b: f.write(json.dumps(dict(k=u['k'], id=u['id'], en=u['en']), ensure_ascii=False) + '\n')
print(f'{len(order)} strings -> {len(batches)} batches')
