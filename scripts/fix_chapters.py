#!/usr/bin/env python3
"""
Fix chapter headers properly - v2
"""
import re
import os

workspace_dir = '/Users/ryantaylorvegh/.openclaw/workspace'
input_file = os.path.join(workspace_dir, 'edited_book_final.txt')
output_file = os.path.join(workspace_dir, 'formatted_book_v2.txt')

with open(input_file, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Loaded {len(text)} characters")

# Fix chapter headers
# Pattern 1: "Chapter 1: 11 13pro" -> "Chapter 1"  
text = re.sub(r'Chapter (\d+):\s*\d+\s*\d*pro?\s*$', r'Chapter \1', text, flags=re.MULTILINE)

# Pattern 2: "Chapter 2:  9" -> "Chapter 2"
text = re.sub(r'Chapter (\d+):\s*\d+\s*$', r'Chapter \1', text, flags=re.MULTILINE)

# Pattern 3: "Chapter 2\nChapter 2" where there's duplicate - keep one
lines = text.split('\n')
fixed_lines = []
prev_line = None
for line in lines:
    stripped = line.strip()
    # If current line is "Chapter X" and previous was also "Chapter X", skip
    if prev_line and stripped == prev_line and stripped.startswith('Chapter'):
        continue
    fixed_lines.append(line)
    prev_line = stripped

text = '\n'.join(fixed_lines)

# Add paragraph spacing (triple newlines)
paragraphs = text.split('\n\n')
text = '\n\n\n'.join(paragraphs)

# Save
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Saved to {output_file}")
print(f"New length: {len(text)} chars")

# Check chapter headers
print("\n=== Chapter headers ===")
for line in text.split('\n'):
    if line.strip().startswith('Chapter'):
        print(repr(line.strip()[:40]))
