from pathlib import Path
import re

root = Path('/Users/ryantaylorvegh/Library/CloudStorage/Dropbox/My Songs')
updated = 0

title_re = re.compile(r'^(\s*)- \*\*(.*?)\*\*\s*$')
embed_re = re.compile(r'!\[\[([^\]]+\.(?:aif|aiff|wav|flac|mp3|m4a|mov|mp4|m4v))\]\]', re.I)

for md in root.rglob('*.md'):
    if '_md_archive' in md.parts or md.name.startswith('.'):
        continue
    if md.name != md.parent.name + '.md':
        continue

    lines = md.read_text(errors='ignore').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    changed = False

    for i in range(len(lines) - 1):
        m_title = title_re.match(lines[i])
        m_embed = embed_re.search(lines[i + 1])
        if not (m_title and m_embed):
            continue
        stem = Path(m_embed.group(1)).stem.replace('_', ' ')
        new_line = f"{m_title.group(1)}- **{stem}**"
        if lines[i] != new_line:
            lines[i] = new_line
            changed = True

    if changed:
        md.write_text('\n'.join(lines).rstrip() + '\n')
        updated += 1

print(updated)
