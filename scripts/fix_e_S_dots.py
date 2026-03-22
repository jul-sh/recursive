#!/usr/bin/env python3
"""
Fix several glyph shapes across ALL UFO sources:
1. Lowercase e: Round the top-right corner
2. Capital S: Simplify top terminal scroll
3. dotaccentcomb: Enlarge the dot for i/j

All changes are coordinate-only (no points added or removed) to maintain
interpolation compatibility across all masters.
"""

import glob
import math
import os
from xml.etree import ElementTree as ET


def fix_e(glif_path):
    """Round the top-right corner of lowercase e.

    Adjusts offcurve control points around the inner counter's top-right
    corner (points 31-35) to create a smoother, more rounded arc.
    All masters have 53 points with identical structure.
    """
    tree = ET.parse(glif_path)
    root = tree.getroot()
    contours = root.findall('.//outline/contour')
    if not contours:
        return False

    contour = contours[0]
    points = contour.findall('point')

    if len(points) != 53:
        print(f"  Unexpected e point count {len(points)} in {os.path.basename(glif_path)}")
        return False

    # Points 30-36 form the inner counter's top-right corner:
    # 30: curve   (on-curve before corner)
    # 31: offcurve (handle going right from pt 30)
    # 32: offcurve (handle approaching corner)
    # 33: curve   (the corner itself)
    # 34: offcurve (handle leaving corner going down)
    # 35: offcurve (handle continuing down)
    # 36: curve   (on-curve after corner)

    # Measure the corner's current sharpness by looking at the angle
    x30 = float(points[30].get('x'))
    y30 = float(points[30].get('y'))
    x33 = float(points[33].get('x'))
    y33 = float(points[33].get('y'))
    x36 = float(points[36].get('x'))
    y36 = float(points[36].get('y'))

    # Scale adjustments proportionally based on corner distance
    corner_span = math.sqrt((x33 - x30)**2 + (y33 - y30)**2)
    scale = corner_span / 80.0  # normalize (Casual A ≈ 78 units)

    def adjust(pt, dx, dy):
        x = float(pt.get('x'))
        y = float(pt.get('y'))
        pt.set('x', str(round(x + dx * scale, 4)))
        pt.set('y', str(round(y + dy * scale, 4)))

    # Round the inner counter corner by pushing offcurves outward
    adjust(points[31], 5, 3)    # offcurve: push right and up
    adjust(points[32], 10, 6)   # offcurve: push right and up more
    adjust(points[33], 12, 10)  # corner curve: push outward
    adjust(points[34], 6, 6)    # offcurve: slight outward push
    adjust(points[35], 3, 3)    # offcurve: minimal adjustment

    # Also adjust outer contour near top-right (points 51-52)
    # These offcurves lead back to point 0 and define the outer arc
    adjust(points[51], 0, 8)    # push outer arc up slightly
    adjust(points[52], 4, 0)    # push right slightly

    tree.write(glif_path, xml_declaration=True, encoding='UTF-8')
    return True


def fix_S_terminal(glif_path):
    """Simplify the top terminal scroll of capital S.

    The Casual S has an ornate scroll at the top terminal (points 47-64).
    We collapse the scroll by moving points closer to a simple arc path
    from the terminal junction to the first point, preserving point count.
    Linear masters (which already have simple terminals) are left unchanged.
    """
    tree = ET.parse(glif_path)
    root = tree.getroot()
    contours = root.findall('.//outline/contour')
    if not contours:
        return False

    contour = contours[0]
    points = contour.findall('point')

    if len(points) != 65:
        print(f"  Unexpected S point count {len(points)} in {os.path.basename(glif_path)}")
        return False

    # The terminal scroll is points 47-64, connecting from point 46
    # (the terminal junction) back to point 0 (the outer S body).
    x46 = float(points[46].get('x'))
    y46 = float(points[46].get('y'))
    x0 = float(points[0].get('x'))
    y0 = float(points[0].get('y'))

    # Calculate how far the scroll deviates from a direct path
    # (Linear masters have minimal deviation and should be skipped)
    scroll_indices = list(range(47, 65))
    mid_x = (x46 + x0) / 2
    mid_y = (y46 + y0) / 2
    max_deviation = 0
    for idx in scroll_indices:
        px = float(points[idx].get('x'))
        py = float(points[idx].get('y'))
        # Distance from midpoint of the direct path
        dev = math.sqrt((px - mid_x)**2 + (py - mid_y)**2)
        max_deviation = max(max_deviation, dev)

    if max_deviation < 80:
        # Terminal is already simple enough (Linear masters)
        return False

    # Collapse the scroll toward a simple arc from pt 46 to pt 0.
    # The arc bulges slightly right of the direct path.
    collapse = 0.6  # 0=no change, 1=fully on arc

    total = len(scroll_indices)
    for j, idx in enumerate(scroll_indices):
        t = (j + 1) / (total + 1)  # parameter along path (0→1)

        # Simple arc target: linear interpolation + rightward bulge
        bulge = 20 * math.sin(t * math.pi)
        target_x = x46 + (x0 - x46) * t + bulge
        target_y = y46 + (y0 - y46) * t

        px = float(points[idx].get('x'))
        py = float(points[idx].get('y'))

        new_x = px + (target_x - px) * collapse
        new_y = py + (target_y - py) * collapse

        points[idx].set('x', str(round(new_x, 4)))
        points[idx].set('y', str(round(new_y, 4)))

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
    # Process ALL masters, not just Casual A
    ufo_dirs = sorted(glob.glob('src/ufo/*/Recursive *.ufo'))

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
