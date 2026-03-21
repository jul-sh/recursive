#!/usr/bin/env python3
"""
Remove the horizontal bar from capital J, keeping only the hook.

The J contour has 46 points. Points 19-37 (0-indexed) form the top bar.
This script collapses those points into a simple rounded cap at the top
of the vertical stem, maintaining interpolation compatibility across all masters.

Bar region point types (indices 19-37):
  19:curve 20:off 21:off 22:curve 23:off 24:off 25:curve
  26:off 27:off 28:curve 29:off 30:off 31:curve 32:off 33:off
  34:curve 35:line 36:line 37:line
"""

import os
import glob
import plistlib
from xml.etree import ElementTree as ET


UFO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")

# Bar region: points 19 through 37 (0-indexed)
BAR_START = 19  # right stem top (curve)
BAR_END = 37    # last bar point before inner stem goes down (line)


def fmt(value):
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))
    return str(rounded)


def fix_j(glif_path):
    """Collapse the J bar into a simple rounded cap."""
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
    if len(points) != 46:
        print(f"  WARNING: Expected 46 points, got {len(points)} in {os.path.basename(glif_path)}, skipping")
        return False

    # Get the stem edges from the points just outside the bar
    # Point 16 starts the right stem going up (x = right_stem_x)
    # Point 38+39+40 are the inner stem going down (x = left_stem_x)
    right_x = float(points[16].get('x'))  # right stem edge
    # For the inner stem, point 40 is a curve at the inner edge
    left_x = float(points[40].get('x'))   # left stem edge

    # For slanted masters, the stem is tilted. Use actual positions of points
    # just above/below the bar to determine the cap position.
    # Point 19 is top of right stem, point 37 leads to inner stem
    right_top_x = float(points[19].get('x'))  # where right stem reaches bar
    left_top_x = float(points[37].get('x'))    # where inner stem meets bar

    # Use 700 as cap height (standard for this font)
    cap_h = 700
    mid_x = (right_top_x + left_top_x) / 2
    stem_w = abs(right_top_x - left_top_x)

    # Create a simple rounded cap
    # The cap should be a gentle curve from right stem to left stem at cap height
    # We have 19 points (indices 19-37) to work with

    # Point positions for a clean cap:
    cap_points = [
        # 19: curve - right stem top at cap height
        (right_top_x, cap_h),
        # 20: off - curve up-right
        (right_top_x, cap_h + 8),
        # 21: off - curve across top
        (right_top_x - stem_w * 0.1, cap_h + 12),
        # 22: curve - top right
        (mid_x + stem_w * 0.15, cap_h + 12),
        # 23: off
        (mid_x + stem_w * 0.05, cap_h + 12),
        # 24: off
        (mid_x - stem_w * 0.05, cap_h + 12),
        # 25: curve - top center
        (mid_x - stem_w * 0.15, cap_h + 12),
        # 26: off
        (left_top_x + stem_w * 0.1, cap_h + 12),
        # 27: off
        (left_top_x, cap_h + 8),
        # 28: curve - left stem top at cap height
        (left_top_x, cap_h),
        # 29-37: collapse to left stem top (degenerate)
        (left_top_x, cap_h),
        (left_top_x, cap_h),
        (left_top_x, cap_h),
        (left_top_x, cap_h),
        (left_top_x, cap_h),
        (left_top_x, cap_h),
        # 35-37: line points - collapse
        (left_top_x, cap_h),
        (left_top_x, cap_h),
        (left_top_x, cap_h),
    ]

    # Apply the new positions
    for i, (x, y) in enumerate(cap_points):
        pt = points[BAR_START + i]
        pt.set('x', fmt(x))
        pt.set('y', fmt(y))

    # Also adjust points 17-18 (offcurves leading up to point 19)
    # to smoothly approach the new cap height
    points[17].set('y', fmt(cap_h * 0.5))  # midway up stem
    points[18].set('y', fmt(cap_h * 0.8))  # approaching cap

    # And points 38-39 (offcurves leaving the cap going down inner stem)
    points[38].set('x', fmt(left_top_x))
    points[38].set('y', fmt(cap_h * 0.8))
    points[39].set('x', fmt(left_top_x))
    points[39].set('y', fmt(cap_h * 0.5))

    tree.write(glif_path, xml_declaration=True, encoding="UTF-8")
    print(f"  Fixed J bar in {os.path.basename(glif_path)} "
          f"(right={fmt(right_top_x)}, left={fmt(left_top_x)}, cap={cap_h})")
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
        glif_path = os.path.join(glyph_dir, "J_.glif")
        if os.path.exists(glif_path):
            if fix_j(glif_path):
                total += 1
    return total


def main():
    print("=" * 70)
    print("Fix J: Remove horizontal bar, keep hook only")
    print("=" * 70)

    mono_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")))
    sans_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo")))
    all_ufos = mono_ufos + sans_ufos

    print(f"\nFound {len(all_ufos)} UFO masters")

    total = 0
    for ufo_path in all_ufos:
        total += process_ufo(ufo_path)

    print(f"\n{'=' * 70}")
    print(f"Done! Fixed J bar in {total} glyph files.")
    print("=" * 70)


if __name__ == "__main__":
    main()
