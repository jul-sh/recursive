#!/usr/bin/env python3
"""
Generate a closeup side-by-side comparison of specific characters
between Recursive Charon (SemiCasual) and Iosevka Charon.
"""

import os
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

RECURSIVE_FONT = os.path.join(PROJECT_ROOT, "fonts_1.088", "Static_OTF", "RecursiveCharonMonoSmCslSt-Regular.otf")
IOSEVKA_FONT = os.path.expanduser("~/Library/Fonts/IosevkaCharonMono-Regular.ttf")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "comparison_output")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    size = 200
    chars = list("flij.:;!?") + ["…"]

    rec_font = ImageFont.truetype(RECURSIVE_FONT, size)
    ios_font = ImageFont.truetype(IOSEVKA_FONT, size)

    cell_w = 250
    cell_h = 350
    cols = len(chars)
    img = Image.new("RGB", (40 + cols * cell_w, 80 + 2 * cell_h + 40), "white")
    draw = ImageDraw.Draw(img)

    label_font = ImageFont.truetype(IOSEVKA_FONT, 18)
    draw.text((20, 10), "TOP ROW: Recursive Charon SemiCasual  |  BOTTOM ROW: Iosevka Charon",
              font=label_font, fill="gray")

    for idx, char in enumerate(chars):
        cx = 40 + idx * cell_w

        # Recursive row
        cy = 60
        draw.rectangle([cx, cy, cx + cell_w - 2, cy + cell_h - 2], outline="#dddddd")
        bbox = rec_font.getbbox(char)
        char_x = cx + (cell_w - (bbox[2] - bbox[0])) // 2 - bbox[0]
        draw.text((char_x, cy + cell_h - 80 - bbox[3]), char, font=rec_font, fill="#cc0000")
        draw.text((cx + 4, cy + 2), f"RC: {repr(char)}", font=label_font, fill="gray")

        # Iosevka row
        cy2 = 60 + cell_h + 20
        draw.rectangle([cx, cy2, cx + cell_w - 2, cy2 + cell_h - 2], outline="#dddddd")
        bbox2 = ios_font.getbbox(char)
        char_x2 = cx + (cell_w - (bbox2[2] - bbox2[0])) // 2 - bbox2[0]
        draw.text((char_x2, cy2 + cell_h - 80 - bbox2[3]), char, font=ios_font, fill="#0000cc")
        draw.text((cx + 4, cy2 + 2), f"IC: {repr(char)}", font=label_font, fill="gray")

    output_path = os.path.join(OUTPUT_DIR, "04_closeup_problem_chars.png")
    img.save(output_path)
    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
