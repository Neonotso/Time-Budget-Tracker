from pathlib import Path
import re, shutil, subprocess, json

ROOT = Path('/Users/ryantaylorvegh/Library/CloudStorage/Dropbox/My Songs')
DOWNLOADS = Path.home() / 'Downloads'
TRASH = Path.home() / '.Trash' / 'OpenClaw-DistroKid-Processing'
TRASH.mkdir(parents=True, exist_ok=True)

pat = re.compile(r'^(\d{1,2})([^/]*)?(?:\s*\(\d+\))?\.(aif|aiff|wav|flac|mp3|m4a)$', re.I)

def norm(s: str) -> str:
    s = s.lower().replace('’', "'")
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    s = s.replace('_', ' ').replace('-', ' ')
    s = re.sub(r'\d+', ' ', s)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def pretty(stem: str) -> str:
    s = re.sub(r'^\d{1,2}', '', stem)
    s = re.sub(r'\(\d+\)$', '', s).strip()
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    s = s.replace('_', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# index all dirs (not just top-level), skip utility internals
all_dirs = [d for d in ROOT.rglob('*') if d.is_dir() and not d.name.startswith('.') and '_md_archive' not in d.parts and d.suffix.lower()!='.pages']

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
    cands.append((int(m.group(1)), pretty(f.stem), f))

moved=[]
unmatched=[]
for n,title,f in cands:
    key=norm(title)
    choices = idx.get(key, [])
    target=None
    if len(choices)==1:
        target=choices[0]
    elif len(choices)>1:
        # prefer shallowest path
        target=sorted(choices,key=lambda p:len(p.parts))[0]
    else:
        # containment fallback
        near=[d for d in all_dirs if key and (key in norm(d.name) or norm(d.name) in key)]
        if len(near)==1:
            target=near[0]
    if not target:
        unmatched.append({'file':f.name,'title':title})
        continue

    canonical = target / f"{target.name}.m4a"
    src=f
    if f.suffix.lower() != '.m4a':
        tmp=target / f"{target.name}.__tmp__.m4a"
        r=subprocess.run(['ffmpeg','-y','-i',str(f),'-c:a','aac','-b:a','256k',str(tmp)],capture_output=True,text=True)
        if r.returncode!=0:
            unmatched.append({'file':f.name,'title':title,'error':'ffmpeg_failed'})
            continue
        src=tmp

    if canonical.exists():
        backup = target / f"{target.name} (pre-DistroKid).m4a"
        if not backup.exists():
            shutil.move(str(canonical), str(backup))
        else:
            backup2 = target / f"{target.name} (pre-DistroKid 2).m4a"
            shutil.move(str(canonical), str(backup2))

    shutil.move(str(src), str(canonical))
    moved.append({'from':f.name,'to':str(canonical)})

    if f.exists():
        t=TRASH/f.name
        if t.exists(): t=TRASH/f"{f.stem}-orig{f.suffix}"
        shutil.move(str(f),str(t))

out={'download_candidates_seen':len(cands),'moved_to_canonical_count':len(moved),'unmatched_count':len(unmatched),'moved':moved,'unmatched':unmatched}
outp=Path('/Users/ryantaylorvegh/.openclaw/workspace/distrokid_remaining_full_process_result_v2.json')
outp.write_text(json.dumps(out,indent=2))
print(outp)
print(json.dumps({'seen':len(cands),'moved':len(moved),'unmatched':len(unmatched)}))