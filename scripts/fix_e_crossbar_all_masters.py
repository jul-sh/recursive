#!/usr/bin/env python3
"""
Fix the e crossbar across ALL masters for interpolation compatibility.

The crossbar area currently has a sharp right corner with extra points.
This script:
1. Removes 4 points in the crossbar junction (the line + offcurve + offcurve + curve
   sequence between the crossbar baseline and the right wall)
2. Updates smooth attributes to round the crossbar corners

The fix is applied by finding the characteristic point pattern in the crossbar
area: a sequence of line, line, line, offcurve, offcurve, curve, line — and
removing the middle 4 points (the offcurve, offcurve, curve, line before the
final wall section).

Point type sequence before (53 pts):
  ... curve line line LINE OFF OFF CURVE line off off curve line off off
Point type sequence after (49 pts):
  ... curve line line line off off curve line off off
"""

import glob
import os
import re
from xml.etree import ElementTree as ET


def fix_e_crossbar(glif_path):
    """Remove 4 extra crossbar junction points and update smooth attributes."""
    tree = ET.parse(glif_path)
    root = tree.getroot()
    contours = root.findall('.//outline/contour')
    if not contours:
        return False

    contour = contours[0]
    points = list(contour.findall('point'))

    if len(points) != 53:
        print(f"  Skipping {os.path.basename(glif_path)}: has {len(points)} points (expected 53)")
        return False

    # Find the crossbar pattern: three consecutive line-type points
    # The pattern is: curve, line, line, line, off, off, curve, line
    # We need to find indices of these three consecutive lines
    target = None
    for i in range(len(points) - 7):
        types = []
        for j in range(8):
            t = points[i + j].get('type')
            types.append(t if t else 'off')

        if types == ['curve', 'line', 'line', 'line', 'off', 'off', 'curve', 'line']:
            target = i
            break

    if target is None:
        print(f"  Could not find crossbar pattern in {os.path.basename(glif_path)}")
        return False

    # Points to remove: the 4 points at target+3, target+4, target+5, target+6
    # These are: line, offcurve, offcurve, curve
    # (the junction between crossbar and right wall)
    remove_indices = [target + 3, target + 4, target + 5, target + 6]

    # Also update smooth attributes:
    # The curve just before the crossbar (at target-3 relative to the line sequence)
    # In the full contour, this is the point 3 before 'target':
    # target+0 is curve (counter bottom-right) -> add smooth
    # target-1 through target-3 is the approach -> the curve at target is already there
    # Actually let me identify by the pattern positions:

    # target+0: curve -> already exists, ADD smooth="yes"
    # target-14 area: the curve before the crossbar (point 39 in example) -> this is
    #   actually at a different offset depending on master, let me find it differently

    # Find the curve point right before the line-line-line sequence
    # That's at target+0 (the curve in our pattern match)
    curve_before_crossbar = points[target]  # curve
    curve_before_crossbar.set('smooth', 'yes')

    # The curve 3 positions before that (where the counter meets crossbar)
    # This is the point at target-3 which should be: off, off, CURVE
    pt_counter_corner = points[target - 3]
    if pt_counter_corner.get('type') == 'curve':
        pt_counter_corner.set('smooth', 'yes')

    # Now remove the 4 points (in reverse order to preserve indices)
    for idx in sorted(remove_indices, reverse=True):
        contour.remove(points[idx])

    # After removal, update references
    points = list(contour.findall('point'))

    # The point that was at target+7 (line, the right wall start) is now at target+3
    # Add smooth to it
    right_wall_line = points[target + 3]
    if right_wall_line.get('type') == 'line':
        right_wall_line.set('smooth', 'yes')

    # The curve after the right wall offcurves (was target+10, now target+6)
    right_wall_curve = points[target + 6]
    if right_wall_curve.get('type') == 'curve':
        right_wall_curve.set('smooth', 'yes')

    # The line after that curve (was target+11, now target+7)
    right_wall_line2 = points[target + 7]
    if right_wall_line2.get('type') == 'line':
        right_wall_line2.set('smooth', 'yes')

    tree.write(glif_path, xml_declaration=True, encoding='UTF-8')
    return True


def main():
    ufo_dirs = sorted(glob.glob('src/ufo/*/Recursive *.ufo'))

    count = 0
    for ufo_dir in ufo_dirs:
        glyphs_dir = os.path.join(ufo_dir, 'glyphs')
        ufo_name = os.path.basename(ufo_dir)

        e_path = os.path.join(glyphs_dir, 'e.glif')
        if os.path.exists(e_path):
            if fix_e_crossbar(e_path):
                print(f"  {ufo_name}: fixed e crossbar")
                count += 1

    print(f"\nFixed {count} e glyphs across all masters")


if __name__ == '__main__':
    main()
