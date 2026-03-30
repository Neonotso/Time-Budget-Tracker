from pathlib import Path
import re, shutil, hashlib, subprocess, json

ROOT = Path('/Users/ryantaylorvegh/Library/CloudStorage/Dropbox/My Songs')
DOWNLOADS = Path.home() / 'Downloads'
TRASH = Path.home() / '.Trash' / 'OpenClaw-DistroKid-Processing'
TRASH.mkdir(parents=True, exist_ok=True)

AUDIO_EXT = {'.aif', '.aiff', '.wav', '.flac', '.mp3', '.m4a'}

# ---- matching helpers ----
pat = re.compile(r'^(\d{1,2})([^/]*)?(?:\s*\(\d+\))?\.(aif|aiff|wav|flac|mp3|m4a)$', re.I)

def norm(s: str) -> str:
    s = s.lower().replace('’', "'")
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    s = s.replace('_', ' ').replace('-', ' ')
    s = re.sub(r'\d+', ' ', s)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def pretty_from_download_stem(stem: str) -> str:
    s = re.sub(r'^\d{1,2}', '', stem)
    s = re.sub(r'\(\d+\)$', '', s).strip()
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    s = s.replace('_', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def file_hash(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

# song folder index (top-level only)
song_dirs = [d for d in ROOT.iterdir() if d.is_dir() and not d.name.startswith('.')]
index = {norm(d.name): d for d in song_dirs}

# gather candidate downloads
candidates = []
for f in DOWNLOADS.iterdir():
    if not f.is_file():
        continue
    m = pat.match(f.name)
    if not m:
        continue
    if f.suffix.lower() not in AUDIO_EXT:
        continue
    n = int(m.group(1))
    stem = f.stem
    pretty = pretty_from_download_stem(stem)
    candidates.append((n, pretty, f))

# dedupe exact-content duplicates in downloads first
by_hash = {}
for _, _, f in candidates:
    try:
        h = file_hash(f)
    except Exception:
        h = f'ERR:{f.name}'
    by_hash.setdefault(h, []).append(f)

trashed = []
for h, files in by_hash.items():
    if len(files) <= 1:
        continue
    keep = sorted(files, key=lambda p: ((' (' in p.stem), -p.stat().st_mtime))[0]
    for f in files:
        if f == keep:
            continue
        dst = TRASH / f.name
        if dst.exists():
            dst = TRASH / f"{f.stem}-dup{f.suffix}"
        shutil.move(str(f), str(dst))
        trashed.append({'from': str(f), 'to_trash': str(dst), 'reason': 'download duplicate'})

# refresh candidates after dedupe
candidates = []
for f in DOWNLOADS.iterdir():
    if not f.is_file():
        continue
    m = pat.match(f.name)
    if not m:
        continue
    n = int(m.group(1))
    candidates.append((n, pretty_from_download_stem(f.stem), f))

# match each candidate to folder by normalized title similarity
matched = []
unmatched = []

for n, pretty, f in candidates:
    k = norm(pretty)
    target = index.get(k)
    if not target:
        # relaxed: containment
        options = [d for d in song_dirs if k and (k in norm(d.name) or norm(d.name) in k)]
        if len(options) == 1:
            target = options[0]
    if target:
        matched.append((f, target))
    else:
        unmatched.append({'file': f.name, 'parsed_title': pretty})

# convert/move to canonical <Folder>.m4a
converted = []
moved = []
errors = []

for src, folder in matched:
    canonical = folder / f"{folder.name}.m4a"
    src_ext = src.suffix.lower()
    try:
        # produce converted temp if needed
        if src_ext != '.m4a':
            temp_out = folder / f"{folder.name}.__tmp__.m4a"
            cmd = ['ffmpeg', '-y', '-i', str(src), '-c:a', 'aac', '-b:a', '256k', str(temp_out)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                errors.append({'file': src.name, 'folder': folder.name, 'error': r.stderr[-300:]})
                continue
            converted.append({'from': str(src), 'to': str(temp_out)})
            new_src = temp_out
        else:
            new_src = src

        if canonical.exists():
            # replace canonical with imported master, preserving old one
            backup = folder / f"{folder.name} (pre-DistroKid).m4a"
            if backup.exists():
                backup = folder / f"{folder.name} (pre-DistroKid 2).m4a"
            shutil.move(str(canonical), str(backup))

        shutil.move(str(new_src), str(canonical))
        moved.append({'to': str(canonical), 'from': str(src)})

        # move original src to trash if still exists (converted case)
        if src.exists():
            dst = TRASH / src.name
            if dst.exists():
                dst = TRASH / f"{src.stem}-orig{src.suffix}"
            shutil.move(str(src), str(dst))
            trashed.append({'from': str(src), 'to_trash': str(dst), 'reason': 'original after conversion'})

    except Exception as e:
        errors.append({'file': src.name, 'folder': folder.name, 'error': str(e)})

# markdown update: ensure <Folder>.md exists, title set, official embed first
order = ['overview','audio','chords','chordpro','lyrics','notes']
headers = {
    'overview':'## 🎵 Overview',
    'audio':'## 🎧 Audio & Media',
    'chords':'## 🎸 Chords',
    'chordpro':'## 🎼 ChordPro',
    'lyrics':'## 📝 Lyrics',
    'notes':'## 📓 Notes',
}

def sec_key(h: str):
    hl = h.lower()
    if 'overview' in hl: return 'overview'
    if 'audio' in hl or 'media' in hl: return 'audio'
    if 'chordpro' in hl: return 'chordpro'
    if 'chord' in hl: return 'chords'
    if 'lyric' in hl: return 'lyrics'
    if 'note' in hl: return 'notes'
    return None

embed_re = re.compile(r'!\[\[([^\]]+)\]\]')
md_updated = []

for folder in {t for _, t in matched}:
    md = folder / f"{folder.name}.md"
    if not md.exists():
        # try rename first md in folder
        mds = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower()=='.md']
        if mds:
            mds[0].rename(md)
        else:
            md.write_text(f"---\ntitle: {folder.name}\n---\n\n## 🎵 Overview\n\n## 🎧 Audio & Media\n\n## 🎸 Chords\n\n## 🎼 ChordPro\n\n## 📝 Lyrics\n\n## 📓 Notes\n")

    txt = md.read_text(errors='ignore').replace('\r\n','\n').replace('\r','\n')
    lines = txt.split('\n')

    # frontmatter parse/update title
    i = 0
    front = []
    if lines and lines[0] == '---':
        front.append(lines[0]); i = 1
        saw_title = False
        while i < len(lines):
            line = lines[i]
            if line == '---':
                if not saw_title:
                    front.append(f'title: {folder.name}')
                front.append('---')
                i += 1
                break
            if ':' in line:
                k, v = line.split(':', 1)
                if k.strip().lower() == 'title':
                    line = f'title: {folder.name}'
                    saw_title = True
            front.append(line)
            i += 1
        while i < len(lines) and lines[i] == '':
            i += 1
    else:
        front = ['---', f'title: {folder.name}', '---']

    body = lines[i:]
    idx = [j for j,l in enumerate(body) if l.startswith('## ')]
    if not idx:
        body = [headers[k] for k in order]
        idx = [j for j,l in enumerate(body) if l.startswith('## ')]
    idx.append(len(body))
    sections = {k:[] for k in order}
    for j in range(len(idx)-1):
        s,e = idx[j], idx[j+1]
        k = sec_key(body[s])
        if k:
            content = body[s+1:e]
            while content and content[0]=='': content = content[1:]
            while content and content[-1]=='': content = content[:-1]
            sections[k] = content

    official_embed = f"![[{folder.name}.m4a]]"
    official_title = f"- **{folder.name}**"

    # remove any existing block with official embed
    audio = sections.get('audio', [])
    cleaned = []
    skip_next = False
    for line in audio:
        if official_embed in line:
            skip_next = False
            continue
        if line.strip() == official_title:
            skip_next = True
            continue
        if skip_next and line.strip().startswith('![['):
            skip_next = False
            continue
        cleaned.append(line)

    # prepend official block
    new_audio = [official_title, f'  {official_embed}', ''] + cleaned
    # trim repeated blanks
    compact = []
    for l in new_audio:
        if l == '' and compact and compact[-1] == '':
            continue
        compact.append(l)
    sections['audio'] = compact

    out = list(front) + ['']
    for k in order:
        out.append(headers[k]); out.append('')
        out.extend(sections.get(k, [])); out.append('')
    new_txt = '\n'.join(out).rstrip() + '\n'
    if new_txt != txt:
        md.write_text(new_txt)
        md_updated.append(str(md))

# final report
report = {
    'download_candidates_seen': len(candidates),
    'matched_to_song_folder': len(matched),
    'unmatched_count': len(unmatched),
    'converted_count': len(converted),
    'moved_to_canonical_count': len(moved),
    'trashed_count': len(trashed),
    'md_updated_count': len(md_updated),
    'unmatched': unmatched[:200],
    'errors': errors[:200],
}

out = Path('/Users/ryantaylorvegh/.openclaw/workspace/distrokid_remaining_full_process_result.json')
out.write_text(json.dumps(report, indent=2))
print(out)
print(json.dumps({k:report[k] for k in ['download_candidates_seen','matched_to_song_folder','unmatched_count','converted_count','moved_to_canonical_count','md_updated_count']}))
