#!/usr/bin/env python3
"""
Fix several glyph shapes across all UFO sources:
1. Lowercase e: Round the top-right corner
2. Capital S: Simplify top terminal scroll
3. dotaccentcomb: Enlarge the dot for i/j
"""

import glob
import os
from xml.etree import ElementTree as ET


def fix_e(glif_path):
    """Round the top-right corner of lowercase e.

    The current e has an angular top-right where the inner counter
    makes a sharp turn. We adjust the offcurve points to create
    a smoother, more rounded arc.
    """
    tree = ET.parse(glif_path)
    root = tree.getroot()
    contours = root.findall('.//outline/contour')
    if not contours:
        return False

    contour = contours[0]
    points = contour.findall('point')

    # Find the characteristic pattern: point at ~(351, 472) type=curve
    # preceded by offcurves at ~(310, 488) and ~(330, 484)
    target_idx = None
    for i, pt in enumerate(points):
        x, y = float(pt.get('x')), float(pt.get('y'))
        if (pt.get('type') == 'curve' and 340 < x < 365 and 460 < y < 485):
            # Check preceding offcurves
            p1 = points[i-2]
            p2 = points[i-1]
            if (p1.get('type') is None and p2.get('type') is None and
                300 < float(p1.get('x')) < 325 and 480 < float(p1.get('y')) < 500):
                target_idx = i
                break

    if target_idx is None:
        print(f"  Could not find e top-right pattern in {os.path.basename(glif_path)}")
        return False

    # Points to modify (0-indexed):
    # target_idx-2: offcurve ~(310, 488) → make higher
    # target_idx-1: offcurve ~(330, 484) → make higher and further right
    # target_idx: curve ~(351.7, 472) → make higher and further right
    # target_idx+1: offcurve ~(376.7, 442) → adjust
    # target_idx+2: offcurve ~(389.2, 411) → adjust

    pts = points

    # Inner counter top-right adjustments
    p38 = pts[target_idx - 2]
    p39 = pts[target_idx - 1]
    p40 = pts[target_idx]
    p41 = pts[target_idx + 1]
    p42 = pts[target_idx + 2]

    # Current values and adjustments
    # Pull offcurves up and right to create a rounder arc
    p38.set('x', str(round(float(p38.get('x')) + 10, 4)))  # 310 → 320
    p38.set('y', str(round(float(p38.get('y')) + 10, 4)))  # 488 → 498

    p39.set('x', str(round(float(p39.get('x')) + 15, 4)))  # 330 → 345
    p39.set('y', str(round(float(p39.get('y')) + 12, 4)))  # 484 → 496

    p40.set('x', str(round(float(p40.get('x')) + 20, 4)))  # 352 → 372
    p40.set('y', str(round(float(p40.get('y')) + 15, 4)))  # 472 → 487

    p41.set('x', str(round(float(p41.get('x')) + 10, 4)))  # 377 → 387
    p41.set('y', str(round(float(p41.get('y')) + 10, 4)))  # 442 → 452

    p42.set('x', str(round(float(p42.get('x')) + 5, 4)))   # 389 → 394
    p42.set('y', str(round(float(p42.get('y')) + 5, 4)))    # 411 → 416

    # Also adjust outer curve top-right (points near the end of the contour)
    # Find the offcurve pair leading to the start point (the outer top-right arc)
    # Pattern: offcurve ~(430, 456), offcurve ~(379, 536)
    for i, pt in enumerate(points):
        x, y = float(pt.get('x')), float(pt.get('y'))
        if (pt.get('type') is None and 425 < x < 440 and 445 < y < 465):
            next_pt = points[(i + 1) % len(points)]
            if (next_pt.get('type') is None and 370 < float(next_pt.get('x')) < 390):
                # Push the outer arc higher
                pt.set('y', str(round(y + 20, 4)))  # 456 → 476
                next_pt.set('x', str(round(float(next_pt.get('x')) + 10, 4)))  # 379 → 389
                break

    tree.write(glif_path, xml_declaration=True, encoding='UTF-8')
    return True


