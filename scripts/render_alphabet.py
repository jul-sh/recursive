#!/usr/bin/env python3
"""Render full alphabet comparison images across Linear, SemiCasual, Casual variants.

Applies OpenType feature substitutions: ss03, ss04, ss05, ss06, ss08, ss12, liga.
"""

import os
import sys
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import ufoLib2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UFO_ROOT = os.path.join(ROOT, "src", "ufo")
OUT_DIR = os.path.join(ROOT, "proofs")

SCALE = 0.12  # scale factor for rendering
GLYPH_GAP = 8  # extra pixels between glyphs to prevent M/N joining
GLYPH_ADVANCE = 500 * SCALE + GLYPH_GAP  # each glyph cell width
CAP_HEIGHT = 700
LINE_HEIGHT = (CAP_HEIGHT + 300) * SCALE  # room for ascenders/descenders

UPPERCASE = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LOWERCASE = list("abcdefghijklmnopqrstuvwxyz")
DIGITS = list("0123456789")
PUNCT = ["at", "fi"]  # @ and fi ligature
ROWS = [UPPERCASE, LOWERCASE, DIGITS, PUNCT]
ROW_LABELS = ["Uppercase", "Lowercase", "Digits", "Punct/Liga"]

# OpenType feature substitutions (ss03, ss04, ss05, ss06, ss08, ss12, liga)
# Maps: original glyph name -> alternate glyph name
FEATURE_SUBS = {
    # ss03: simplified f
    "f": "f.simple",
    # ss04: simplified i
    "i": "i.simple",
    # ss05: simplified l
    "l": "l.simple",
    # ss06: simplified r
    "r": "r.simple",
    # ss08: no-serif L and Z
    "L": "L.sans",
    "Z": "Z.sans",
    # ss12: simplified @
    "at": "at.alt",
}


def apply_features(glyph_name, font):
    """Apply feature substitutions if alternate glyph exists in font."""
    alt = FEATURE_SUBS.get(glyph_name)
    if alt and alt in font:
        return alt
    return glyph_name


def glyph_to_svg_path(glyph, font, scale, x_offset, y_offset):
    """Convert a glyph to SVG path data with transform."""
    pen = SVGPathPen(font)
    tpen = TransformPen(pen, (scale, 0, 0, -scale, x_offset, y_offset))
    glyph.draw(tpen)
    return pen.getCommands()


def render_alphabet_svg(family, weight, slant, variants):
    """Render alphabet comparison for one weight/slant combination."""
    slant_label = "Slanted" if slant else "Upright"
    fam_cap = "Mono" if family == "mono" else "Sans"

    # Load fonts
    fonts = {}
    for variant in variants:
        slant_suffix = " Slanted" if slant else ""
        ufo_name = f"Recursive {fam_cap}-{variant} {weight}{slant_suffix}.ufo"
        ufo_path = os.path.join(UFO_ROOT, family, ufo_name)
        if os.path.exists(ufo_path):
            fonts[variant] = ufoLib2.Font.open(ufo_path)

    if not fonts:
        return None

    num_variants = len(fonts)
    variant_names = list(fonts.keys())

    # Layout
    chars_per_row = 26  # max characters in a row
    label_width = 90
    margin = 20
    variant_block_height = LINE_HEIGHT * len(ROWS) + 30  # rows + label space
    total_width = label_width + chars_per_row * GLYPH_ADVANCE + margin * 2
    total_height = margin + num_variants * variant_block_height + margin

    svg_parts = []

    # Features label
    features_label = "ss03 ss04 ss05 ss06 ss08 ss12 liga"
    title = f"{fam_cap} {weight} {slant_label}  [{features_label}]"
    svg_parts.append(
        f'<text x="{total_width/2}" y="{margin}" text-anchor="middle" '
        f'font-size="14" font-family="sans-serif" font-weight="bold" fill="#333">{title}</text>'
    )

    for vi, variant in enumerate(variant_names):
        font = fonts[variant]
        block_y = margin + 10 + vi * variant_block_height

        # Variant label
        svg_parts.append(
            f'<text x="{margin}" y="{block_y + 14}" '
            f'font-size="11" font-family="sans-serif" font-weight="bold" fill="#555">{variant}</text>'
        )

        for ri, (row_chars, row_label) in enumerate(zip(ROWS, ROW_LABELS)):
            row_y = block_y + 20 + ri * LINE_HEIGHT

            for ci, char in enumerate(row_chars):
                # char can be a single character or a glyph name (e.g., "at", "fi")
                if len(char) == 1:
                    glyph_name = char
                else:
                    glyph_name = char  # already a glyph name

                # Apply feature substitutions
                glyph_name = apply_features(glyph_name, font)

                if glyph_name not in font:
                    continue

                glyph = font[glyph_name]
                x = label_width + ci * GLYPH_ADVANCE
                # baseline position: offset from top to account for cap height
                baseline_y = row_y + CAP_HEIGHT * SCALE

                path_d = glyph_to_svg_path(glyph, font, SCALE, x, baseline_y)
                if path_d:
                    svg_parts.append(
                        f'<path d="{path_d}" fill="#1a1a1a"/>'
                    )

        # Separator line
        if vi < num_variants - 1:
            sep_y = block_y + variant_block_height - 8
            svg_parts.append(
                f'<line x1="{margin}" y1="{sep_y}" x2="{total_width - margin}" y2="{sep_y}" '
                f'stroke="#ddd" stroke-width="0.5"/>'
            )

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{total_height}"
     viewBox="0 0 {total_width} {total_height}">
