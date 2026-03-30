from pathlib import Path
import re, shutil, subprocess, json

ROOT = Path('/Users/ryantaylorvegh/Library/CloudStorage/Dropbox/My Songs')
DOWNLOADS = Path.home() / 'Downloads'
TRASH = Path.home() / '.Trash' / 'OpenClaw-DistroKid-Processing'
TRASH.mkdir(parents=True, exist_ok=True)

# Examples:
# RyanVeghTheMoonlitSunrise12BlazingLightofGod.wav
# RyanVeghTheMoonlitSunrise01MoonlightUpontheFirstSunrise (1).wav
pat = re.compile(r'^RyanVegh(?:TheMoonlitSunrise|Raj|TheEarlyYears)(\d{2})([A-Za-z0-9]+)(?: \(\d+\))?\.(wav|aif|aiff|flac|mp3|m4a)$', re.I)

def split_camel(s: str) -> str:
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', s)
    return s

def norm(s: str) -> str:
    s = s.lower().replace('’', "'")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

# index folders recursively (skip utility internals)
all_dirs = [d for d in ROOT.rglob('*') if d.is_dir() and not d.name.startswith('.') and '_md_archive' not in d.parts and d.suffix.lower() != '.pages']
idx = {}
for d in all_dirs:
    idx.setdefault(norm(d.name), []).append(d)

cands = []
for f in DOWNLOADS.iterdir():
    if not f.is_file():
        continue
    m = pat.match(f.name)
    if not m:
        continue
    title = split_camel(m.group(2)).strip()
    cands.append((f, title))

# dedupe by name pattern keeping non-(1) then newest
by_key = {}
for f, title in cands:
    k = re.sub(r' \(\d+\)(?=\.)', '', f.name)
    by_key.setdefault(k, []).append((f, title))

selected = []
trashed = []
for k, arr in by_key.items():
    arr = sorted(arr, key=lambda t: ((' (' in t[0].stem), -t[0].stat().st_mtime))
    keep = arr[0]
    selected.append(keep)
    for extra, _ in arr[1:]:
        dst = TRASH / extra.name
        if dst.exists():
            dst = TRASH / f"{extra.stem}-dup{extra.suffix}"
        shutil.move(str(extra), str(dst))
        trashed.append({'from': str(extra), 'to_trash': str(dst), 'reason': 'duplicate'})

moved = []
unmatched = []

for f, title in selected:
    key = norm(title)
    choices = idx.get(key, [])
    target = None
    if len(choices) == 1:
        target = choices[0]
    elif len(choices) > 1:
        target = sorted(choices, key=lambda p: len(p.parts))[0]
    else:
        near = [d for d in all_dirs if key and (key in norm(d.name) or norm(d.name) in key)]
        if len(near) == 1:
            target = near[0]

    if not target:
        unmatched.append({'file': f.name, 'parsed_title': title})
        continue

    canonical = target / f"{target.name}.m4a"
    tmp = target / f"{target.name}.__tmp__.m4a"
    r = subprocess.run(['ffmpeg', '-y', '-i', str(f), '-c:a', 'aac', '-b:a', '256k', str(tmp)], capture_output=True, text=True)
    if r.returncode != 0:
        unmatched.append({'file': f.name, 'parsed_title': title, 'error': 'ffmpeg_failed'})
        continue

    if canonical.exists():
        backup = target / f"{target.name} (pre-DistroKid).m4a"
        if backup.exists():
            backup = target / f"{target.name} (pre-DistroKid 2).m4a"
        shutil.move(str(canonical), str(backup))

    shutil.move(str(tmp), str(canonical))
    moved.append({'from': f.name, 'to': str(canonical)})

    if f.exists():
        dst = TRASH / f.name
        if dst.exists():
            dst = TRASH / f"{f.stem}-orig{f.suffix}"
        shutil.move(str(f), str(dst))
        trashed.append({'from': str(f), 'to_trash': str(dst), 'reason': 'source after conversion'})

out = {
    'seen_candidates': len(cands),
    'selected_after_dedupe': len(selected),
    'moved_count': len(moved),
    'unmatched_count': len(unmatched),
    'trashed_count': len(trashed),
    'unmatched': unmatched,
}
outp = Path('/Users/ryantaylorvegh/.openclaw/workspace/distrokid_album_named_process_result.json')
outp.write_text(json.dumps(out, indent=2))
print(outp)
print(json.dumps({'seen': out['seen_candidates'], 'moved': out['moved_count'], 'unmatched': out['unmatched_count']}))