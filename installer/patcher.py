"""L.A. Noire Korean patch - installer / uninstaller (Python standard library only).

    patcher.py install [game folder]
    patcher.py uninstall [game folder]

How it works: Korean text is written into the Russian language slot of the game's string
tables, every UI font definition's Russian entry is pointed at two prebuilt Korean bitmap fonts
(they replace the unused Japanese fonts), Cyrillic UI artwork is swapped for the English one and
settings.ini is switched to Russian. LANoire.exe is never modified: the Rockstar Games Launcher
refuses to start a game whose exe signature is broken.
"""
import ctypes, hashlib, json, os, re, shutil, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import atbstr, bigpc
from wad import wad_read, wad_write

DATA = os.path.join(ROOT, 'data')
BACKUP = os.path.join(ROOT, 'backup')
BIG_SOURCES = ['cases.big.pc'] + [f'dlc.dlc{i}.big.pc' for i in (1, 2, 3, 4, 5, 6, 8, 9)]
FULL_COPY = ['out.wad.pc', 'cases.big.pc']
ROOT_ATB = 'out/attribute/root.atb.pc'
FONTS = ['japanese_font.fnt', 'japanese_font_0.dds', 'japanese_notebook_font.fnt', 'japanese_notebook_font_0.dds']
SLOT = 'ru'
TAG = re.compile(r'\[[^\]]*\]')
FONT_JA = re.compile(rb'\x08\x6e\x41\x97\x0a(..)(fonts/[a-z_]+\.fnt)\x08\x75\xf1\x66\xeb(..)(fonts/[a-z_]+\.fnt)', re.S)
RU_FONT = re.compile(rb'\x08\x75\xf1\x66\xeb..fonts/japanese_', re.S)


class PatchError(Exception):
    pass


# ---------------------------------------------------------------- locating things
def is_game_dir(p):
    return p and os.path.isfile(os.path.join(p, 'LANoire.exe')) and os.path.isfile(os.path.join(p, 'final', 'pc', 'out.wad.pc'))


def steam_libraries():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as k:
            steam = winreg.QueryValueEx(k, 'SteamPath')[0]
    except OSError:
        return []
    libs = [steam]
    vdf = os.path.join(steam, 'steamapps', 'libraryfolders.vdf')
    if os.path.isfile(vdf):
        libs += [p.replace('\\\\', '\\') for p in re.findall(r'"path"\s+"([^"]+)"', open(vdf, encoding='utf-8', errors='replace').read())]
    return libs


def find_game(arg):
    cands = [arg, os.path.dirname(ROOT), ROOT] + [os.path.join(l, 'steamapps', 'common', 'L.A.Noire') for l in steam_libraries()]
    for c in cands:
        if is_game_dir(c): return os.path.abspath(c)
    print('L.A. Noire 설치 폴더를 찾지 못했습니다.')
    p = input('LANoire.exe가 있는 폴더 경로를 입력하세요: ').strip().strip('"')
    if is_game_dir(p): return os.path.abspath(p)
    raise PatchError('입력한 폴더에 LANoire.exe 또는 final\\pc\\out.wad.pc가 없습니다.')


def documents_dir():
    buf = ctypes.create_unicode_buffer(260)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0:  # CSIDL_PERSONAL
        return buf.value
    return os.path.join(os.path.expanduser('~'), 'Documents')


def settings_path():
    return os.path.join(documents_dir(), 'Rockstar Games', 'L.A. Noire', 'settings.ini')


def game_running():
    try:
        import subprocess
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq LANoire.exe'], capture_output=True, text=True).stdout
        return 'LANoire.exe' in out
    except OSError:
        return False


# ---------------------------------------------------------------- backup / restore
def backup(pc):
    os.makedirs(BACKUP, exist_ok=True)
    for name in FULL_COPY:
        dst = os.path.join(BACKUP, name)
        if not os.path.exists(dst):
            print(f'  원본 백업: {name}'); shutil.copyfile(pc + name, dst + '.tmp'); os.replace(dst + '.tmp', dst)
    for name in BIG_SOURCES:
        if name in FULL_COPY: continue
        meta = os.path.join(BACKUP, name + '.tail.json')
        if os.path.exists(meta): continue
        b = bigpc.Big(pc + name)
        b.f.seek(b.table_off); table = b.f.read(); b.f.close()
        open(os.path.join(BACKUP, name + '.tail'), 'wb').write(table)
        json.dump(dict(table_off=b.table_off, size=b.fsize), open(meta, 'w'))


def restore(pc):
    for name in FULL_COPY:
        src = os.path.join(BACKUP, name)
        if os.path.exists(src): shutil.copyfile(src, pc + name)
    for name in BIG_SOURCES:
        meta = os.path.join(BACKUP, name + '.tail.json')
        if not os.path.exists(meta): continue
        m = json.load(open(meta))
        table = open(os.path.join(BACKUP, name + '.tail'), 'rb').read()
        with open(pc + name, 'r+b') as f:
            f.seek(m['table_off']); f.write(table); f.truncate(m['size'])


def wad_is_patched(path):
    d, ents, names, _ = wad_read(path)
    i = names.index(ROOT_ATB)
    return bool(RU_FONT.search(d[ents[i][1]:ents[i][1] + ents[i][2]]))


