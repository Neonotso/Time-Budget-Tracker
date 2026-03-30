#!/usr/bin/env python3
"""
Book spell/grammar editor - processes the fixed book and corrects errors
"""
import re
import os

workspace_dir = '/Users/ryantaylorvegh/.openclaw/workspace'
input_file = os.path.join(workspace_dir, 'fixed_full_book.txt')
output_file = os.path.join(workspace_dir, 'edited_book.txt')

# Read the book
with open(input_file, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Loaded {len(text)} characters")

# Common corrections - add more as we find them
corrections = [
    # Missing apostrophes
    (r"\bcant\b", "can't"),
    (r"\bwont\b", "won't"),
    (r"\bdont\b", "don't"),
    (r"\bdoesnt\b", "doesn't"),
    (r"\bisnt\b", "isn't"),
    (r"\bwasnt\b", "wasn't"),
    (r"\bwerent\b", "weren't"),
    (r"\bhasnt\b", "hasn't"),
    (r"\bhadnt\b", "hadn't"),
    (r"\bwouldnt\b", "wouldn't"),
    (r"\bcouldnt\b", "couldn't"),
    (r"\bshouldnt\b", "shouldn't"),
    (r"\bim\b", "I'm"),
    (r"\bive\b", "I've"),
    (r"\bid\b", "I'd"),
    (r"\bill\b", "I'll"),
    (r"\byoure\b", "you're"),
    (r"\byouve\b", "you've"),
    (r"\byoud\b", "you'd"),
    (r"\byoull\b", "you'll"),
    (r"\bhes\b", "he's"),
    (r"\bhed\b", "he'd"),
    (r"\bhell\b", "he'll"),
    (r"\bshes\b", "she's"),
    (r"\bshed\b", "she'd"),
    (r"\bshell\b", "she'll"),
    (r"\bits\b", "it's"),
    (r"\bitll\b", "it'll"),
    (r"\bweve\b", "we've"),
    (r"\bwed\b", "we'd"),
    (r"\bwell\b", "we'll"),
    (r"\btheyre\b", "they're"),
    (r"\btheyve\b", "they've"),
    (r"\btheyd\b", "they'd"),
    (r"\btheyll\b", "they'll"),
    (r"\bwhos\b", "who's"),
    (r"\bwhod\b", "who'd"),
    (r"\bwholl\b", "who'll"),
    (r"\bwhats\b", "what's"),
    (r"\bwhats\b", "what's"),
    (r"\blets\b", "let's"),
    
    # Contractions with not (didint -> didn't)
    (r"\bdidint\b", "didn't"),
    (r"\bcouldint\b", "couldn't"),
    (r"\bwouldint\b", "wouldn't"),
    (r"\bshouldint\b", "shouldn't"),
    
    # Common misspellings
    (r"\brecieve\b", "receive"),
    (r"\bdefinately\b", "definitely"),
    (r"\boccured\b", "occurred"),
    (r"\bseperate\b", "separate"),
    (r"\bthier\b", "their"),
    (r"\bwierd\b", "weird"),
    (r"\baccomodate\b", "accommodate"),
    (r"\bbegining\b", "beginning"),
    (r"\bbussiness\b", "business"),
    (r"\bconciousness\b", "consciousness"),
    (r"\bembarassed\b", "embarrassed"),
    (r"\benviroment\b", "environment"),
    (r"\bgoverment\b", "government"),
    (r"\bhappend\b", "happened"),
    (r"\bindependant\b", "independent"),
    (r"\bintresting\b", "interesting"),
    (r"\bknowlege\b", "knowledge"),
    (r"\blittel\b", "little"),
    (r"\bneccessary\b", "necessary"),
    (r"\bnoticable\b", "noticeable"),
    (r"\boccassion\b", "occasion"),
    (r"\boportunity\b", "opportunity"),
    (r"\bparalell\b", "parallel"),
    (r"\bpersistant\b", "persistent"),
    (r"\bposession\b", "possession"),
    (r"\bprefered\b", "preferred"),
    (r"\bprivelege\b", "privilege"),
    (r"\bpromiss\b", "promise"),
    (r"\brealy\b", "really"),
    (r"\brecomend\b", "recommend"),
    (r"\brefered\b", "referred"),
    (r"\brelevent\b", "relevant"),
    (r"\bresaurant\b", "restaurant"),
    (r"\bsence\b", "sense"),
    (r"\bsometing\b", "something"),
    (r"\bspecialy\b", "especially"),
    (r"\bstruggel\b", "struggle"),
    (r"\bsuprise\b", "surprise"),
    (r"\btommorow\b", "tomorrow"),
    (r"\btommorrow\b", "tomorrow"),
    (r"\btruely\b", "truly"),
    (r"\buntill\b", "until"),
    (r"\bwritting\b", "writing"),
    
    # Double words
    (r"\bthe the\b", "the"),
    (r"\band and\b", "and"),
    (r"\bto to\b", "to"),
    (r"\bof of\b", "of"),
    (r"\bis is\b", "is"),
    (r"\bwas was\b", "was"),
    
    # Spaces before punctuation
    (r"\s+([.,!?])", r"\1"),
    
    # Multiple spaces
    (r"  +", " "),
]

# Apply corrections
for pattern, replacement in corrections:
    text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

# Fix: space after paragraph
text = re.sub(r"\n\n+", "\n\n", text)

# Save edited version
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Saved edited version to {output_file}")
print(f"New length: {len(text)} characters")

# Count chapters up to 27
chapter_matches = re.findall(r'^Chapter (\d+)', text, re.MULTILINE)
chapters_found = [int(c) for c in chapter_matches]
print(f"Chapters found: {chapters_found[:30]}...")

# Find where Chapter 27 ends (or Chapter 1 repeats)
try:
    ch27_index = chapters_found.index(27)
    print(f"Chapter 27 is at index {ch27_index}")
except ValueError:
    print("Chapter 27 not found")
