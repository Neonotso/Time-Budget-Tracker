from pathlib import Path
import re, subprocess, shutil, json

root=Path('/Users/ryantaylorvegh/Library/CloudStorage/Dropbox/My Songs')
trash=Path.home()/'.Trash'/'OpenClaw-AIF-Originals'
trash.mkdir(parents=True, exist_ok=True)

pat=re.compile(r'^(\d{1,2}).*\.(aif|aiff)$',re.I)
conversions=[]
skipped=[]
errors=[]
rename_map={}

for d in [p for p in root.rglob('*') if p.is_dir() and not p.name.startswith('.') and '_md_archive' not in p.parts]:
    files=[f for f in d.iterdir() if f.is_file() and pat.match(f.name)]
    if not files:
        continue
    files=sorted(files, key=lambda p:p.stat().st_mtime, reverse=True)
    src=files[0]
    target=d/(d.name + '.m4a')
    try:
        if target.exists():
            skipped.append({'folder':str(d.relative_to(root)), 'src':src.name, 'reason':'target_exists', 'target':target.name})
            rename_map.setdefault(str(d),{})[src.name]=target.name
            td=trash/src.name
            if td.exists(): td=trash/f"{src.stem}-dup{src.suffix}"
            shutil.move(str(src), str(td))
            continue

        cmd=['ffmpeg','-y','-i',str(src),'-c:a','aac','-b:a','256k',str(target)]
        r=subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode!=0:
            errors.append({'folder':str(d.relative_to(root)),'src':src.name,'error':r.stderr[-400:]})
            continue

        rename_map.setdefault(str(d),{})[src.name]=target.name
        conversions.append({'folder':str(d.relative_to(root)),'from':src.name,'to':target.name})
        for f in files:
            td=trash/f.name
            if td.exists(): td=trash/f"{f.stem}-orig{f.suffix}"
            shutil.move(str(f), str(td))
    except Exception as e:
        errors.append({'folder':str(d.relative_to(root)),'src':src.name,'error':str(e)})

md_updated=[]
for md in root.rglob('*.md'):
    if '_md_archive' in md.parts or md.name.startswith('.'):
        continue
    if md.name != md.parent.name + '.md':
        continue
    fmap=rename_map.get(str(md.parent))
    if not fmap:
        continue
    txt=md.read_text(errors='ignore')
    new=txt
    for old,newname in fmap.items():
        new=new.replace(f'![[{old}]]', f'![[{newname}]]')
        new=new.replace(f'[[{old}]]', f'[[{newname}]]')
        new=new.replace(old, newname)
    if new!=txt:
        md.write_text(new)
        md_updated.append(str(md.relative_to(root)))

out={
  'converted_count':len(conversions),
  'md_updated_count':len(md_updated),
  'skipped_count':len(skipped),
  'errors_count':len(errors),
  'converted':conversions,
  'skipped':skipped,
  'md_updated':md_updated,
  'errors':errors,
  'trash_root':str(trash)
}
outp=Path('/Users/ryantaylorvegh/.openclaw/workspace/song_audio_convert_and_rename_result.json')
outp.write_text(json.dumps(out, indent=2))
print(outp)
print(json.dumps({'converted_count':len(conversions),'md_updated_count':len(md_updated),'skipped_count':len(skipped),'errors_count':len(errors)}))