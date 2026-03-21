#!/usr/bin/env python3
"""
Fix Q tail: make the inner end blunt with even stroke thickness.

The Q tail contour has 26 points. The inner end (point 0) is where the
inner edge (pts 24→25→0) and outer edge (0→1→2) converge, creating a
pointed thin tip. This script spreads point 0 and point 1 apart to form
a flat blunt cap with even stroke width, and adjusts neighboring offcurves.

Contour flow at the tip:
  ...23(curve) → 24(off) → 25(off) → 0(curve) → 1(line) → 2(off) → 3(off)...
  Inner edge approaches from 24-25, outer edge departs via 1-2-3.
"""

import os
import math
import glob
import plistlib
from xml.etree import ElementTree as ET


UFO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")

# Desired stroke half-width (perpendicular to tail direction)
HALF_WIDTH = 20


def fmt(value):
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))
    return str(rounded)


def fix_q(glif_path):
    """Make Q tail tip blunt with even stroke thickness."""
    try:
        tree = ET.parse(glif_path)
    except ET.ParseError:
        print(f"  WARNING: Could not parse {glif_path}, skipping")
        return False

    root = tree.getroot()
    contours = root.findall(".//outline/contour")
    if not contours:
        return False

    points = contours[0].findall("point")
    if len(points) != 26:
        print(f"  WARNING: Expected 26 points, got {len(points)}, skipping")
        return False

    # Read current positions
    def getxy(i):
        return float(points[i].get('x')), float(points[i].get('y'))

    p0_x, p0_y = getxy(0)   # current tip (both edges converge here)
    p1_x, p1_y = getxy(1)   # outer edge departure
    p2_x, p2_y = getxy(2)   # outer edge offcurve
    p3_x, p3_y = getxy(3)   # outer edge offcurve
    p23_x, p23_y = getxy(23) # inner edge curve before offcurves
    p24_x, p24_y = getxy(24) # inner edge offcurve
    p25_x, p25_y = getxy(25) # inner edge offcurve

    # Compute the tail direction at the tip using the approach vectors
    # Average of inner approach (25→0) and outer departure (0→1)
    inner_dx = p0_x - p25_x
    inner_dy = p0_y - p25_y
    outer_dx = p1_x - p0_x
    outer_dy = p1_y - p0_y

    # Tail center direction (pointing inward, toward the tip)
    center_dx = inner_dx - outer_dx  # bisector-ish
    center_dy = inner_dy - outer_dy
    length = math.sqrt(center_dx**2 + center_dy**2)
    if length < 1:
        # Fallback: use inner approach direction
        center_dx, center_dy = inner_dx, inner_dy
        length = math.sqrt(center_dx**2 + center_dy**2)

    # Normalize
    cdx = center_dx / length
    cdy = center_dy / length

    # Perpendicular direction (rotated 90° CCW)
    perp_x = -cdy
    perp_y = cdx

    # Create blunt cap: split the tip into two points offset perpendicular
    # Point 0 becomes the "left" side of the cap (inner edge end)
    # Point 1 becomes the "right" side of the cap (outer edge start)
    cap_center_x = p0_x
    cap_center_y = p0_y

    # Left side (inner edge end) — offset in perpendicular direction
    new_p0_x = cap_center_x + perp_x * HALF_WIDTH
    new_p0_y = cap_center_y + perp_y * HALF_WIDTH

    # Right side (outer edge start) — offset in opposite perpendicular
    new_p1_x = cap_center_x - perp_x * HALF_WIDTH
    new_p1_y = cap_center_y - perp_y * HALF_WIDTH

    # Adjust offcurve 25 to approach the new point 0 position smoothly
    # Shift it toward the inner edge side
    new_p25_x = p25_x + perp_x * HALF_WIDTH * 0.6
    new_p25_y = p25_y + perp_y * HALF_WIDTH * 0.6

    # Adjust offcurve 24 slightly
    new_p24_x = p24_x + perp_x * HALF_WIDTH * 0.3
    new_p24_y = p24_y + perp_y * HALF_WIDTH * 0.3

    # Adjust offcurve 2 to depart from new point 1 position smoothly
    # Shift it toward the outer edge side
    new_p2_x = p2_x - perp_x * HALF_WIDTH * 0.4
    new_p2_y = p2_y - perp_y * HALF_WIDTH * 0.4

    # Adjust offcurve 3 slightly
    new_p3_x = p3_x - perp_x * HALF_WIDTH * 0.2
    new_p3_y = p3_y - perp_y * HALF_WIDTH * 0.2

    # Apply changes
    for pt, x, y in [
        (points[0], new_p0_x, new_p0_y),
        (points[1], new_p1_x, new_p1_y),
        (points[2], new_p2_x, new_p2_y),
        (points[3], new_p3_x, new_p3_y),
        (points[24], new_p24_x, new_p24_y),
        (points[25], new_p25_x, new_p25_y),
    ]:
        pt.set('x', fmt(x))
        pt.set('y', fmt(y))

    tree.write(glif_path, xml_declaration=True, encoding="UTF-8")
    print(f"  Fixed Q tip in {os.path.basename(glif_path)}: "
          f"cap width={HALF_WIDTH*2}, center=({fmt(cap_center_x)},{fmt(cap_center_y)})")
    return True


def process_ufo(ufo_path):
    ufo_name = os.path.basename(ufo_path)
    print(f"\n{ufo_name}:")

    glyph_dirs = [os.path.join(ufo_path, "glyphs")]
    layercontents_path = os.path.join(ufo_path, "layercontents.plist")
    if os.path.exists(layercontents_path):
        with open(layercontents_path, "rb") as f:
            layers = plistlib.load(f)
        glyph_dirs = [os.path.join(ufo_path, layer_dir) for _, layer_dir in layers]

    total = 0
    for glyph_dir in glyph_dirs:
        if not os.path.isdir(glyph_dir):
            continue
        glif_path = os.path.join(glyph_dir, "Q_.glif")
        if os.path.exists(glif_path):
            if fix_q(glif_path):
                total += 1
    return total


def main():
    print("=" * 70)
    print("Fix Q: Make tail tip blunt with even stroke thickness")
    print("=" * 70)

    mono_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")))
    sans_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo")))
    all_ufos = mono_ufos + sans_ufos

    print(f"\nFound {len(all_ufos)} UFO masters")

    total = 0
    for ufo_path in all_ufos:
        total += process_ufo(ufo_path)

    print(f"\n{'=' * 70}")
    print(f"Done! Fixed Q tip in {total} glyph files.")
    print("=" * 70)


if __name__ == "__main__":
    main()
