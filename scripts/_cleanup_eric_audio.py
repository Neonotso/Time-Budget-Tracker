from pathlib import Path
removed = []
for p in Path.home().joinpath('Downloads').glob('*Eric*'):
    if p.is_file() and p.suffix.lower() in {'.m4a', '.mp3', '.wav', '.aiff'}:
        p.unlink(missing_ok=True)
        removed.append(str(p))
print('REMOVED')
for r in removed:
    print(r)
print('COUNT', len(removed))