def set_language(lang):
    p = settings_path()
    if not os.path.exists(p):
        print(f'  settings.ini가 없습니다({p}). 게임을 한 번 실행했다가 끈 뒤 다시 설치해 주세요.')
        return False
    txt = open(p, encoding='utf-8', errors='replace').read()
    new = re.sub(r'(?m)^Language:.*$', 'Language:' + lang, txt)
    if 'Language:' not in new: new = new.replace('[LANSettings]', '[LANSettings]\nLanguage:' + lang, 1)
    open(p, 'w', encoding='utf-8').write(new)
    print(f'  게임 언어 설정 -> {lang}')
    return True


# ---------------------------------------------------------------- patching
def key(en):
    return hashlib.sha1(en.encode('utf-8')).hexdigest()[:12]


def patch_atb(blob, tr, by_id, stats):
    repl = {}
    for r in atbstr.records(blob):
        en = atbstr.text(blob, r['fields']['en'])
        if r['id'] in by_id:  # e.g. Japan-only film reel titles whose English text is just [BLANK]
            repl[r['start']] = by_id[r['id']]; stats['korean'] += 1; continue
        ko = tr.get(key(en))
        if ko is None or sorted(TAG.findall(ko)) != sorted(TAG.findall(en)):
            ko = en; stats['english'] += 1
        else:
            stats['korean'] += 1
        repl[r['start']] = ko
    return atbstr.patch(blob, repl, SLOT)[0]


def patch_fonts(blob):
    out = bytearray(); last = 0
    for m in FONT_JA.finditer(blob):
        ja = m.group(2)
        out += blob[last:m.start(3)] + struct.pack('<H', len(ja)) + ja
        last = m.end(4)
    return bytes(out + blob[last:])


def install(game):
    pc = os.path.join(game, 'final', 'pc') + os.sep
    data = json.load(open(os.path.join(DATA, 'translation.json'), encoding='utf-8'))
    tr, by_id = data['strings'], data['by_id']
    if not os.path.exists(os.path.join(BACKUP, 'out.wad.pc')) and wad_is_patched(pc + 'out.wad.pc'):
        raise PatchError('게임 파일이 이미 한글패치된 상태인데 이 폴더에 원본 백업이 없습니다.\n'
                         'Steam에서 [속성 > 설치된 파일 > 게임 파일 무결성 검사]로 원본을 복구한 뒤 다시 설치해 주세요.')
    print('[1/4] 원본 파일 백업 / 복원'); backup(pc); restore(pc)
    stats = dict(korean=0, english=0)

    print('[2/4] UI 텍스트와 폰트 패치 (out.wad.pc)')
    d, ents, names, tail = wad_read(pc + 'out.wad.pc')
    def wget(n):
        i = names.index(n); return d[ents[i][1]:ents[i][1] + ents[i][2]]
    repl = {ROOT_ATB: patch_fonts(patch_atb(wget(ROOT_ATB), tr, by_id, stats))}
    for f in FONTS:
        repl['out/fonts/' + f] = open(os.path.join(DATA, 'fonts', f), 'rb').read()
    for n in names:  # Cyrillic UI artwork -> English artwork
        if '/russian/' in n and n.replace('/russian/', '/english/') in names:
            repl[n] = wget(n.replace('/russian/', '/english/'))
    wad_write(pc + 'out.wad.pc', d, ents, names, tail, repl)
    del d

    print('[3/4] 대사·자막 패치 (cases / dlc)')
    for bn in BIG_SOURCES:
        b = bigpc.Big(pc + bn); mods = {}
        for e in b.entries:
            if b.read(e, first_only=True)[:4] != b'ATB\x04': continue
            blob = b.read(e)
            new = patch_atb(blob, tr, by_id, stats)
            if new != blob: mods[e.hash] = new
        b.f.close()
        if mods: bigpc.append_entries(pc + bn, mods)
        print(f'  {bn}')

    print('[4/4] 게임 언어 설정')
    ok = set_language('Russian')
    print(f"\n완료: 한국어 {stats['korean']}줄 적용 (영어 유지 {stats['english']}줄)")
    if not ok: print('※ settings.ini를 찾지 못해 언어 설정은 하지 못했습니다.')


def uninstall(game):
    pc = os.path.join(game, 'final', 'pc') + os.sep
    if not os.path.exists(os.path.join(BACKUP, 'out.wad.pc')):
        raise PatchError('이 폴더에 원본 백업이 없습니다. Steam의 게임 파일 무결성 검사로 복구해 주세요.')
    print('원본 파일 복원 중...'); restore(pc)
    set_language('English')
    print('\n완료: 원래 영어 상태로 되돌렸습니다.')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'install'
    try:
        game = find_game(sys.argv[2] if len(sys.argv) > 2 else None)
        print(f'게임 폴더: {game}\n')
        if game_running(): raise PatchError('게임이 실행 중입니다. 게임과 PlayLAN을 완전히 종료한 뒤 다시 실행해 주세요.')
        {'install': install, 'uninstall': uninstall}[cmd](game)
    except PatchError as e:
        print(f'\n[오류] {e}'); sys.exit(1)
    except PermissionError as e:
        # exit code 5 (= ERROR_ACCESS_DENIED) makes the .bat relaunch itself as administrator
        print(f'\n[오류] 파일에 쓸 수 없습니다: {e.filename}\n게임이 실행 중이거나 관리자 권한이 필요합니다.'); sys.exit(5)


if __name__ == '__main__':
    main()