def fix_S_terminal(glif_path):
    """Simplify the top terminal scroll of capital S.

    The casual S has an elaborate scroll/flag at the top terminal
    (about 20 points). We replace it with a simple rounded cap.
    """
    tree = ET.parse(glif_path)
    root = tree.getroot()
    contours = root.findall('.//outline/contour')
    if not contours:
        return False

    contour = contours[0]
    points = list(contour.findall('point'))

    # Find the scroll start: curve point at ~(376.7, 648) followed by
    # a line at ~(357.5, 648)
    scroll_start = None
    for i, pt in enumerate(points):
        x, y = float(pt.get('x')), float(pt.get('y'))
        if (pt.get('type') == 'curve' and 365 < x < 390 and 640 < y < 660):
            next_pt = points[(i + 1) % len(points)]
            if next_pt.get('type') == 'line':
                scroll_start = i
                break

    if scroll_start is None:
        print(f"  Could not find S scroll pattern in {os.path.basename(glif_path)}")
        return False

    # Find the last point before point 1 (which is at ~(315, 720))
    # The scroll ends with offcurves leading back to point 1
    # Point 1 is at index 0 in the contour (first point)
    first_pt = points[0]
    first_x, first_y = float(first_pt.get('x')), float(first_pt.get('y'))

    # The scroll occupies points from scroll_start+1 to the end
    # (points scroll_start+1 through len-1 are the scroll, connecting back to point 0)

    # Also find the two offcurves before the scroll_start point
    # These define the approach to the terminal
    pre1 = points[scroll_start - 2]  # offcurve ~(335.8, 670)
    pre2 = points[scroll_start - 1]  # offcurve ~(360.8, 667)
    on_pt = points[scroll_start]      # curve ~(376.7, 648)

    # Get the coordinates of the terminal approach
    term_x = float(on_pt.get('x'))
    term_y = float(on_pt.get('y'))

    # We'll extend the terminal further right, then cap it with a rounded end
    # The cap connects from the inner wall to the outer wall

    # Modify the approach offcurves to extend further right
    pre1.set('x', str(round(float(pre1.get('x')) + 20, 4)))  # push right
    pre2.set('x', str(round(float(pre2.get('x')) + 15, 4)))  # push right

    # Move the terminal curve point further right and up
    on_pt.set('x', str(round(term_x + 20, 4)))   # e.g. 377 → 397
    on_pt.set('y', str(round(term_y + 15, 4)))    # e.g. 648 → 663

    new_term_x = round(term_x + 20, 4)
    new_term_y = round(term_y + 15, 4)

    # Remove all scroll points (from scroll_start+1 to end)
    scroll_points = points[scroll_start + 1:]
    for sp in scroll_points:
        contour.remove(sp)

    # Add a simple rounded cap: semicircle from terminal to first point
    # Terminal inner: (new_term_x, new_term_y)
    # First point (outer): (first_x, first_y) = (315, 720)

    # Cap midpoint
    mid_x = (new_term_x + first_x) / 2 + 15  # offset outward (to the right)
    mid_y = (new_term_y + first_y) / 2

    # Bezier control points for the cap
    cap_height = (first_y - new_term_y)
    cap_extend = 30  # how far the cap extends to the right

    # Create cap points
    cap_points = [
        # offcurve: pull right from terminal
        {'x': str(round(new_term_x + cap_extend, 4)),
         'y': str(round(new_term_y + cap_height * 0.2, 4))},
        # offcurve: pull right
        {'x': str(round(new_term_x + cap_extend, 4)),
         'y': str(round(first_y - cap_height * 0.2, 4))},
    ]

    for cp in cap_points:
        elem = ET.SubElement(contour, 'point')
        elem.set('x', cp['x'])
        elem.set('y', cp['y'])

    tree.write(glif_path, xml_declaration=True, encoding='UTF-8')
    return True


def fix_dot(glif_path, scale_factor=1.3):
    """Enlarge the dot in dotaccentcomb.

    Scale the dot circle by scale_factor around its center.
    """
    tree = ET.parse(glif_path)
    root = tree.getroot()
    contours = root.findall('.//outline/contour')
    if not contours:
        return False

    contour = contours[0]
    points = contour.findall('point')

    # Find center of the dot
    xs = [float(p.get('x')) for p in points]
    ys = [float(p.get('y')) for p in points]
    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)

    # Scale each point around the center
    for pt in points:
        x = float(pt.get('x'))
        y = float(pt.get('y'))
        new_x = cx + (x - cx) * scale_factor
        new_y = cy + (y - cy) * scale_factor
        pt.set('x', str(round(new_x, 4)))
        pt.set('y', str(round(new_y, 4)))

    tree.write(glif_path, xml_declaration=True, encoding='UTF-8')
    return True


def main():
    ufo_dirs = sorted(glob.glob('src/ufo/*/Recursive *-Casual A.ufo'))

    e_count = 0
    s_count = 0
    dot_count = 0

    for ufo_dir in ufo_dirs:
        glyphs_dir = os.path.join(ufo_dir, 'glyphs')
        ufo_name = os.path.basename(ufo_dir)
        print(f"\n{ufo_name}:")

        # Fix e
        e_path = os.path.join(glyphs_dir, 'e.glif')
        if os.path.exists(e_path):
            if fix_e(e_path):
                print(f"  Fixed e top-right corner")
                e_count += 1

        # Fix S
        s_path = os.path.join(glyphs_dir, 'S_.glif')
        if os.path.exists(s_path):
            if fix_S_terminal(s_path):
                print(f"  Fixed S top terminal")
                s_count += 1

        # Fix dot
        dot_path = os.path.join(glyphs_dir, 'dotaccentcomb.glif')
        if os.path.exists(dot_path):
            if fix_dot(dot_path, scale_factor=1.3):
                print(f"  Enlarged dot (1.3x)")
                dot_count += 1

    print(f"\n{'='*60}")
    print(f"Fixed: {e_count} e glyphs, {s_count} S glyphs, {dot_count} dot glyphs")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
