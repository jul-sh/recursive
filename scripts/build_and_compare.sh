#!/bin/bash
# Fast build + comparison for inspection.
# Builds only the Casual Mono Regular static OTF, then generates comparison images.
#
# Usage: ./scripts/build_and_compare.sh
#
# This takes ~2-3 minutes vs ~10+ minutes for a full build.
# Output: fonts_inspect/ and comparison_output/

set -e
cd "$(dirname "$0")/.."

VERSION="1.089"
OUT_DIR="fonts_inspect"

echo "=== Preparing sources ==="
cd mastering
python3 build.py --files --version "$VERSION" -o "../$OUT_DIR"

echo ""
echo "=== Building Casual Mono Regular OTF only ==="
cd ..

# Find the Casual Regular instance UFO
INSTANCE_UFO=$(find mastering/build/static/CFF/RecursiveCharonMonoCasualStatic/Regular -name "*.ufo" 2>/dev/null | head -1)

if [ -z "$INSTANCE_UFO" ]; then
    echo "ERROR: Casual Regular instance UFO not found. Run full build first."
    exit 1
fi

mkdir -p "$OUT_DIR/Static_OTF"

# Apply mono substitution rules (designspace rules aren't applied for static instances)
echo "  Applying mono substitutions to $INSTANCE_UFO"
python3 scripts/apply_mono_subs.py "$INSTANCE_UFO"

# Build just the one OTF with makeotf
echo "  Building OTF from $INSTANCE_UFO"
makeotf -f "$INSTANCE_UFO" -o "$OUT_DIR/Static_OTF/RecursiveCharonMonoCslSt-Regular.otf" -r 2>/dev/null || \
    makeotf -f "$INSTANCE_UFO" -o "$OUT_DIR/Static_OTF/RecursiveCharonMonoCslSt-Regular.otf" 2>&1 | tail -3

echo ""
echo "=== Generating comparison images ==="
export RECURSIVE_FONT="$OUT_DIR/Static_OTF/RecursiveCharonMonoCslSt-Regular.otf"

python3 -c "
import os, sys
from PIL import Image, ImageDraw, ImageFont

RECURSIVE = os.environ['RECURSIVE_FONT']
OUT = 'comparison_output'
os.makedirs(OUT, exist_ok=True)

rec_label_font = ImageFont.truetype(RECURSIVE, 18)

# Closeup of problem characters
size = 200
chars = list('flij.:;!?') + ['…']
rec_font = ImageFont.truetype(RECURSIVE, size)
cell_w, cell_h = 250, 350
cols = len(chars)
img = Image.new('RGB', (40 + cols * cell_w, 80 + cell_h + 20), 'white')
draw = ImageDraw.Draw(img)
draw.text((20, 10), 'Recursive Charon Mono Casual — Closeup of key characters', font=rec_label_font, fill='gray')
for idx, char in enumerate(chars):
    cx = 40 + idx * cell_w
    cy = 50
    draw.rectangle([cx, cy, cx+cell_w-2, cy+cell_h-2], outline='#dddddd')
    bbox = rec_font.getbbox(char)
    char_x = cx + (cell_w - (bbox[2]-bbox[0]))//2 - bbox[0]
    draw.text((char_x, cy + cell_h - 80 - bbox[3]), char, font=rec_font, fill='#cc0000')
    draw.text((cx+4, cy+2), repr(char), font=rec_label_font, fill='gray')
img.save(f'{OUT}/04_closeup_problem_chars.png')
print(f'  Saved {OUT}/04_closeup_problem_chars.png')

# Full text specimen at 72pt
size = 72
rec_font = ImageFont.truetype(RECURSIVE, size)
texts = [
    'the quick brown fox jumps over the lazy dog',
    'THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG',
    'abcdefghijklmnopqrstuvwxyz 0123456789',
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789',
    'fijlt {}[]() @#\$%^&*',
    'AaBbCcDdEeFfGgHhIiJjKkLlMm',
    'NnOoPpQqRrSsTtUuVvWwXxYyZz',
]
width = 2400
height = 40 + len(texts) * (size + 12) + 20
img = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(img)
title_font = ImageFont.truetype(RECURSIVE, 20)
y = 20
draw.text((20, y), 'Recursive Charon Mono Casual — 72pt specimen', font=title_font, fill='gray')
y += 30
for text in texts:
    draw.text((20, y), text, font=rec_font, fill='black')
    h = rec_font.getbbox(text)[3] + 4
    y += max(h, size + 8)
img = img.crop((0, 0, width, y + 10))
img.save(f'{OUT}/01_text_comparison.png')
print(f'  Saved {OUT}/01_text_comparison.png')

# Character grid at 200pt
size = 200
rec_font = ImageFont.truetype(RECURSIVE, size)
chars = list('fligtrj?!abcde')
cell_w, cell_h = 300, 350
cols = 7
rows = 2
width = 40 + cols * cell_w
height = 60 + rows * cell_h
img = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(img)
draw.text((20, 10), 'Recursive Charon Mono Casual — Character grid', font=rec_label_font, fill='gray')
for idx, char in enumerate(chars):
    col = idx % cols
    row = idx // cols
    cx = 20 + col * cell_w
    cy = 40 + row * cell_h
    draw.rectangle([cx, cy, cx+cell_w-2, cy+cell_h-2], outline='#dddddd')
    baseline_y = cy + cell_h - 80
    bbox_r = rec_font.getbbox(char)
    if bbox_r:
        rx = cx + (cell_w - (bbox_r[2]-bbox_r[0]))//2 - bbox_r[0]
        draw.text((rx, baseline_y - bbox_r[3]), char, font=rec_font, fill=(200, 0, 0))
    draw.text((cx+4, cy+2), repr(char), font=rec_label_font, fill='gray')
img.save(f'{OUT}/06_overlay.png')
print(f'  Saved {OUT}/06_overlay.png')
"

echo ""
echo "=== Done ==="
echo "Font: $OUT_DIR/Static_OTF/RecursiveCharonMonoCslSt-Regular.otf"
echo "Images: comparison_output/"
