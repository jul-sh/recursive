#!/usr/bin/env python3
"""
Remove the top terminal scroll from S across ALL masters for interpolation
compatibility.

The S glyph has an elaborate scroll/flag at the top terminal. This script
removes the scroll points and replaces them with a simple rounded cap
(2 offcurve points), consistently across all masters.

In all 65-point S glyphs, the structure is:
  - Points 0-46: main S body (47 points)
  - Point 47: line (scroll start)
  - Points 47-61: scroll geometry (15 points)
  - Points 62-64: closing curve back to point 0 (3 points)

The fix:
  1. Keep points 0-46 (adjusting approach + terminal coords at 44-46)
  2. Remove scroll points 47-61
  3. Add 2 offcurve cap points
  4. Keep closing points 62-64

Point count: 65 -> 52 (removes 15 scroll points, adds 2 cap offcurves)
"""

import glob
import os
from xml.etree import ElementTree as ET


def fix_S_scroll(glif_path):
    """Remove scroll from S and add rounded cap, for any master."""
    tree = ET.parse(glif_path)
    root = tree.getroot()
    contours = root.findall('.//outline/contour')
    if not contours:
        return False

    contour = contours[0]
    points = list(contour.findall('point'))

    if len(points) != 65:
        print(f"  Skipping {os.path.basename(glif_path)}: has {len(points)} points (expected 65)")
        return False

    # Verify structural assumption: point 47 must be a line (scroll start)
    if points[47].get('type') != 'line':
        print(f"  Unexpected: point 47 is not 'line' in {os.path.basename(glif_path)}")
        return False

    # Verify point 46 is a curve (the terminal)
    if points[46].get('type') != 'curve':
        print(f"  Unexpected: point 46 is not 'curve' in {os.path.basename(glif_path)}")
        return False

    # Get coordinates
    first_pt = points[0]
    first_x = float(first_pt.get('x'))
    first_y = float(first_pt.get('y'))

    # The two offcurves before the terminal define the approach
    pre1 = points[44]  # offcurve
    pre2 = points[45]  # offcurve
    on_pt = points[46]  # curve (the terminal)

    term_x = float(on_pt.get('x'))
    term_y = float(on_pt.get('y'))

    # Modify the approach: extend the terminal further right
    pre1.set('x', str(round(float(pre1.get('x')) + 20, 4)))
    pre2.set('x', str(round(float(pre2.get('x')) + 15, 4)))

    # Move the terminal curve point further right and up
    new_term_x = round(term_x + 20, 4)
    new_term_y = round(term_y + 15, 4)
    on_pt.set('x', str(new_term_x))
    on_pt.set('y', str(new_term_y))

    # Add smooth to key points
    points[43].set('smooth', 'yes')  # curve before terminal approach
    on_pt.set('smooth', 'yes')       # the terminal itself

    # Save the closing points (62-64) before removing scroll
    closing_data = []
    for i in [62, 63, 64]:
        pt = points[i]
        closing_data.append({
            'x': pt.get('x'),
            'y': pt.get('y'),
            'type': pt.get('type'),
            'smooth': pt.get('smooth'),
        })

    # Remove all points after the terminal (47-64)
    for pt in points[47:]:
        contour.remove(pt)

    # Compute 2 offcurve cap points
    cap_height = first_y - new_term_y
    cap_extend = 30

    cap_data = [
        {'x': str(round(new_term_x + cap_extend, 4)),
         'y': str(round(new_term_y + cap_height * 0.2, 4))},
        {'x': str(round(new_term_x + cap_extend, 4)),
         'y': str(round(first_y - cap_height * 0.2, 4))},
    ]

    for cp in cap_data:
        elem = ET.SubElement(contour, 'point')
        elem.set('x', cp['x'])
        elem.set('y', cp['y'])

    # Re-add the closing points (curve + 2 offcurves connecting back to pt 0)
    for cd in closing_data:
        elem = ET.SubElement(contour, 'point')
        elem.set('x', cd['x'])
        elem.set('y', cd['y'])
        if cd['type']:
            elem.set('type', cd['type'])
        if cd['smooth']:
            elem.set('smooth', cd['smooth'])

    tree.write(glif_path, xml_declaration=True, encoding='UTF-8')
    return True


def main():
    ufo_dirs = sorted(glob.glob('src/ufo/*/Recursive *.ufo'))

    count = 0
    for ufo_dir in ufo_dirs:
        glyphs_dir = os.path.join(ufo_dir, 'glyphs')
        ufo_name = os.path.basename(ufo_dir)

        s_path = os.path.join(glyphs_dir, 'S_.glif')
        if os.path.exists(s_path):
            if fix_S_scroll(s_path):
                print(f"  {ufo_name}: fixed S scroll")
                count += 1

    print(f"\nFixed {count} S glyphs across all masters")


if __name__ == '__main__':
    main()
