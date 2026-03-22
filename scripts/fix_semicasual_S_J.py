#!/usr/bin/env python3
"""
Fix S and J glyphs in SemiCasual masters.

S issues:
1. When Linear and Casual S have incompatible contours (different point counts),
   SemiCasual S was copied from Linear. The scroll terminal creates a visible "tag".
   Fix: redistribute terminal points along a smooth monotonic arc.
2. When Linear and Casual S have compatible contours, fontMath inflated the point
   count by converting line segments to degenerate curve segments (e.g. 65→81 pts).
   Fix: re-interpolate directly from XML, preserving point types.

J issue: fontMath converted line segments to degenerate curves, inflating 46→54 pts.
Fix: re-interpolate from XML.
"""

import glob
import math
import os
from xml.etree import ElementTree as ET


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
UFO_ROOT = os.path.join(ROOT_DIR, "src", "ufo")

FACTOR = 0.5


def fmt(value):
    """Format a coordinate value."""
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))
    s = f"{rounded:.4f}".rstrip('0').rstrip('.')
    return s


def get_matching_paths(family, weight, slant_suffix):
    """Return (linear_ufo, casual_ufo, semicasual_ufo) paths."""
    family_cap = "Mono" if family == "mono" else "Sans"
    base = os.path.join(UFO_ROOT, family)
    linear = os.path.join(base, f"Recursive {family_cap}-Linear {weight}{slant_suffix}.ufo")
    casual = os.path.join(base, f"Recursive {family_cap}-Casual {weight}{slant_suffix}.ufo")
    semicasual = os.path.join(base, f"Recursive {family_cap}-SemiCasual {weight}{slant_suffix}.ufo")
    return linear, casual, semicasual


def reinterpolate_glyph(linear_glif, casual_glif, semicasual_glif, expected_pts):
    """Re-interpolate a glyph from Linear and Casual using direct XML coordinate averaging.

    Both sources must have expected_pts points with compatible structure.
    Preserves point types from Linear. Returns True if fixed.
    """
    try:
        tree_l = ET.parse(linear_glif)
        tree_c = ET.parse(casual_glif)
        tree_sc = ET.parse(semicasual_glif)
    except ET.ParseError:
        return False

    contours_l = tree_l.getroot().findall('.//outline/contour')
    contours_c = tree_c.getroot().findall('.//outline/contour')

    if not contours_l or not contours_c:
        return False

    points_l = contours_l[0].findall('point')
    points_c = contours_c[0].findall('point')

    if len(points_l) != expected_pts or len(points_c) != expected_pts:
        return False

    # Check if SemiCasual already has correct point count
    contours_sc = tree_sc.getroot().findall('.//outline/contour')
    if contours_sc:
        pts_sc = contours_sc[0].findall('point')
        if len(pts_sc) == expected_pts:
            # Already correct count — check if it's already properly interpolated
            # by comparing with expected midpoint of first on-curve point
            xl = float(points_l[0].get('x'))
            xc = float(points_c[0].get('x'))
            x_sc = float(pts_sc[0].get('x'))
            expected_x = xl + (xc - xl) * FACTOR
            if abs(x_sc - expected_x) < 0.01:
                return False  # Already properly interpolated

    root_sc = tree_sc.getroot()

    # Replace outline
    outline_sc = root_sc.find('outline')
    if outline_sc is None:
        outline_sc = ET.SubElement(root_sc, 'outline')
    else:
        for contour in outline_sc.findall('contour'):
            outline_sc.remove(contour)

    new_contour = ET.SubElement(outline_sc, 'contour')

    for i in range(expected_pts):
        pt_l = points_l[i]
        pt_c = points_c[i]

        xl = float(pt_l.get('x'))
        yl = float(pt_l.get('y'))
        xc = float(pt_c.get('x'))
        yc = float(pt_c.get('y'))

        x_new = xl + (xc - xl) * FACTOR
        y_new = yl + (yc - yl) * FACTOR

        new_pt = ET.SubElement(new_contour, 'point')
        new_pt.set('x', fmt(x_new))
        new_pt.set('y', fmt(y_new))

        pt_type = pt_l.get('type')
        if pt_type:
            new_pt.set('type', pt_type)
        smooth = pt_l.get('smooth')
        if smooth:
            new_pt.set('smooth', smooth)

    # Interpolate anchors
    anchors_l = {a.get('name'): a for a in tree_l.getroot().findall('anchor')}
    anchors_c = {a.get('name'): a for a in tree_c.getroot().findall('anchor')}

    for anchor in root_sc.findall('anchor'):
        root_sc.remove(anchor)

    for name, al in anchors_l.items():
        ac = anchors_c.get(name)
        new_anchor = ET.SubElement(root_sc, 'anchor')
        if ac:
            x = float(al.get('x')) + (float(ac.get('x')) - float(al.get('x'))) * FACTOR
            y = float(al.get('y')) + (float(ac.get('y')) - float(al.get('y'))) * FACTOR
            new_anchor.set('x', fmt(x))
            new_anchor.set('y', fmt(y))
        else:
            new_anchor.set('x', al.get('x'))
            new_anchor.set('y', al.get('y'))
        new_anchor.set('name', name)

    # Interpolate width
    advance_l = tree_l.getroot().find('advance')
    advance_c = tree_c.getroot().find('advance')
    advance_sc = root_sc.find('advance')
    if advance_l is not None and advance_c is not None and advance_sc is not None:
        wl = float(advance_l.get('width', 500))
        wc = float(advance_c.get('width', 500))
        advance_sc.set('width', fmt(wl + (wc - wl) * FACTOR))

    tree_sc.write(semicasual_glif, xml_declaration=True, encoding='UTF-8')
    return True


