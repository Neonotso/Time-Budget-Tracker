from pathlib import Path
import re

root = Path('/Users/ryantaylorvegh/Library/CloudStorage/Dropbox/My Songs')
embed_re = re.compile(r'!\[\[([^\]]+)\]\]')

notes_with_official = 0
notes_total = 0

for md in root.rglob('*.md'):
    if '_md_archive' in md.parts or md.name.startswith('.'):
        continue
    if md.name != f"{md.parent.name}.md":
        continue
    notes_total += 1
    txt = md.read_text(errors='ignore')
    official = f"![[{md.parent.name}.m4a]]"
    if official in txt:
        notes_with_official += 1

print(notes_total)
print(notes_with_official)
