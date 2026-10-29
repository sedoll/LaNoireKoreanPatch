"""Build the distributable patch: dist/LANoire_KoreanPatch_v<version>.zip

    python build_release.py --version 1.0 [--python-embed build/python-3.13.17-embed-amd64.zip]

Needs the original (unpatched) out.wad.pc - taken from backup/ if present, else from the game -
for the Japanese/tutorial font templates, plus numpy and Pillow for rendering the fonts.
"""
import argparse, glob, json, os, re, shutil, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tools'))
sys.path.insert(0, os.path.join(HERE, 'installer'))
from common import *
import fontgen

UI_TTF = os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts', 'NotoSansKR-VF.ttf')
PEN_TTF = os.path.join(HERE, 'fonts', 'NanumPen.ttf')
TAG_RE = re.compile(r'\[[^\]]*\]')


def merged_translations():
    tr = {}
    for p in sorted(glob.glob(os.path.join(HERE, 'translation', 'b*.jsonl'))):
        for line in open(p, encoding='utf-8'):
            if line.strip():
                r = json.loads(line); tr[r['k']] = r['ko']
    by_id = json.load(open(os.path.join(HERE, 'translation', 'id_overrides.json'), encoding='utf-8'))
    return tr, by_id


def ttf_names(path, ids=(0, 13, 14)):
    """Read copyright / license / license-URL strings from a TrueType name table."""
    d = open(path, 'rb').read()
    n, = struct.unpack_from('>H', d, 4)
    for i in range(n):
        tag, _, off, ln = struct.unpack_from('>4sIII', d, 12 + 16 * i)
        if tag == b'name': break
    _, count, sto = struct.unpack_from('>HHH', d, off)
    out = {}
    for i in range(count):
        pid, eid, lid, nid, l, o = struct.unpack_from('>6H', d, off + 6 + 12 * i)
        if nid in ids and pid == 3 and lid == 0x409:
            out[nid] = d[off + sto + o:off + sto + o + l].decode('utf-16-be')
    return [out[i] for i in ids if i in out]


def build_fonts(dst, chars):
    wad = os.path.join(HERE, 'backup', 'out.wad.pc')
    if not os.path.exists(wad): wad = WAD
    d, ents, names, _ = wad_read(wad)
    tmp = os.path.join(HERE, 'build', 'tpl'); os.makedirs(tmp, exist_ok=True)
    for n in ['japanese_font.fnt', 'japanese_font_0.dds', 'japanese_notebook_font.fnt', 'japanese_notebook_font_0.dds',
              'tutorial_font.fnt', 'tutorial_font_0.dds']:
        i = names.index('out/fonts/' + n)
        open(os.path.join(tmp, n), 'wb').write(d[ents[i][1]:ents[i][1] + ents[i][2]])
    keys = [(os.path.join(tmp, 'tutorial_font.fnt'), os.path.join(tmp, 'tutorial_font_0.dds'))]
    for nm, ttf, size, outline, var in [('japanese_font', UI_TTF, 25, 2, [500]),
                                        ('japanese_notebook_font', PEN_TTF, 36, 0, None)]:
        r = fontgen.build(os.path.join(tmp, nm + '.fnt'), os.path.join(tmp, nm + '_0.dds'), ttf, size, chars,
                          os.path.join(dst, nm + '.fnt'), os.path.join(dst, nm + '_0.dds'),
                          variation=var, outline=outline, extra_fonts=keys)
        print(f'  {nm}: {r["glyphs"]} glyphs, 2048x{r["height"]}, missing {r["missing"]}')
        if r['missing']: raise SystemExit('glyphs missing from ' + ttf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', required=True)
    ap.add_argument('--python-embed', default=os.path.join(HERE, 'build', 'python-3.13.17-embed-amd64.zip'))
    args = ap.parse_args()
    name = f'LANoire_KoreanPatch_v{args.version}'
    out = os.path.join(HERE, 'dist', name)
    shutil.rmtree(out, ignore_errors=True)
    for sub in ('python', 'patcher', 'data/fonts', 'licenses'): os.makedirs(os.path.join(out, sub))

    tr, by_id = merged_translations()
    json.dump({'strings': tr, 'by_id': by_id}, open(os.path.join(out, 'data', 'translation.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    print(f'translations: {len(tr)} strings, {len(by_id)} id overrides')
    chars = set(range(0x20, 0x7f)) | set(fontgen.ksx1001_hangul())
    for ko in list(tr.values()) + list(by_id.values()):
        chars |= {ord(c) for c in TAG_RE.sub('', ko)}
    build_fonts(os.path.join(out, 'data', 'fonts'), sorted(chars))

    for f in ('patcher.py',): shutil.copy(os.path.join(HERE, 'installer', f), os.path.join(out, 'patcher'))
    for f in ('atbstr.py', 'bigpc.py', 'wad.py'): shutil.copy(os.path.join(HERE, 'tools', f), os.path.join(out, 'patcher'))
    for f in ('한글패치_설치.bat', '원본_복구.bat', '사용법.txt'): shutil.copy(os.path.join(HERE, 'installer', f), out)
    with zipfile.ZipFile(args.python_embed) as z: z.extractall(os.path.join(out, 'python'))

    lic = os.path.join(out, 'licenses')
    shutil.copy(os.path.join(HERE, 'fonts', 'NanumPen_LICENSE.txt'), lic)
    open(os.path.join(lic, 'NotoSansKR_LICENSE.txt'), 'w', encoding='utf-8').write(
        'Noto Sans KR (UI 글꼴)\n\n' + '\n\n'.join(ttf_names(UI_TTF)) + '\n')
    shutil.copy(os.path.join(out, 'python', 'LICENSE.txt'), os.path.join(lic, 'Python_LICENSE.txt'))

    zpath = os.path.join(HERE, 'dist', name + '.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for base, _, files in os.walk(out):
            for f in files:
                p = os.path.join(base, f)
                z.write(p, os.path.join(name, os.path.relpath(p, out)))
    print(f'-> {zpath} ({os.path.getsize(zpath) / 1e6:.1f} MB)')


if __name__ == '__main__':
    main()