def fix_S_terminal(glif_path):
    """Fix the S terminal tag by smoothing the scroll into a clean arc.

    Only applies to 65-point S glyphs (copied from Linear) where the terminal
    has a non-monotonic y path (the "tag").
    """
    try:
        tree = ET.parse(glif_path)
    except ET.ParseError:
        return False

    root = tree.getroot()
    contours = root.findall('.//outline/contour')
    if not contours:
        return False

    contour = contours[0]
    points = contour.findall('point')

    if len(points) != 65:
        return False

    x46 = float(points[46].get('x'))
    y46 = float(points[46].get('y'))
    x0 = float(points[0].get('x'))
    y0 = float(points[0].get('y'))

    # Detect non-monotonic y in terminal (tag = dip then rise)
    ys = [float(points[idx].get('y')) for idx in range(47, 65)]
    has_tag = False
    for i in range(len(ys) - 1):
        if ys[i] > ys[i + 1]:
            for j in range(i + 1, len(ys)):
                if ys[j] > ys[i]:
                    has_tag = True
                    break
            if has_tag:
                break

    if not has_tag:
        return False

    # Redistribute along smooth arc
    scroll_indices = list(range(47, 65))
    total = len(scroll_indices)

    for j, idx in enumerate(scroll_indices):
        t = (j + 1) / (total + 1)
        t_smooth = t * t * (3 - 2 * t)  # smoothstep

        base_x = x46 + (x0 - x46) * t_smooth
        base_y = y46 + (y0 - y46) * t_smooth

        bulge = 12 * math.sin(t * math.pi)
        target_x = base_x + bulge
        target_y = base_y

        points[idx].set('x', fmt(target_x))
        points[idx].set('y', fmt(target_y))

    tree.write(glif_path, xml_declaration=True, encoding='UTF-8')
    return True


def fix_glyph(glyph_name, glif_filename, linear_ufo, casual_ufo, semicasual_ufo,
              layer="glyphs"):
    """Fix a glyph in a specific layer. Returns (method, success) tuple."""
    l_glif = os.path.join(linear_ufo, layer, glif_filename)
    c_glif = os.path.join(casual_ufo, layer, glif_filename)
    sc_glif = os.path.join(semicasual_ufo, layer, glif_filename)

    if not os.path.exists(sc_glif):
        return None, False

    # Check point counts
    try:
        tree_sc = ET.parse(sc_glif)
        sc_pts = tree_sc.getroot().findall('.//outline/contour/point')
        sc_count = len(sc_pts)
    except ET.ParseError:
        return None, False

    if not os.path.exists(l_glif) or not os.path.exists(c_glif):
        # No sources — try terminal fix for S
        if glyph_name == "S" and sc_count == 65:
            return "terminal", fix_S_terminal(sc_glif)
        return None, False

    # Check source point counts
    try:
        tree_l = ET.parse(l_glif)
        tree_c = ET.parse(c_glif)
        l_count = len(tree_l.getroot().findall('.//outline/contour/point'))
        c_count = len(tree_c.getroot().findall('.//outline/contour/point'))
    except ET.ParseError:
        return None, False

    # If sources are compatible, re-interpolate
    if l_count == c_count and sc_count != l_count:
        success = reinterpolate_glyph(l_glif, c_glif, sc_glif, l_count)
        if success:
            return f"reinterp({l_count}pts)", True

    # If sources are incompatible and SemiCasual is a Linear copy, fix terminal
    if glyph_name == "S" and l_count != c_count and sc_count == l_count == 65:
        success = fix_S_terminal(sc_glif)
        if success:
            return "terminal", True

    return None, False


def main():
    print("=" * 70)
    print("Fix SemiCasual S (terminal tag) and J (extra points)")
    print("=" * 70)

    s_fixed = 0
    j_fixed = 0

    for family in ["mono", "sans"]:
        for weight in ["A", "B", "C"]:
            for slant_suffix in ["", " Slanted"]:
                linear_ufo, casual_ufo, semicasual_ufo = get_matching_paths(
                    family, weight, slant_suffix
                )

                sc_name = os.path.basename(semicasual_ufo)
                print(f"\n{sc_name}:")

                for layer in ["glyphs", "glyphs.overlap"]:
                    layer_label = f" [{layer}]" if layer != "glyphs" else ""

                    # Fix S
                    method, success = fix_glyph(
                        "S", "S_.glif",
                        linear_ufo, casual_ufo, semicasual_ufo, layer
                    )
                    if success:
                        print(f"  Fixed S{layer_label} via {method}")
                        s_fixed += 1
                    elif method is None and layer == "glyphs":
                        print(f"  S: already OK or no fix applicable")

                    # Fix J
                    method, success = fix_glyph(
                        "J", "J_.glif",
                        linear_ufo, casual_ufo, semicasual_ufo, layer
                    )
                    if success:
                        print(f"  Fixed J{layer_label} via {method}")
                        j_fixed += 1
                    elif method is None and layer == "glyphs":
                        print(f"  J: already OK or no fix applicable")

    print(f"\n{'=' * 70}")
    print(f"Done! Fixed {s_fixed} S glyphs and {j_fixed} J glyphs.")
    print("=" * 70)


if __name__ == "__main__":
    main()
