#!/usr/bin/env python3
"""
Remove the vertical downward tab at the top-right of capital C.

The C contour has 52 points. Points 26-36 create a downward vertical
excursion from the terminal (~y=638) down to ~y=427, forming a serif/tab.
Points 36-39 then go back up along the right side.

This script collapses points 27-36 so the contour smoothly transitions
from the terminal (point 26) to the right edge going up (points 37+),
eliminating the downward tab.
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


def fix_c(glif_path):
    """Remove the vertical tab at the top-right terminal of C."""
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
    if len(points) != 52:
        print(f"  WARNING: Expected 52 points, got {len(points)}, skipping")
        return False

    # Read key positions
    p26_x = float(points[26].get('x'))  # terminal end
    p26_y = float(points[26].get('y'))
    p39_x = float(points[39].get('x'))  # right edge going up
    p39_y = float(points[39].get('y'))

    # The right edge x-position (from points 36-39 in the original)
    right_x = float(points[36].get('x'))  # typically ~429

    # We want the contour to go smoothly from terminal (p26) to the right
    # edge going upward, without the downward detour.
    # Create a smooth curve from terminal → right edge at terminal height → up

    # Point 27 (line): move near terminal, slightly right
    # Point 28-29 (off): curve toward right edge
    # Point 30 (curve): on right edge at terminal-ish height
    # Points 31-35 (off/curve): evenly spaced going down to meet point 36
    # Point 36 (curve): stays near right edge but at higher y

    terminal_y = p26_y
    right_edge_y = p39_y  # where the right edge is at right_x

    # Smoothly distribute points from terminal to right edge
    # Point 27: near terminal
    points[27].set('x', fmt(p26_x + 5))
    points[27].set('y', fmt(terminal_y))

    # Point 28 (off): curving toward right edge
    points[28].set('x', fmt(right_x - 5))
    points[28].set('y', fmt(terminal_y - 5))

    # Point 29 (off): approaching right edge
    points[29].set('x', fmt(right_x))
    points[29].set('y', fmt(terminal_y - 15))

    # Point 30 (curve): on right edge
    points[30].set('x', fmt(right_x))
    points[30].set('y', fmt(terminal_y - 30))

    # Points 31-35: evenly space down the right edge toward point 36/39
    span_y = (terminal_y - 30) - right_edge_y
    for i, idx in enumerate([31, 32, 33, 34, 35]):
        frac = (i + 1) / 6.0
        y = (terminal_y - 30) - span_y * frac
        points[idx].set('x', fmt(right_x))
        points[idx].set('y', fmt(y))

    # Point 36: near the right edge, connecting to point 37+
    points[36].set('x', fmt(right_x))
    points[36].set('y', fmt(right_edge_y + 5))

    tree.write(glif_path, xml_declaration=True, encoding="UTF-8")
    print(f"  Fixed C terminal in {os.path.basename(glif_path)}: "
          f"collapsed tab from y={fmt(terminal_y)} (was going to y≈427)")
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
        glif_path = os.path.join(glyph_dir, "C_.glif")
        if os.path.exists(glif_path):
            if fix_c(glif_path):
                total += 1
    return total


def main():
    print("=" * 70)
    print("Fix C: Remove vertical tab at top-right terminal")
    print("=" * 70)

    mono_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")))
    sans_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo")))
    all_ufos = mono_ufos + sans_ufos

    print(f"\nFound {len(all_ufos)} UFO masters")

    total = 0
    for ufo_path in all_ufos:
        total += process_ufo(ufo_path)

    print(f"\n{'=' * 70}")
    print(f"Done! Fixed C terminal in {total} glyph files.")
    print("=" * 70)


if __name__ == "__main__":
    main()
