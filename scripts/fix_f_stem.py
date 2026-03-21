#!/usr/bin/env python3
"""
Fix f.mono stem width to match the base f glyph.

The f.mono stem is too thin — its left edge was moved too far right,
making it about half the normal stem width. This script reads the base
f glyph's left stem position and adjusts the f.mono left edge to match.

Affected points in f.mono contour 0: points 2-6 (the left edge of the
stem from hook curve down to baseline).
"""

import os
import glob
import plistlib
from xml.etree import ElementTree as ET


UFO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")


def fmt(value):
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))
    return str(rounded)


def fix_f_mono(ufo_path):
    """Widen f.mono stem to match base f stem width."""
    f_path = os.path.join(ufo_path, "glyphs", "f.glif")
    fm_path = os.path.join(ufo_path, "glyphs", "f.mono.glif")

    if not os.path.exists(f_path) or not os.path.exists(fm_path):
        return False

    # Read base f to get the left stem x position
    f_tree = ET.parse(f_path)
    f_contours = f_tree.findall(".//outline/contour")
    if len(f_contours) < 2:
        return False

    # In the base f, contour 1 is the main body. The left stem edge is
    # the minimum x among points in the stem region (y between 100 and 600)
    f_body = f_contours[1]
    f_pts = f_body.findall("point")
    stem_pts = [(float(p.get('x')), float(p.get('y'))) for p in f_pts
                if 50 < float(p.get('y')) < 650]
    if not stem_pts:
        return False

    target_left_x = min(x for x, y in stem_pts)

    # Read f.mono
    fm_tree = ET.parse(fm_path)
    fm_contours = fm_tree.findall(".//outline/contour")
    if not fm_contours:
        return False

    fm_body = fm_contours[0]
    fm_pts = fm_body.findall("point")

    if len(fm_pts) < 15:
        return False

    # Find the current left edge x (points 2-6 typically)
    # These are the points with the smallest x in the stem region
    current_left_x = None
    left_indices = []
    for i, p in enumerate(fm_pts):
        x = float(p.get('x'))
        y = float(p.get('y'))
        if 30 <= y <= 700 and x < 210:  # left side of stem
            if current_left_x is None or x <= current_left_x + 1:
                current_left_x = min(x, current_left_x) if current_left_x else x
                left_indices.append(i)

    if current_left_x is None:
        return False

    # Move left edge points to target position
    dx = target_left_x - current_left_x
    modified = 0
    for i in left_indices:
        p = fm_pts[i]
        x = float(p.get('x'))
        if abs(x - current_left_x) < 2:  # only move points at the left edge
            p.set('x', fmt(x + dx))
            modified += 1

    if modified > 0:
        fm_tree.write(fm_path, xml_declaration=True, encoding="UTF-8")
        ufo_name = os.path.basename(ufo_path)
        print(f"  {ufo_name}: f.mono left edge {fmt(current_left_x)} -> {fmt(target_left_x)} "
              f"({modified} points, stem width {fmt(float(fm_pts[14].get('x')) - target_left_x)})")
        return True

    return False


def main():
    print("=" * 70)
    print("Fix f.mono stem width")
    print("=" * 70)

    mono_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")))
    sans_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo")))
    all_ufos = mono_ufos + sans_ufos

    total = 0
    for ufo_path in all_ufos:
        if fix_f_mono(ufo_path):
            total += 1

    print(f"\nDone! Fixed f.mono in {total} UFO masters.")


if __name__ == "__main__":
    main()
