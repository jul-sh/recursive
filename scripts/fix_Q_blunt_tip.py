#!/usr/bin/env python3
"""
Fix Q tail tip to have even stroke thickness (blunt, non-pointy end).

The Q tail is a closed contour shaped like a wedge — both edges converge
at point 0, creating a pointed tip. To make it blunt with even thickness:

1. Compute the stroke center line from the tail base (point 23/4) to the tip
2. Offset point 0 and point 1 to opposite sides of the center line
3. Offset control points 24-25 to the inner edge and 2-3 to the outer edge
   so the two edges run parallel at the stroke width (~40 units)

The key insight: for parallel edges, the control points must be offset
by MORE than the desired stroke half-width to compensate for Bézier
curve behavior (curves are pulled toward the average of control points).
"""

import os
import math
import glob
import plistlib
from xml.etree import ElementTree as ET


UFO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")

# Offset per side — slightly more than half the stroke width to compensate
# for Bézier averaging. Results in ~38-40 unit stroke width.
OFFSET = 27


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

    def getxy(i):
        return float(points[i].get('x')), float(points[i].get('y'))

    # Key positions: point 23 (inner edge base) and point 4 (outer edge base)
    # are where the two edges of the tail meet the decorative curl.
    # Their midpoint defines the stroke center at the base.
    p23_x, p23_y = getxy(23)
    p4_x, p4_y = getxy(4)
    base_center_x = (p23_x + p4_x) / 2
    base_center_y = (p23_y + p4_y) / 2

    # The tip center is the current point 0 position (or midpoint of 0 and 1
    # if they were already separated by a previous fix attempt).
    p0_x, p0_y = getxy(0)
    p1_x, p1_y = getxy(1)
    tip_center_x = (p0_x + p1_x) / 2
    tip_center_y = (p0_y + p1_y) / 2

    # Stroke direction from base to tip
    dx = tip_center_x - base_center_x
    dy = tip_center_y - base_center_y
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1:
        print(f"  WARNING: degenerate stroke in {os.path.basename(glif_path)}, skipping")
        return False

    # Unit direction along stroke
    udx = dx / length
    udy = dy / length

    # Perpendicular direction (90° CW): this points to the RIGHT of the stroke
    # when looking from base toward tip
    perp_x = udy
    perp_y = -udx

    # LEFT edge = center - OFFSET * perp (inner edge, points 24→25→0)
    # RIGHT edge = center + OFFSET * perp (outer edge, points 1→2→3)
    left_ox = -OFFSET * perp_x
    left_oy = -OFFSET * perp_y
    right_ox = OFFSET * perp_x
    right_oy = OFFSET * perp_y

    # === Cap endpoints ===
    new_p0_x = tip_center_x + left_ox
    new_p0_y = tip_center_y + left_oy
    new_p1_x = tip_center_x + right_ox
    new_p1_y = tip_center_y + right_oy

    # === Control points along center line at 1/3 and 2/3 ===
    # For inner edge (23 → 24 → 25 → 0):
    #   24 at ~1/3 from base, 25 at ~2/3 from base, offset LEFT
    center_13_x = base_center_x + dx * 0.33
    center_13_y = base_center_y + dy * 0.33
    center_23_x = base_center_x + dx * 0.67
    center_23_y = base_center_y + dy * 0.67

    new_p24_x = center_13_x + left_ox
    new_p24_y = center_13_y + left_oy
    new_p25_x = center_23_x + left_ox
    new_p25_y = center_23_y + left_oy

    # For outer edge (1 → 2 → 3 → 4):
    #   2 at ~1/3 from tip toward base, 3 at ~2/3 from tip toward base
    #   which is 2/3 and 1/3 from base respectively, offset RIGHT
    new_p2_x = center_23_x + right_ox
    new_p2_y = center_23_y + right_oy
    new_p3_x = center_13_x + right_ox
    new_p3_y = center_13_y + right_oy

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

    cap_dist = math.sqrt((new_p1_x - new_p0_x)**2 + (new_p1_y - new_p0_y)**2)
    print(f"  Fixed Q tip in {os.path.basename(glif_path)}: "
          f"cap width={cap_dist:.0f}, center=({fmt(tip_center_x)},{fmt(tip_center_y)})")
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
    print("Fix Q: Even stroke thickness at tail tip (blunt end)")
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
