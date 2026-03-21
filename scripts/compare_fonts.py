#!/usr/bin/env python3
"""
Side-by-side comparison of Recursive Charon (SemiCasual) vs Iosevka Charon.

Renders sample text in both fonts at multiple sizes, with per-glyph
comparisons for characters likely affected by vertical clipping.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

# Paths
RECURSIVE_FONT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fonts_1.088", "Static_OTF", "RecursiveCharonMonoSmCslSt-Regular.otf"
)
IOSEVKA_FONT = os.path.expanduser("~/Library/Fonts/IosevkaCharonMono-Regular.ttf")

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "comparison_output")


def render_text_block(draw, font, text, x, y, fill="black"):
    """Render text and return the bounding box height used."""
    draw.text((x, y), text, font=font, fill=fill)
    bbox = font.getbbox(text)
    return bbox[3] - bbox[1]


def create_comparison():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    size = 72

    # === PAGE 1: Full text comparison ===
    title_font = ImageFont.truetype(IOSEVKA_FONT, 20)

    sample_texts = [
        "the quick brown fox jumps over the lazy dog",
        "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
        "abcdefghijklmnopqrstuvwxyz 0123456789",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789",
        "fijlt {}[]() @#$%^&*",
        "AaBbCcDdEeFfGgHhIiJjKkLlMm",
        "NnOoPpQqRrSsTtUuVvWwXxYyZz",
    ]

    rec_font = ImageFont.truetype(RECURSIVE_FONT, size)
    ios_font = ImageFont.truetype(IOSEVKA_FONT, size)

    width = 2400
    height = 40 + len(sample_texts) * (size + 8 + size + 8 + 4) + 20
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    y = 20
    draw.text((20, y), "RECURSIVE CHARON (SemiCasual) vs IOSEVKA CHARON — 72pt", font=title_font, fill="gray")
    y += 30

    for text in sample_texts:
        draw.text((20, y), "RC:", font=title_font, fill="#cc0000")
        draw.text((60, y), text, font=rec_font, fill="black")
        h1 = rec_font.getbbox(text)[3] + 4
        y += max(h1, size + 8)

        draw.text((20, y), "IC:", font=title_font, fill="#0000cc")
        draw.text((60, y), text, font=ios_font, fill="black")
        h2 = ios_font.getbbox(text)[3] + 4
        y += max(h2, size + 8)

        y += 4  # gap between pairs

    img = img.crop((0, 0, width, y + 10))
    img.save(os.path.join(OUTPUT_DIR, "01_text_comparison.png"))
    print(f"Saved 01_text_comparison.png")

    # === PAGE 2: Per-glyph comparison for problem characters ===
    # Characters likely affected by vertical clipping
    problem_chars = list("fijltbdghklABCDEFGHIJKLMNOPQRSTUVWXYZ{}[]()@#$^")
    glyph_size = 96
    cell_w = 120
    cell_h = 200
    cols = 12
    rows = (len(problem_chars) + cols - 1) // cols

    img2_w = 40 + cols * cell_w + 40
    img2_h = 80 + rows * cell_h + 40
    img2 = Image.new("RGB", (img2_w, img2_h), "white")
    draw2 = ImageDraw.Draw(img2)

    rec_font = ImageFont.truetype(RECURSIVE_FONT, glyph_size)
    ios_font = ImageFont.truetype(IOSEVKA_FONT, glyph_size)

    draw2.text((20, 10), "Per-glyph: RED = Recursive Charon SemiCasual, BLUE = Iosevka Charon (overlaid)", font=title_font, fill="gray")
    draw2.text((20, 35), "Differences in vertical extent indicate clipping issues", font=title_font, fill="gray")

    for idx, char in enumerate(problem_chars):
        col = idx % cols
        row = idx // cols
        cx = 40 + col * cell_w
        cy = 80 + row * cell_h

        # Draw cell border
        draw2.rectangle([cx, cy, cx + cell_w - 2, cy + cell_h - 2], outline="#dddddd")

        # Render both glyphs overlaid
        # Center each glyph in the cell
        rec_bbox = rec_font.getbbox(char)
        ios_bbox = ios_font.getbbox(char)

        # Position: center horizontally, align baseline
        rec_x = cx + (cell_w - (rec_bbox[2] - rec_bbox[0])) // 2 - rec_bbox[0]
        ios_x = cx + (cell_w - (ios_bbox[2] - ios_bbox[0])) // 2 - ios_bbox[0]

        baseline_y = cy + cell_h - 50

        # Draw Iosevka first (blue, behind)
        draw2.text((ios_x, baseline_y - ios_bbox[3]), char, font=ios_font, fill=(0, 0, 200, 180))
        # Draw Recursive on top (red)
        draw2.text((rec_x, baseline_y - rec_bbox[3]), char, font=rec_font, fill=(200, 0, 0, 180))

        # Label
        label_font = ImageFont.truetype(IOSEVKA_FONT, 14)
        draw2.text((cx + 4, cy + 2), char, font=label_font, fill="gray")

    img2.save(os.path.join(OUTPUT_DIR, "02_glyph_overlay.png"))
    print(f"Saved 02_glyph_overlay.png")

    # === PAGE 3: Metrics comparison ===
    rec_tt = TTFont(RECURSIVE_FONT)
    ios_tt = TTFont(IOSEVKA_FONT)

    img3 = Image.new("RGB", (1200, 900), "white")
    draw3 = ImageDraw.Draw(img3)
    mono_font = ImageFont.truetype(IOSEVKA_FONT, 18)

    draw3.text((20, 10), "Font Metrics Comparison", font=title_font, fill="gray")

    y = 50
    header = f"{'Metric':<40} {'Recursive Charon':<20} {'Iosevka Charon':<20} {'Diff':<10}"
    draw3.text((20, y), header, font=mono_font, fill="black")
    y += 30
    draw3.line([(20, y), (1100, y)], fill="gray")
    y += 10

    metrics = []

    # OS/2 table
    rec_os2 = rec_tt["OS/2"]
    ios_os2 = ios_tt["OS/2"]
    metrics.append(("OS/2 sTypoAscender", rec_os2.sTypoAscender, ios_os2.sTypoAscender))
    metrics.append(("OS/2 sTypoDescender", rec_os2.sTypoDescender, ios_os2.sTypoDescender))
    metrics.append(("OS/2 usWinAscent", rec_os2.usWinAscent, ios_os2.usWinAscent))
    metrics.append(("OS/2 usWinDescent", rec_os2.usWinDescent, ios_os2.usWinDescent))
    metrics.append(("OS/2 sxHeight", rec_os2.sxHeight, ios_os2.sxHeight))
    metrics.append(("OS/2 sCapHeight", rec_os2.sCapHeight, ios_os2.sCapHeight))
    metrics.append(("OS/2 yStrikeoutPosition", rec_os2.yStrikeoutPosition, ios_os2.yStrikeoutPosition))
    metrics.append(("OS/2 yStrikeoutSize", rec_os2.yStrikeoutSize, ios_os2.yStrikeoutSize))

    # hhea table
    rec_hhea = rec_tt["hhea"]
    ios_hhea = ios_tt["hhea"]
    metrics.append(("hhea ascent", rec_hhea.ascent, ios_hhea.ascent))
    metrics.append(("hhea descent", rec_hhea.descent, ios_hhea.descent))

    # head table
    rec_head = rec_tt["head"]
    ios_head = ios_tt["head"]
    metrics.append(("head unitsPerEm", rec_head.unitsPerEm, ios_head.unitsPerEm))
    metrics.append(("head yMin", rec_head.yMin, ios_head.yMin))
    metrics.append(("head yMax", rec_head.yMax, ios_head.yMax))
    metrics.append(("head xMin", rec_head.xMin, ios_head.xMin))
    metrics.append(("head xMax", rec_head.xMax, ios_head.xMax))

    # post table
    rec_post = rec_tt["post"]
    ios_post = ios_tt["post"]
    metrics.append(("post underlinePosition", rec_post.underlinePosition, ios_post.underlinePosition))
    metrics.append(("post underlineThickness", rec_post.underlineThickness, ios_post.underlineThickness))

    for name, rec_val, ios_val in metrics:
        diff = rec_val - ios_val
        color = "red" if abs(diff) > 20 else ("orange" if abs(diff) > 5 else "black")
        line = f"{name:<40} {str(rec_val):<20} {str(ios_val):<20} {diff:+d}"
        draw3.text((20, y), line, font=mono_font, fill=color)
        y += 25

    # === Glyph-level vertical extent comparison for key chars ===
    y += 30
    draw3.text((20, y), "Per-glyph vertical bounds (yMin, yMax) for key characters:", font=title_font, fill="gray")
    y += 30

    header2 = f"{'Char':<6} {'RC yMin':<10} {'RC yMax':<10} {'IC yMin':<10} {'IC yMax':<10} {'yMax diff':<10}"
    draw3.text((20, y), header2, font=mono_font, fill="black")
    y += 25
    draw3.line([(20, y), (700, y)], fill="gray")
    y += 10

    rec_glyf = rec_tt.getGlyphSet()
    ios_glyf = ios_tt.getGlyphSet()
    rec_cmap = rec_tt.getBestCmap()
    ios_cmap = ios_tt.getBestCmap()

    check_chars = "fijltbdhkl"
    for char in check_chars:
        rec_gname = rec_cmap.get(ord(char))
        ios_gname = ios_cmap.get(ord(char))
        if rec_gname and ios_gname:
            from fontTools.pens.boundsPen import BoundsPen

            rec_pen = BoundsPen(rec_glyf)
            rec_glyf[rec_gname].draw(rec_pen)
            rec_bounds = rec_pen.bounds

            ios_pen = BoundsPen(ios_glyf)
            ios_glyf[ios_gname].draw(ios_pen)
            ios_bounds = ios_pen.bounds

            if rec_bounds and ios_bounds:
                ymax_diff = round(rec_bounds[3]) - round(ios_bounds[3])
                color = "red" if abs(ymax_diff) > 20 else "black"
                line = f"  {char:<4} {round(rec_bounds[1]):<10} {round(rec_bounds[3]):<10} {round(ios_bounds[1]):<10} {round(ios_bounds[3]):<10} {ymax_diff:+d}"
                draw3.text((20, y), line, font=mono_font, fill=color)
                y += 22

    img3.save(os.path.join(OUTPUT_DIR, "03_metrics_comparison.png"))
    print(f"Saved 03_metrics_comparison.png")

    rec_tt.close()
    ios_tt.close()

    print(f"\nAll comparisons saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    create_comparison()
