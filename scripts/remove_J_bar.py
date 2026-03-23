#!/usr/bin/env python3
"""
Remove the horizontal bar from capital J across ALL masters (Linear, Casual).

The J contour has 46 points. The bar occupies points 19-37:
  - pt 19: top of outer stem (will become cap height)
  - pts 20-34: bar structure (top, left side, bottom)
  - pts 35-37: junction line points

After bar removal: points 19-37 form a simple rounded cap connecting
the outer stem to the inner stem at cap height (~700-712).

For slanted masters, x positions are extrapolated using the stem's slant angle.
"""

import glob
import os
from xml.etree import ElementTree as ET


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
UFO_ROOT = os.path.join(ROOT_DIR, "src", "ufo")

CAP_H = 700  # cap height


def fmt(value):
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))
    s = f"{rounded:.4f}".rstrip('0').rstrip('.')
    return s


def get_slant_dx(pts, idx_lo, idx_hi):
    """Calculate dx/dy slant from two points along a stem."""
    x_lo = float(pts[idx_lo].get('x'))
    y_lo = float(pts[idx_lo].get('y'))
    x_hi = float(pts[idx_hi].get('x'))
    y_hi = float(pts[idx_hi].get('y'))
    dy = y_hi - y_lo
    if abs(dy) < 1:
        return 0
    return (x_hi - x_lo) / dy


def project_x(base_x, base_y, target_y, slant):
    """Project x at target_y given a slant rate."""
    return base_x + (target_y - base_y) * slant


def remove_j_bar(glif_path):
    """Remove the bar from J, replacing with a simple rounded cap."""
    try:
        tree = ET.parse(glif_path)
    except ET.ParseError:
        return False

    root = tree.getroot()
    contours = root.findall('.//outline/contour')
    if not contours:
        return False

    points = contours[0].findall('point')
    if len(points) != 46:
        print(f"    SKIP: {len(points)} points (expected 46)")
        return False

    # Get outer stem slant from pts 16→19 (right stem)
    outer_slant = get_slant_dx(points, 16, 19)

    # Get inner stem slant from pts 44→37 (inner stem up)
    # pt 44 is at the bottom of inner stem approach, pt 37 is the junction
    inner_slant = get_slant_dx(points, 40, 37)

    # Current positions
    x19 = float(points[19].get('x'))
    y19 = float(points[19].get('y'))
    x37 = float(points[37].get('x'))
    y37 = float(points[37].get('y'))

    # Project to cap height
    right_x = project_x(x19, y19, CAP_H, outer_slant)
    inner_x = project_x(x37, y37, CAP_H, inner_slant)

    stem_w = abs(right_x - inner_x)
    mid_x = (right_x + inner_x) / 2

    # Overshoot for rounded cap
    overshoot = 12

    # Build new positions for bar points (indices 19-37)
    # Points 19: move outer stem top to cap height
    new_positions = {
        19: (right_x, CAP_H),
        # 20-22: transition from outer stem to cap top (off, off, curve)
        20: (right_x, CAP_H + 8),
        21: (right_x - stem_w * 0.1, CAP_H + overshoot),
        22: (mid_x + stem_w * 0.15, CAP_H + overshoot),
        # 23-25: cap top going left (off, off, curve)
        23: (mid_x + stem_w * 0.05, CAP_H + overshoot),
        24: (mid_x - stem_w * 0.05, CAP_H + overshoot),
        25: (mid_x - stem_w * 0.15, CAP_H + overshoot),
        # 26-28: transition from cap to inner stem (off, off, curve)
        26: (inner_x + stem_w * 0.1, CAP_H + overshoot),
        27: (inner_x, CAP_H + 8),
        28: (inner_x, CAP_H),
    }

    # Points 29-37: collapse to inner stem top (degenerate)
    for i in range(29, 38):
        new_positions[i] = (inner_x, CAP_H)

    # Apply new positions
    for idx, (x, y) in new_positions.items():
        points[idx].set('x', fmt(x))
        points[idx].set('y', fmt(y))

    # Adjust off-curves leading to pt 19 (pts 17-18) for smooth approach
    # pt 16 is the stem base, pts 17-18 are off-curves going up
    x16 = float(points[16].get('x'))
    y16 = float(points[16].get('y'))
    # Redistribute 17-18 evenly between pt16 and new pt19
    for i, frac in [(17, 0.33), (18, 0.67)]:
        y_new = y16 + (CAP_H - y16) * frac
        x_new = project_x(x16, y16, y_new, outer_slant)
        points[i].set('x', fmt(x_new))
        points[i].set('y', fmt(y_new))

    # Adjust off-curves leaving pt 37 going down (pts 38-39)
    x40 = float(points[40].get('x'))
    y40 = float(points[40].get('y'))
    for i, frac in [(38, 0.33), (39, 0.67)]:
        y_new = CAP_H - (CAP_H - y40) * frac
        x_new = project_x(inner_x, CAP_H, y_new, inner_slant)
        points[i].set('x', fmt(x_new))
        points[i].set('y', fmt(y_new))

    tree.write(glif_path, xml_declaration=True, encoding='UTF-8')
    return True


def main():
    print("=" * 70)
    print("Remove J bar across ALL masters")
    print("=" * 70)

    fixed = 0
    for family in ['mono', 'sans']:
        fam = 'Mono' if family == 'mono' else 'Sans'
        for variant in ['Linear', 'Casual']:
            for weight in ['A', 'B', 'C']:
                for slant in ['', ' Slanted']:
                    ufo = f"Recursive {fam}-{variant} {weight}{slant}.ufo"
                    glif = os.path.join(UFO_ROOT, family, ufo, 'glyphs', 'J_.glif')
                    if not os.path.exists(glif):
                        continue
                    print(f"\n{ufo}:")
                    if remove_j_bar(glif):
                        print(f"  Bar removed")
                        fixed += 1
                    else:
                        print(f"  FAILED")

    print(f"\n{'=' * 70}")
    print(f"Done! Removed bar from {fixed} J glyphs.")
    print("=" * 70)


if __name__ == '__main__':
    main()
