#!/usr/bin/env python3
"""
Fix top-bar overhangs on capital letters B, R, F, P, E, D.

In these letters, the top horizontal bar contour extends to the LEFT of the
vertical stem, creating visible overhangs. This script aligns the bar's left
edge with the stem's left edge by:

1. Finding the "ink trap tab" at the stem top (two consecutive line-type points)
2. Computing the stem's left edge position (and slope for slanted masters)
3. Moving all points that are to the left of the stem edge to align with it
"""

import os
import sys
import glob
from xml.etree import ElementTree as ET


# Glyphs to fix (J included: its top bar should collapse to stem width)
GLYPH_FILES = ["B_.glif", "R_.glif", "F_.glif", "P_.glif", "E_.glif", "D_.glif", "J_.glif"]

# Root of UFO sources
UFO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")

# Margin: only move points more than this many units to the left of the stem edge
MARGIN = 2.0


def fmt(value):
    """Format a number: integer if whole, otherwise up to 4 decimals."""
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))
    return str(rounded)


def find_tab(contours):
    """
    Find the ink trap tab pattern near cap height.

    Primary: two consecutive line-type points at the same y, where the first
    has a much larger x than the second.

    Fallback (for J etc.): a line-type point near cap height followed by
    off-curve points going down at approximately the same x (indicating the
    stem continues downward from that point).

    Returns (tab_right, tab_left, contour_index, tab_left_index) or None.
    """
    # Primary detection: two consecutive line points at same y
    for ci, points in enumerate(contours):
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            if (p1.get('type') == 'line' and p2.get('type') == 'line' and
                abs(p1['y'] - p2['y']) < 1 and  # same y (within tolerance)
                p1['x'] - p2['x'] > 30 and      # p1 is much further right
                p1['y'] > 500):                  # near cap height
                tab_left_idx = (i + 1) % len(points)
                return p1, p2, ci, tab_left_idx

    # Fallback: line point at y > 630 followed by points going DOWN at same x
    # This handles J-type glyphs where the tab has 3+ line points
    for ci, points in enumerate(contours):
        n = len(points)
        for i in range(n):
            p = points[i]
            if p.get('type') != 'line' or p['y'] < 630:
                continue
            # Check if next 2 points go down at approximately the same x
            n1 = points[(i + 1) % n]
            n2 = points[(i + 2) % n]
            if (n1['y'] < p['y'] - 50 and abs(n1['x'] - p['x']) < 3 and
                n2['y'] < n1['y'] - 50 and abs(n2['x'] - p['x']) < 3):
                # This line point is at the stem position
                # Create a synthetic tab_right (same point) for compatibility
                return p, p, ci, i

    return None


def compute_slope(contour, tab_left_idx, tab_left_x, tab_y):
    """
    Compute the slope (dx/dy) of the stem's left edge by looking at points
    below the tab in the same contour.

    Returns slope (0.0 for non-slanted masters).
    """
    n = len(contour)
    best_point = None
    best_y_diff = 0

    # Look at next 10 points after the tab left for stem left edge points
    for i in range(1, 15):
        idx = (tab_left_idx + i) % n
        p = contour[idx]
        y_diff = abs(tab_y - p['y'])
        if y_diff > best_y_diff and p['y'] < tab_y:
            best_point = p
            best_y_diff = y_diff

    if best_point and best_y_diff > 50:
        slope = (tab_left_x - best_point['x']) / (tab_y - best_point['y'])
        return slope

    return 0.0


def fix_overhang(glif_path):
    """Fix the bar overhang in a single .glif file."""
    try:
        tree = ET.parse(glif_path)
    except ET.ParseError:
        print(f"  WARNING: Could not parse {glif_path}, skipping")
        return False

    root = tree.getroot()

    # Collect all contours and their points
    contours = []
    for outline in root.findall("outline"):
        for contour in outline.findall("contour"):
            points = []
            for pt in contour.findall("point"):
                points.append({
                    'x': float(pt.get('x')),
                    'y': float(pt.get('y')),
                    'type': pt.get('type'),
                    'element': pt
                })
            contours.append(points)

    # Find the tab
    result = find_tab(contours)
    if result is None:
        print(f"  No tab found in {os.path.basename(glif_path)}, skipping")
        return False

    tab_right, tab_left, tab_ci, tab_left_idx = result
    stem_left_x = tab_left['x']
    tab_y = tab_left['y']

    # Compute slope for slanted masters
    raw_slope = compute_slope(contours[tab_ci], tab_left_idx, stem_left_x, tab_y)

    # Slope sanity checks:
    # - If |slope| < 0.05, it's just floating point noise → treat as 0 (non-slanted)
    # - If |slope| > 0.5, the tab detection likely matched a wrong pattern → skip
    if abs(raw_slope) > 0.5:
        print(f"  WARNING: Suspicious slope {raw_slope:.4f} in {os.path.basename(glif_path)}, skipping")
        return False
    slope = raw_slope if abs(raw_slope) >= 0.05 else 0.0

    def stem_x_at_y(y):
        """Compute the stem's left edge x at a given y-level."""
        return stem_left_x + (y - tab_y) * slope

    # Fix all points that are to the left of the stem edge
    # Only fix points near the cap height (y > 500) to avoid touching baseline area
    modified = False
    fixed_count = 0
    for ci, points in enumerate(contours):
        for p in points:
            if p['y'] < 500:
                continue
            target_x = stem_x_at_y(p['y'])
            if p['x'] < target_x - MARGIN:
                p['element'].set('x', fmt(target_x))
                fixed_count += 1
                modified = True

    if modified:
        tree.write(glif_path, xml_declaration=True, encoding="UTF-8")
        print(f"  Fixed {os.path.basename(glif_path)}: moved {fixed_count} points "
              f"(stem_left_x={fmt(stem_left_x)}, slope={slope:.4f})")

    return modified


def process_ufo(ufo_path):
    """Process a single UFO master."""
    ufo_name = os.path.basename(ufo_path)
    print(f"\n{ufo_name}:")

    # Find all glyph layer directories
    glyph_dirs = [os.path.join(ufo_path, "glyphs")]

    # Also check layercontents.plist for additional layers
    import plistlib
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
                if fix_overhang(glif_path):
                    total_fixed += 1

    if total_fixed == 0:
        print("  No overhangs found to fix")

    return total_fixed


def main():
    print("=" * 70)
    print("Fix Bar Overhangs: B, R, F, P, E, D")
    print("=" * 70)

    # Find all UFO masters
    mono_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")))
    sans_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo")))
    all_ufos = mono_ufos + sans_ufos

    print(f"\nFound {len(all_ufos)} UFO masters ({len(mono_ufos)} mono, {len(sans_ufos)} sans)")

    total = 0
    for ufo_path in all_ufos:
        total += process_ufo(ufo_path)

    print(f"\n{'=' * 70}")
    print(f"Done! Fixed overhangs in {total} glyph files.")
    print("=" * 70)


if __name__ == "__main__":
    main()