<rect width="100%" height="100%" fill="white"/>
{"".join(svg_parts)}
</svg>'''

    return svg, total_width, total_height


def render_closeup_svg(family, weight, slant, variants, chars, label):
    """Render close-up of specific characters.

    chars: list of (display_label, glyph_name) tuples
    """
    slant_label = "Slanted" if slant else "Upright"
    fam_cap = "Mono" if family == "mono" else "Sans"

    close_scale = 0.35
    glyph_w = 500 * close_scale
    cap_h = 700

    fonts = {}
    for variant in variants:
        slant_suffix = " Slanted" if slant else ""
        ufo_name = f"Recursive {fam_cap}-{variant} {weight}{slant_suffix}.ufo"
        ufo_path = os.path.join(UFO_ROOT, family, ufo_name)
        if os.path.exists(ufo_path):
            fonts[variant] = ufoLib2.Font.open(ufo_path)

    if not fonts:
        return None

    variant_names = list(fonts.keys())
    num_variants = len(variant_names)

    margin = 20
    label_w = 100
    row_h = (cap_h + 250) * close_scale
    total_width = label_w + len(chars) * glyph_w + margin * 2
    total_height = margin + 20 + num_variants * row_h + margin

    svg_parts = []

    # Title
    title = f"{fam_cap} {weight} {slant_label} — {label}"
    svg_parts.append(
        f'<text x="{total_width/2}" y="{margin + 10}" text-anchor="middle" '
        f'font-size="14" font-family="sans-serif" font-weight="bold" fill="#333">{title}</text>'
    )

    # Column headers
    for ci, (display, gname) in enumerate(chars):
        x = label_w + ci * glyph_w + glyph_w / 2
        svg_parts.append(
            f'<text x="{x}" y="{margin + 28}" text-anchor="middle" '
            f'font-size="10" font-family="sans-serif" fill="#999">{display}</text>'
        )

    for vi, variant in enumerate(variant_names):
        font = fonts[variant]
        row_y = margin + 35 + vi * row_h

        # Label
        svg_parts.append(
            f'<text x="{margin}" y="{row_y + row_h/2}" '
            f'font-size="11" font-family="sans-serif" font-weight="bold" fill="#555">{variant}</text>'
        )

        for ci, (display, glyph_name) in enumerate(chars):
            # Apply feature substitutions
            resolved = apply_features(glyph_name, font)
            if resolved not in font:
                continue
            glyph = font[resolved]
            x = label_w + ci * glyph_w
            baseline_y = row_y + cap_h * close_scale

            path_d = glyph_to_svg_path(glyph, font, close_scale, x, baseline_y)
            if path_d:
                svg_parts.append(f'<path d="{path_d}" fill="#1a1a1a"/>')

        # Separator
        if vi < num_variants - 1:
            sep_y = row_y + row_h - 5
            svg_parts.append(
                f'<line x1="{margin}" y1="{sep_y}" x2="{total_width - margin}" y2="{sep_y}" '
                f'stroke="#eee" stroke-width="0.5"/>'
            )

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{total_height}"
     viewBox="0 0 {total_width} {total_height}">
<rect width="100%" height="100%" fill="white"/>
{"".join(svg_parts)}
</svg>'''

    return svg, total_width, total_height


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    variants = ["Linear", "SemiCasual", "Casual"]

    # Close-up characters: (display_label, glyph_name)
    key_glyphs = [
        ("J", "J"), ("S", "S"), ("L", "L"), ("Z", "Z"),
        ("f", "f"), ("i", "i"), ("l", "l"), ("r", "r"),
        ("@", "at"), ("fi", "fi"),
    ]

    count = 0
    for family in ["mono", "sans"]:
        for weight in ["A", "B", "C"]:
            for slant in [False, True]:
                slant_label = "slanted" if slant else "upright"
                fam_cap = "Mono" if family == "mono" else "Sans"

                # Full alphabet
                result = render_alphabet_svg(family, weight, slant, variants)
                if result:
                    svg, w, h = result
                    filename = f"alphabet_{family}_{weight}_{slant_label}.svg"
                    filepath = os.path.join(OUT_DIR, filename)
                    with open(filepath, 'w') as f:
                        f.write(svg)
                    print(f"  {filename} ({w:.0f}x{h:.0f})")
                    count += 1

                # Close-up of key glyphs (feature alternates)
                result = render_closeup_svg(
                    family, weight, slant, variants,
                    key_glyphs,
                    "Key glyphs + features"
                )
                if result:
                    svg, w, h = result
                    filename = f"closeup_{family}_{weight}_{slant_label}.svg"
                    filepath = os.path.join(OUT_DIR, filename)
                    with open(filepath, 'w') as f:
                        f.write(svg)
                    print(f"  {filename} ({w:.0f}x{h:.0f})")
                    count += 1

    print(f"\nDone! Generated {count} proof images in {OUT_DIR}/")


if __name__ == '__main__':
    main()
