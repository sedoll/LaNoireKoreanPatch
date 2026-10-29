"""Check a translated batch: python tools/check_batch.py b007

Reports source keys with no translation yet and translations whose [tags] differ from the English.
"""
import glob, json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = re.compile(r'\[[^\]]*\]')
b = sys.argv[1]
src = [json.loads(l) for l in open(os.path.join(HERE, 'source', 'batches', b + '.jsonl'), encoding='utf-8')]
tr = {}
for p in sorted(glob.glob(os.path.join(HERE, 'translation', b + '_*.jsonl'))):
    for n, line in enumerate(open(p, encoding='utf-8'), 1):
        if not line.strip(): continue
        try: r = json.loads(line)
        except json.JSONDecodeError as e: print(f'BAD JSON {os.path.basename(p)}:{n}: {e}'); continue
        tr[r['k']] = r['ko']
missing = [s for s in src if s['k'] not in tr]
bad = [s for s in src if s['k'] in tr and sorted(TAG.findall(tr[s['k']])) != sorted(TAG.findall(s['en']))]
newline = [s for s in src if s['k'] in tr and '\n' in tr[s['k']]]
print(f'{b}: {len(src)} lines, {len(tr)} translated, {len(missing)} missing, {len(bad)} tag mismatches, {len(newline)} with newlines')
for s in missing[:20]: print('  MISSING', s['k'], s['id'])
for s in bad[:20]: print('  TAGS', s['k'], s['id'], '| en:', TAG.findall(s['en']), '| ko:', TAG.findall(tr[s['k']]))
for s in newline[:20]: print('  NEWLINE', s['k'], s['id'])
