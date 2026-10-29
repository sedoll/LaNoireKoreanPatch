"""Translate the still-missing lines with a local Ollama model (default: gemma4:31b-cloud).

    python tools/translate_ollama.py                 all missing lines, UI and early cases first
    python tools/translate_ollama.py --batches b024 --limit 30

Results go to translation/bNNN_g.jsonl (appended as chunks finish, so the run can be resumed).
Only lines whose [tags] match the English are kept; the rest are retried one by one.
"""
import argparse, glob, json, os, re, sys, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = re.compile(r'\[[^\]]*\]')
PRIORITY = ['b001', 'b002', 'b004', 'b024', 'b022', 'b023']
GUIDE = open(os.path.join(HERE, 'translation_guide.md'), encoding='utf-8').read()
SYSTEM = GUIDE + """

## 출력 형식
입력은 JSON 배열이다. 각 항목 {"i": 번호, "id": 문맥용 id, "en": 영어}.
반드시 다음 JSON 객체만 출력한다: {"translations": [{"i": 번호, "ko": "한국어 번역"}, ...]}
모든 항목을 빠짐없이 번역한다. 대괄호 태그는 원문과 똑같이 남긴다. 설명이나 다른 텍스트는 출력하지 않는다."""
lock = threading.Lock()


def load_done():
    done = set()
    for p in glob.glob(os.path.join(HERE, 'translation', 'b*.jsonl')):
        for line in open(p, encoding='utf-8'):
            try: done.add(json.loads(line)['k'])
            except (json.JSONDecodeError, KeyError): pass
    return done


def ask(model, items, host):
    payload = [{'i': i, 'id': s['id'], 'en': s['en']} for i, s in enumerate(items)]
    body = json.dumps({'model': model, 'stream': False, 'format': 'json', 'think': False,
                       'options': {'temperature': 0.3},
                       'messages': [{'role': 'system', 'content': SYSTEM},
                                    {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}]}).encode()
    req = urllib.request.Request(host + '/api/chat', body, {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r:
        content = json.loads(r.read())['message']['content']
    # the cloud model ignores `format` and wraps its answer in a ```json fence
    content = content[content.find('{'):content.rfind('}') + 1]
    out = {}
    for t in json.loads(content).get('translations', []):
        try: out[int(t['i'])] = str(t['ko'])
        except (KeyError, ValueError, TypeError): pass
    return out


def valid(en, ko):
    return ko.strip() and '\n' not in ko and sorted(TAG.findall(ko)) == sorted(TAG.findall(en))


def work(batch, items, args, stats):
    good, bad = {}, list(items)
    for attempt in range(3):
        if not bad: break
        todo = [bad] if attempt == 0 else [[s] for s in bad]  # retry failures one at a time
        bad = []
        for chunk in todo:
            try: res = ask(args.model, chunk, args.host)
            except Exception as e:
                print(f'  {batch}: request failed ({e}); retrying', flush=True); time.sleep(5); bad += chunk; continue
            for i, s in enumerate(chunk):
                ko = res.get(i)
                if ko is not None and valid(s['en'], ko): good[s['k']] = ko
                else: bad.append(s)
    with lock:
        with open(os.path.join(HERE, 'translation', f'{batch}_g.jsonl'), 'a', encoding='utf-8') as f:
            for k, ko in good.items(): f.write(json.dumps({'k': k, 'ko': ko}, ensure_ascii=False) + '\n')
        stats['done'] += len(good); stats['failed'] += len(bad)
        print(f"{batch}: +{len(good)} ok, {len(bad)} failed | total {stats['done']}/{stats['total']}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='gemma4:31b-cloud')
    ap.add_argument('--host', default='http://localhost:11434')
    ap.add_argument('--batches', nargs='*')
    ap.add_argument('--limit', type=int, default=0, help='max lines (for a test run)')
    ap.add_argument('--chunk', type=int, default=25)
    ap.add_argument('--workers', type=int, default=3)
    args = ap.parse_args()
    names = sorted(os.path.basename(p)[:-6] for p in glob.glob(os.path.join(HERE, 'source', 'batches', 'b*.jsonl')))
    order = args.batches or (PRIORITY + [b for b in names if b not in PRIORITY])
    done = load_done()
    jobs = []
    for b in order:
        src = [json.loads(l) for l in open(os.path.join(HERE, 'source', 'batches', b + '.jsonl'), encoding='utf-8')]
        miss = [s for s in src if s['k'] not in done]
        for i in range(0, len(miss), args.chunk): jobs.append((b, miss[i:i + args.chunk]))
    if args.limit:
        keep, n = [], 0
        for b, items in jobs:
            if n >= args.limit: break
            keep.append((b, items[:args.limit - n])); n += len(keep[-1][1])
        jobs = keep
    stats = dict(done=0, failed=0, total=sum(len(i) for _, i in jobs))
    print(f"{stats['total']} lines in {len(jobs)} chunks, model {args.model}", flush=True)
    with ThreadPoolExecutor(args.workers) as ex:
        for b, items in jobs: ex.submit(work, b, items, args, stats)
    print(f"finished: {stats['done']} translated, {stats['failed']} failed", flush=True)


if __name__ == '__main__':
    main()
