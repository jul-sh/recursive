#!/usr/bin/env python3
"""
Adjust .mono glyph shapes to better match Iosevka Charon's geometric style.

Modifications:
- f.mono: Narrow the crossbar (contour 1) on the right side
- r.mono: Trim the arm by horizontally compressing points above x-height/2

These are applied to ALL masters for interpolation consistency.
"""

import os
from xml.etree import ElementTree as ET

SRC_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")

WEIGHTS = ["A", "B", "C"]
SLANTS = ["", " Slanted"]
FAMILIES = [("mono", "Mono"), ("sans", "Sans")]
STYLES = ["Casual", "Linear"]


def fmt(v):
    r = round(v, 4)
    if r == int(r):
        return str(int(r))
    return str(r)


def fix_f_mono(ufo_path):
    """Fix f.mono to match Iosevka's f design.

    Iosevka's f has:
    - No bottom bar/serif (clean stem end)
    - Narrower crossbar (doesn't extend as far left)
    - Tighter, rounder hook (less horizontal extension to the left)
    - Thinner stem (outer/left edge closer to inner/right edge)

    We can't remove contours (breaks interpolation), so we collapse
    the bottom bar to be invisible (all points at same y).
    """
    glyph_path = os.path.join(ufo_path, "glyphs", "f.mono.glif")
    if not os.path.exists(glyph_path):
        return False

    tree = ET.parse(glyph_path)
    root = tree.getroot()
    outline = root.find("outline")
    if outline is None:
        return False

    contours = outline.findall("contour")

    # Collapse the bottom bar contour
    for contour in contours:
        pts = contour.findall("point")
        xs = [float(p.get("x")) for p in pts]
        ys = [float(p.get("y")) for p in pts]

        y_min, y_max = min(ys), max(ys)
        x_min, x_max = min(xs), max(xs)
        height = y_max - y_min
        width = x_max - x_min

        # Bottom bar: wide, short, near baseline (y_max < 200)
        if width > 300 and height < 200 and y_max < 200:
            for p in pts:
                p.set("x", fmt(200))
                p.set("y", fmt(0))

    # Narrow the stem and tighten the hook in the main body contour (contour 0).
    # The problem: Recursive's outer (left) stem edge is too far left (~146),
    # while Iosevka's is closer to center. The hook extends too far left/wide.
    # We need to pull the LEFT side of the stem and hook RIGHTWARD toward the
    # inner (right) stem edge.
    main_contour = contours[0]
    main_pts = main_contour.findall("point")

    if len(main_pts) == 33:
        # Inner stem edge (right side) — this is the reference that stays fixed
        inner_x = float(main_pts[16].get("x"))  # point 16 = inner stem at top

        # Points 0-11 form the outer contour (left side of stem + hook).
        # Pull them rightward toward inner_x to narrow the stem and hook.
        # The compression ratio: ~40% of the distance gets removed.
        compress = 0.6  # keep 60% of the gap = narrow by 40%

        for i in range(12):  # points 0-11
            p = main_pts[i]
            x = float(p.get("x"))
            if x < inner_x - 10:  # only move points left of the inner edge
                gap = inner_x - x
                new_x = inner_x - gap * compress
                p.set("x", fmt(new_x))

    # Narrow the crossbar (contour 1) on the LEFT side.
    # Recursive's crossbar extends to x~50. Iosevka's starts closer to x~120.
    crossbar = contours[1]
    cb_pts = crossbar.findall("point")
    if cb_pts:
        # Find the rightmost x as reference
        cb_xs = [float(p.get("x")) for p in cb_pts]
        cb_right = max(cb_xs)
        # Pull left-side points rightward (toward center)
        for p in cb_pts:
            x = float(p.get("x"))
            if x < 200:  # left side of crossbar
                # Move ~40% of the way toward center (250)
                new_x = x + (250 - x) * 0.4
                p.set("x", fmt(new_x))

    tree.write(glyph_path, xml_declaration=True, encoding="UTF-8")
    return True


def trim_r_arm(ufo_path):
    """Shorten the r.mono arm by compressing the right extension."""
    glyph_path = os.path.join(ufo_path, "glyphs", "r.mono.glif")
    if not os.path.exists(glyph_path):
        return False

    tree = ET.parse(glyph_path)
    root = tree.getroot()
    outline = root.find("outline")
    if outline is None:
        return False

    contours = outline.findall("contour")
    if not contours:
        return False

    # r has a single contour. The arm extends to the right above x-height.
    # We want to compress points that are far right and high up.
    contour = contours[0]
    pts = contour.findall("point")
    xs = [float(p.get("x")) for p in pts]
    ys = [float(p.get("y")) for p in pts]

    x_max = max(xs)
    x_min = min(xs)

    # Find the stem x position (leftmost points near baseline)
    stem_pts = [(float(p.get("x")), float(p.get("y"))) for p in pts if float(p.get("y")) < 100]
    if stem_pts:
        stem_x = min(x for x, y in stem_pts) + 40  # inner edge of stem + some margin
    else:
        stem_x = x_min + 100

    # Compress points to the right of stem, in the upper portion
    # Scale factor: reduce rightward extension by ~25%
    scale = 0.75
    for p in pts:
        x = float(p.get("x"))
        y = float(p.get("y"))
        if x > stem_x + 50 and y > 200:  # upper-right region = the arm
            dx = x - stem_x
            new_x = stem_x + dx * scale
            p.set("x", fmt(new_x))

    tree.write(glyph_path, xml_declaration=True, encoding="UTF-8")
    return True


def main():
    total = 0

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

                    if fix_f_mono(ufo_path):
                        print(f"  {label}: f.mono bottom bar collapsed")
                        total += 1

                    if trim_r_arm(ufo_path):
                        print(f"  {label}: r.mono arm trimmed")
                        total += 1

    print(f"\nDone: {total} modifications")


if __name__ == "__main__":
    main()
