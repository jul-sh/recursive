#!/usr/bin/env python3
"""
Fix terminal/ink-trap overhangs on capital letters C, G, J, S, Z.

These letters have "ink trap tab" points (type="line") near the cap height that
protrude above their neighboring contour points, creating visible overhangs.

This script:
1. For C, G, S, J: Finds line-type points near cap height that extend above
   their neighbors and brings them down to match.
2. For Z: Collapses the decorative second contour (flag element) so it doesn't
   protrude above the main letter body.
"""

import os
import glob
import plistlib
from xml.etree import ElementTree as ET


GLYPH_FILES = ["C_.glif", "G_.glif", "J_.glif", "S_.glif", "Z_.glif"]

UFO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")


def fmt(value):
    """Format a number: integer if whole, otherwise up to 4 decimals."""
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))
    return str(rounded)


def parse_contours(root):
    """Parse all contours and return list of point lists."""
    contours = []
    for outline in root.findall("outline"):
        for contour in outline.findall("contour"):
            points = []
            for pt in contour.findall("point"):
                points.append({
                    'x': float(pt.get('x')),
                    'y': float(pt.get('y')),
                    'type': pt.get('type'),
                    'smooth': pt.get('smooth'),
                    'element': pt
                })
            contours.append(points)
    return contours


def fix_terminal_tabs(contours, glyph_name):
    """
    Fix line-type points near cap height that protrude above their neighbors.

    For C, G, S, J: finds line-type points where y > both predecessor and
    successor y-values, and brings them down.

    Returns number of points fixed.
    """
    fixed = 0
    for ci, points in enumerate(contours):
        n = len(points)
        for i in range(n):
            p = points[i]
            # Only look at line-type points near cap height
            if p.get('type') != 'line' or p['y'] < 600:
                continue

            prev_p = points[(i - 1) % n]
            next_p = points[(i + 1) % n]

            # Check if this line point extends above BOTH neighbors
            max_neighbor_y = max(prev_p['y'], next_p['y'])

            if p['y'] > max_neighbor_y + 5:
                # This point protrudes above its neighbors
                # Bring it down to match the predecessor's y (the outer curve level)
                target_y = prev_p['y']
                p['element'].set('y', fmt(target_y))
                fixed += 1

    return fixed


def fix_z_flag(contours):
    """
    Fix Z's decorative second contour (flag element at top-left).

    The second contour extends from ~y=550 up to y=700+, creating a visible
    protrusion. We collapse it by bringing all points above y=560 down to y=555,
    effectively making it invisible.

    Returns number of points fixed.
    """
    if len(contours) < 2:
        return 0

    # Find the flag contour: it's a small contour with points near y=550-700
    # and x < 150 (left side of the letter)
    fixed = 0
    for ci, points in enumerate(contours):
        # Skip the main contour (usually has many points)
        if len(points) > 20:
            continue

        # Check if this contour is the flag: small contour at top-left
        max_y = max(p['y'] for p in points)
        min_y = min(p['y'] for p in points)
        max_x = max(p['x'] for p in points)

        if max_y > 680 and min_y > 500 and max_x < 200:
            # This is the flag contour - collapse it
            for p in points:
                if p['y'] > 560:
                    p['element'].set('y', fmt(555))
                    fixed += 1

    return fixed


def fix_glyph(glif_path):
    """Fix terminal overhangs in a single glyph file."""
    try:
        tree = ET.parse(glif_path)
    except ET.ParseError:
        print(f"  WARNING: Could not parse {glif_path}, skipping")
        return False

    root = tree.getroot()
    glyph_name = os.path.basename(glif_path).replace('.glif', '').rstrip('_')
    contours = parse_contours(root)

    if not contours:
        return False

    total_fixed = 0

    if glyph_name == 'Z':
        total_fixed += fix_z_flag(contours)

    # Fix terminal tabs for all affected glyphs (C, G, J, S, and also Z's main contour)
    total_fixed += fix_terminal_tabs(contours, glyph_name)

    if total_fixed > 0:
        tree.write(glif_path, xml_declaration=True, encoding="UTF-8")
        print(f"  Fixed {os.path.basename(glif_path)}: adjusted {total_fixed} points")
        return True

    return False


def process_ufo(ufo_path):
    """Process a single UFO master."""
    ufo_name = os.path.basename(ufo_path)
    print(f"\n{ufo_name}:")

    glyph_dirs = [os.path.join(ufo_path, "glyphs")]

    layercontents_path = os.path.join(ufo_path, "layercontents.plist")
    if os.path.exists(layercontents_path):
        with open(layercontents_path, "rb") as f:
            layers = plistlib.load(f)
        glyph_dirs = [os.path.join(ufo_path, layer_dir) for _, layer_dir in layers]

    total_fixed = 0
    for glyph_dir in glyph_dirs:
        if not os.path.isdir(glyph_dir):
            continue
        for glyph_file in GLYPH_FILES:
            glif_path = os.path.join(glyph_dir, glyph_file)
            if os.path.exists(glif_path):
                if fix_glyph(glif_path):
                    total_fixed += 1

    if total_fixed == 0:
        print("  No terminal overhangs found")

    return total_fixed


def main():
    print("=" * 70)
    print("Fix Terminal Overhangs: C, G, J, S, Z")
    print("=" * 70)

    mono_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")))
    sans_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo")))
    all_ufos = mono_ufos + sans_ufos

    print(f"\nFound {len(all_ufos)} UFO masters ({len(mono_ufos)} mono, {len(sans_ufos)} sans)")

    total = 0
    for ufo_path in all_ufos:
        total += process_ufo(ufo_path)

    print(f"\n{'=' * 70}")
    print(f"Done! Fixed terminal overhangs in {total} glyph files.")
    print("=" * 70)


if __name__ == "__main__":
    main()
