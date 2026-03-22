#!/usr/bin/env python3
"""Generate semi-casual UFO sources by interpolating between Linear and Casual at factor 0.5."""

import copy
import os
import shutil
import sys

from fontMath.mathGlyph import MathGlyph
from fontMath.mathInfo import MathInfo
from fontMath.mathKerning import MathKerning
import ufoLib2


FACTOR = 0.5

# Pairs: (linear_ufo, casual_ufo, output_semicasual_ufo)
PAIRS = []

for family in ["mono", "sans"]:
    family_cap = "Mono" if family == "mono" else "Sans"
    base = f"src/ufo/{family}"
    for weight in ["A", "B", "C"]:
        for slant_suffix in ["", " Slanted"]:
            linear = f"{base}/Recursive {family_cap}-Linear {weight}{slant_suffix}.ufo"
            casual = f"{base}/Recursive {family_cap}-Casual {weight}{slant_suffix}.ufo"
            semicasual = f"{base}/Recursive {family_cap}-SemiCasual {weight}{slant_suffix}.ufo"
            PAIRS.append((linear, casual, semicasual))


def interpolate_glyph(glyph_linear, glyph_casual, factor):
    """Interpolate between two glyphs using fontMath."""
    mg_linear = MathGlyph(glyph_linear)
    mg_casual = MathGlyph(glyph_casual)

    # Interpolate: linear + (casual - linear) * factor
    mg_result = mg_linear + (mg_casual - mg_linear) * factor
    return mg_result


def interpolate_value(a, b, factor):
    """Interpolate between two numeric values."""
    if a is None or b is None:
        return a if a is not None else b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * factor
    return a  # non-numeric, just return first


def generate_semicasual(linear_path, casual_path, output_path, root_dir):
    """Generate a semi-casual UFO by interpolating between linear and casual."""
    linear_abs = os.path.join(root_dir, linear_path)
    casual_abs = os.path.join(root_dir, casual_path)
    output_abs = os.path.join(root_dir, output_path)

    print(f"  Linear:  {linear_path}")
    print(f"  Casual:  {casual_path}")
    print(f"  Output:  {output_path}")

    font_linear = ufoLib2.Font.open(linear_abs)
    font_casual = ufoLib2.Font.open(casual_abs)

    # Start with a copy of the linear font as base
    font_out = ufoLib2.Font.open(linear_abs)

    # Interpolate font info
    info_linear = MathInfo(font_linear.info)
    info_casual = MathInfo(font_casual.info)
    info_result = info_linear + (info_casual - info_linear) * FACTOR
    info_result.extractInfo(font_out.info)

    # Update family/style name
    basename = os.path.basename(output_path).replace(".ufo", "")
    font_out.info.familyName = basename.split("-")[0].strip()
    font_out.info.styleName = basename.split("-")[1].strip() if "-" in basename else basename

    # Interpolate kerning
    if font_linear.kerning or font_casual.kerning:
        kern_linear = MathKerning(font_linear.kerning, font_linear.groups)
        kern_casual = MathKerning(font_casual.kerning, font_casual.groups)
        kern_result = kern_linear + (kern_casual - kern_linear) * FACTOR
        font_out.kerning.clear()
        # Extract kerning from MathKerning
        for pair, value in kern_result.items():
            font_out.kerning[pair] = value
        # Copy groups from linear (should be same)
        font_out.groups.clear()
        font_out.groups.update(font_linear.groups)

    # Interpolate glyphs
    glyph_names_linear = set(font_linear.keys())
    glyph_names_casual = set(font_casual.keys())
    common_glyphs = glyph_names_linear & glyph_names_casual

    interpolated = 0
    copied = 0
    errors = 0

    for glyph_name in sorted(font_out.keys()):
        if glyph_name in common_glyphs:
            glyph_l = font_linear[glyph_name]
            glyph_c = font_casual[glyph_name]

            try:
                mg_result = interpolate_glyph(glyph_l, glyph_c, FACTOR)

                # Clear the output glyph and draw the interpolated result
                out_glyph = font_out[glyph_name]
                out_glyph.clear()

                # Draw the interpolated glyph
                pen = out_glyph.getPen()
                mg_result.drawPoints(out_glyph.getPointPen())

                # Interpolate width
                out_glyph.width = round(glyph_l.width + (glyph_c.width - glyph_l.width) * FACTOR, 4)

                # Interpolate anchors
                out_glyph.anchors.clear()
                anchors_l = {a.name: a for a in glyph_l.anchors}
                anchors_c = {a.name: a for a in glyph_c.anchors}
                for anchor_name in anchors_l:
                    if anchor_name in anchors_c:
                        al = anchors_l[anchor_name]
                        ac = anchors_c[anchor_name]
                        x = round(al.x + (ac.x - al.x) * FACTOR, 4)
                        y = round(al.y + (ac.y - al.y) * FACTOR, 4)
                        out_glyph.anchors.append(ufoLib2.objects.Anchor(x=x, y=y, name=anchor_name))
                    else:
                        al = anchors_l[anchor_name]
                        out_glyph.anchors.append(ufoLib2.objects.Anchor(x=al.x, y=al.y, name=anchor_name))

                interpolated += 1
            except Exception as e:
                # If interpolation fails (incompatible outlines), keep linear version
                errors += 1
                if errors <= 10:
                    print(f"    Warning: Could not interpolate '{glyph_name}': {e}")
        else:
            copied += 1

    # Remove guidelines from glyphs (they're editor-specific and would have different IDs)
    for glyph_name in font_out.keys():
        glyph = font_out[glyph_name]
        glyph.guidelines.clear()

    # Save
    font_out.save(output_abs, overwrite=True)

    print(f"    Interpolated: {interpolated}, Kept from linear: {copied}, Errors: {errors}")
    return interpolated, copied, errors


def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Root directory: {root_dir}")
    print(f"Interpolation factor: {FACTOR}")
    print()

    total_interpolated = 0
    total_errors = 0

    for linear, casual, semicasual in PAIRS:
        print(f"\nGenerating: {os.path.basename(semicasual)}")
        interp, copied, errs = generate_semicasual(linear, casual, semicasual, root_dir)
        total_interpolated += interp
        total_errors += errs

    print(f"\n{'='*60}")
    print(f"Done! Generated {len(PAIRS)} semi-casual UFO sources.")
    print(f"Total glyphs interpolated: {total_interpolated}")
    if total_errors:
        print(f"Total interpolation errors: {total_errors}")


if __name__ == "__main__":
    main()
