#!/usr/bin/env python3
"""
Extend Q's tail to cross through the center of the O circle.

Currently the tail starts at the bottom-right edge of the O and goes
down-right. This script extends point 0 (the tail's top/inner end)
further into the O circle so the tail visually crosses through it.

The Q glyph has: 1 contour (tail, 26 points) + 1 O component.
Point 0 is the inner end of the tail (where it meets the O circle).
Point 1 is a line going down from point 0.
Points 24-25 are offcurves approaching point 0 from the bottom.
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


def fix_q(glif_path):
    """Extend Q tail to cross through the O circle."""
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

    # Current point 0 position (tail's inner end)
    p0_x = float(points[0].get('x'))
    p0_y = float(points[0].get('y'))

    # Current point 1 position (line going down from tail end)
    p1_x = float(points[1].get('x'))
    p1_y = float(points[1].get('y'))

    # Current offcurves approaching point 0
    p24_x = float(points[24].get('x'))
    p24_y = float(points[24].get('y'))
    p25_x = float(points[25].get('x'))
    p25_y = float(points[25].get('y'))

    # Extend the tail inward: move point 0 up and to the left
    # The O circle center is roughly at x=250, y=350
    # We want the tail to cross through the lower portion of the circle
    # Move point 0 from ~(327, 35) to ~(210, 250) for a nice crossing diagonal

    # Calculate the extension vector (toward center-left and up)
    dx = p0_x - p1_x  # direction from p1 to p0 (roughly +32, +32 in Casual A)
    dy = p0_y - p1_y

    # Extend point 0 significantly further in the same general direction
    # but angled more toward the circle center
    new_p0_x = p0_x - 100  # move ~100 units left into circle
    new_p0_y = p0_y + 180  # move ~180 units up into circle

    # Adjust point 1 to maintain a good angle for the tail
    new_p1_x = p1_x - 30   # slight adjustment
    new_p1_y = p1_y + 50    # move up a bit

    # Adjust offcurves 24-25 to smoothly approach the new point 0
    new_p24_x = p24_x - 50
    new_p24_y = p24_y + 60

    new_p25_x = p25_x - 80
    new_p25_y = p25_y + 120

    # Apply changes
    points[0].set('x', fmt(new_p0_x))
    points[0].set('y', fmt(new_p0_y))
    points[1].set('x', fmt(new_p1_x))
    points[1].set('y', fmt(new_p1_y))
    points[24].set('x', fmt(new_p24_x))
    points[24].set('y', fmt(new_p24_y))
    points[25].set('x', fmt(new_p25_x))
    points[25].set('y', fmt(new_p25_y))

    tree.write(glif_path, xml_declaration=True, encoding="UTF-8")
    print(f"  Extended Q tail in {os.path.basename(glif_path)}: "
          f"({fmt(p0_x)},{fmt(p0_y)}) -> ({fmt(new_p0_x)},{fmt(new_p0_y)})")
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
    print("Fix Q: Extend tail through center of O circle")
    print("=" * 70)

    mono_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")))
    sans_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo")))
    all_ufos = mono_ufos + sans_ufos

    print(f"\nFound {len(all_ufos)} UFO masters")

    total = 0
    for ufo_path in all_ufos:
        total += process_ufo(ufo_path)

    print(f"\n{'=' * 70}")
    print(f"Done! Extended Q tail in {total} glyph files.")
    print("=" * 70)


if __name__ == "__main__":
    main()
