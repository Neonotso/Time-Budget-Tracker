#!/usr/bin/env python3
"""
Comprehensive book editor - deeper fixes
"""
import re
import os

workspace_dir = '/Users/ryantaylorvegh/.openclaw/workspace'
input_file = os.path.join(workspace_dir, 'fixed_full_book.txt')
output_file = os.path.join(workspace_dir, 'edited_book_v2.txt')

# Read the book
with open(input_file, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Loaded {len(text)} characters")

# More comprehensive corrections
corrections = [
    # Apostrophes
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
    (r"\bdidint\b", "didn't"),
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
    (r"\blets\b", "let's"),
    (r"\baint\b", "ain't"),
    (r"\bweren't\b", "weren't"),
    (r"\bShes\b", "She's"),
    (r"\bHes\b", "He's"),
    (r"\bIts\b", "It's"),
    (r"\bDont\b", "Don't"),
    (r"\bWont\b", "Won't"),
    (r"\bCant\b", "Can't"),
    
    # "i" lowercase fixes
    (r"\bi would\b", "I would"),
    (r"\bi could\b", "I could"),
    (r"\bi have\b", "I have"),
    (r"\bi had\b", "I had"),
    (r"\bi am\b", "I am"),
    (r"\bi was\b", "I was"),
    (r"\bi will\b", "I will"),
    (r"\bi dont\b", "I don't"),
    (r"\bi can't\b", "I can't"),
    (r"\bi've\b", "I've"),
    (r"\bi'll\b", "I'll"),
    (r"\bi'd\b", "I'd"),
    
    # Specific fixes found in the text
    (r"we'll then", "Well then"),
    (r"We'll then", "Well then"),
    (r"couldent", "couldn't"),
    (r"couldent", "couldn't"),
    (r"couldent", "couldn't"),
    (r"Ston said", "Stone said"),
    (r"it's breathing", "its breathing"),  # actually "it's" might be correct here
    (r"it's shape", "its shape"),
    (r"it's breath", "its breath"),
    (r"it 's", "it's"),
    (r"\bi would\b", "I would"),
    (r"\bi would", "I would"),
    
    # Double words
    (r"\bthe the\b", "the"),
    (r"\band and\b", "and"),
    (r"\bto to\b", "to"),
    (r"\bof of\b", "of"),
    (r"\bis is\b", "is"),
    (r"\bwas was\b", "was"),
    (r"\bthat that\b", "that"),
    
    # Spaces
    (r"\s+([.,!?])", r"\1"),
    (r"  +", " "),
    
    # Common misspellings
    (r"\brecieve\b", "receive"),
    (r"\bdefinately\b", "definitely"),
    (r"\boccured\b", "occurred"),
    (r"\bseperate\b", "separate"),
    (r"\bthier\b", "their"),
    (r"\bwierd\b", "weird"),
    (r"\baccomodate\b", "accommodate"),
    (r"\bbegining\b", "beginning"),
    (r"\benviroment\b", "environment"),
    (r"\bhappend\b", "happened"),
    (r"\bintresting\b", "interesting"),
    (r"\bknowlege\b", "knowledge"),
    (r"\blittel\b", "little"),
    (r"\bneccessary\b", "necessary"),
    (r"\bnoticable\b", "noticeable"),
    (r"\bpersistant\b", "persistent"),
    (r"\bposession\b", "possession"),
    (r"\bprefered\b", "preferred"),
    (r"\brealy\b", "really"),
    (r"\brecomend\b", "recommend"),
    (r"\bspecialy\b", "especially"),
    (r"\bstruggel\b", "struggle"),
    (r"\bsuprise\b", "surprise"),
    (r"\btruely\b", "truly"),
    (r"\buntill\b", "until"),
    (r"\bwritting\b", "writing"),
    
    # Paragraph fixes
    (r"\n\n\n+", "\n\n"),
]

# Apply corrections multiple times for nested fixes
for _ in range(3):
    for pattern, replacement in corrections:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

# Save
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Saved to {output_file}")
print(f"New length: {len(text)} chars")

# Count chapters
chapters = re.findall(r'^Chapter (\d+)', text, re.MULTILINE)
unique_chapters = sorted(set(int(c) for c in chapters), key=lambda x: (x < 20, x))
print(f"Chapters found: {unique_chapters}")
