from pathlib import Path
import re

root = Path('/Users/ryantaylorvegh/Library/CloudStorage/Dropbox/My Songs')

section_header_re = re.compile(r'^##\s+🎧\s+Audio\s*&\s*Media\s*$')
next_header_re = re.compile(r'^##\s+')
embed_re = re.compile(r'!\[\[([^\]]+)\]\]')

def is_official(folder: Path, embed_name: str) -> bool:
    return embed_name.strip() == f"{folder.name}.m4a"

updated = 0

for md in root.rglob('*.md'):
    if '_md_archive' in md.parts or md.name.startswith('.'):
        continue
    if md.name != f"{md.parent.name}.md":
        continue

    text = md.read_text(errors='ignore').replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')

    start = None
    end = None
    for i, line in enumerate(lines):
        if section_header_re.match(line):
            start = i
            break
    if start is None:
        continue

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if next_header_re.match(lines[i]):
            end = i
            break

    section = lines[start:end]

    # Parse audio blocks: title line + optional embed line + following blank lines
    blocks = []
    i = 1  # skip section header
    while i < len(section):
        line = section[i]
        if line.strip().startswith('- **'):
            block = [line]
            i += 1
            while i < len(section) and (section[i].startswith('  ![[') or section[i].strip() == ''):
                block.append(section[i])
                i += 1
            blocks.append(block)
        else:
            i += 1

    if not blocks:
        continue

    official_blocks = []
    other_blocks = []

    for b in blocks:
        embed_name = None
        for line in b:
            m = embed_re.search(line)
            if m:
                embed_name = m.group(1)
                break
        if embed_name and is_official(md.parent, embed_name):
            official_blocks.append(b)
        else:
            other_blocks.append(b)

    reordered = official_blocks + other_blocks

    # Rebuild section with one blank line between blocks
    new_section = [section[0], '']
    for idx, b in enumerate(reordered):
        # trim trailing blanks inside block
        while b and b[-1].strip() == '':
            b = b[:-1]
        new_section.extend(b)
        new_section.append('')

    # Keep any non-block content lines from original section (rare) by appending if not duplicate
    # (Skip for now to keep deterministic formatting)

    new_lines = lines[:start] + new_section + lines[end:]
    new_text = '\n'.join(new_lines).rstrip() + '\n'

    if new_text != text:
        md.write_text(new_text)
        updated += 1

print(updated)
