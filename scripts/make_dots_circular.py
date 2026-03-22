#!/usr/bin/env python3
"""
Replace dotaccentcomb contours with circular dots across all masters.

The original dotaccentcomb is a wide flat oval. This script replaces it
with a near-circular shape, matching Iosevka Charon's round i/j dots.

Also makes period and ellipsis dots more circular.

Uses cubic Bezier circle approximation: control point offset = radius * 0.5523
"""

import os
import math
from xml.etree import ElementTree as ET

SRC_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")

WEIGHTS = ["A", "B", "C"]
SLANTS = ["", " Slanted"]
FAMILIES = [("mono", "Mono"), ("sans", "Sans")]
STYLES = ["Casual", "Linear"]

# Bezier constant for circle approximation
KAPPA = 0.5523


def get_contour_bounds(contour):
    """Get bounding box of contour from on-curve and off-curve points."""
    pts = contour.findall("point")
    xs = [float(p.get("x")) for p in pts]
    ys = [float(p.get("y")) for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def make_circular_contour(contour, target_ratio=1.0):
    """Reshape a 14-point contour to be more circular while preserving structure.

    The contour has 6 on-curve points and 8 off-curve points.
    We keep the same point count and types but adjust positions to create
    a more circular shape.

    target_ratio: height/width ratio. 1.0 = perfect circle.
    """
    pts = contour.findall("point")
    xs = [float(p.get("x")) for p in pts]
    ys = [float(p.get("y")) for p in pts]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    cx = (x_min + x_max) / 2
    cy = (y_min + y_max) / 2

    cur_w = x_max - x_min
    cur_h = y_max - y_min

    if cur_w == 0 or cur_h == 0:
        return

    # Target: make it circular. Use geometric mean of current dimensions
    # as the diameter, scaled up 10% to better match Iosevka's larger dots
    diameter = (cur_w * cur_h) ** 0.5 * 1.1

    target_w = diameter
    target_h = diameter * target_ratio

    # Scale factors
    sx = target_w / cur_w
    sy = target_h / cur_h

    for p in pts:
        old_x = float(p.get("x"))
        old_y = float(p.get("y"))

        new_x = cx + (old_x - cx) * sx
        new_y = cy + (old_y - cy) * sy

        # Round to 4 decimal places, clean up
        new_x = round(new_x, 4)
        new_y = round(new_y, 4)

        if new_x == int(new_x):
            p.set("x", str(int(new_x)))
        else:
            p.set("x", str(new_x))

        if new_y == int(new_y):
            p.set("y", str(int(new_y)))
        else:
            p.set("y", str(new_y))


def process_glyph(path, contour_indices=None):
    """Make specified contours circular in a glyph file."""
    tree = ET.parse(path)
    root = tree.getroot()
    outline = root.find("outline")
    if outline is None:
        return False

    contours = outline.findall("contour")
    if contour_indices is None:
        contour_indices = range(len(contours))

    for idx in contour_indices:
        if idx < len(contours):
            make_circular_contour(contours[idx])

    tree.write(path, xml_declaration=True, encoding="UTF-8")
    return True


def main():
    total = 0

    glyphs_to_fix = [
        ("dotaccentcomb.glif", None),   # all contours (just 1)
        ("period.glif", None),          # all contours (just 1)
        ("ellipsis.glif", None),        # all 3 dot contours
        ("question.glif", [0]),         # just contour 0 (the dot)
    ]

    for family_dir, family_name in FAMILIES:
        ufo_root = os.path.join(SRC_ROOT, family_dir)
        for style in STYLES:
            for weight in WEIGHTS:
                for slant in SLANTS:
                    ufo_name = f"Recursive {family_name}-{style} {weight}{slant}.ufo"
                    ufo_path = os.path.join(ufo_root, ufo_name)

                    if not os.path.isdir(ufo_path):
                        continue

                    label = f"{family_name} {style} {weight}{slant}"

                    for glyph_file, contour_idxs in glyphs_to_fix:
                        glyph_path = os.path.join(ufo_path, "glyphs", glyph_file)
                        if os.path.exists(glyph_path):
                            process_glyph(glyph_path, contour_idxs)
                            print(f"  {label}: {glyph_file} -> circular")
                            total += 1

    print(f"\nDone: {total} glyph files updated")


if __name__ == "__main__":
    main()
