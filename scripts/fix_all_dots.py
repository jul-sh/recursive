#!/usr/bin/env python3
"""
Replace all dot contours with proper circular Bezier curves.

Affects: dotaccentcomb, period, ellipsis, question (dot only).
All these glyphs have 14-point contours with the pattern:
  curve, line, off, off, curve, off, off, curve, line, off, off, curve, off, off

The LINE segments create flat sides even when coordinates are "round".
This script replaces them with proper circular Bezier curves using
degenerate zero-length LINE segments (LINE point coincident with CURVE point).

Applies to ALL masters (Mono + Sans, Casual + Linear, A/B/C, ± Slanted).
"""

import os
from xml.etree import ElementTree as ET

SRC_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")

WEIGHTS = ["A", "B", "C"]
SLANTS = ["", " Slanted"]
FAMILIES = [("mono", "Mono"), ("sans", "Sans")]
STYLES = ["Casual", "Linear"]

KAPPA = 0.5523


def fmt(v):
    r = round(v, 4)
    if r == int(r):
        return str(int(r))
    return str(r)


def get_contour_center_and_radius(contour):
    """Get center and approximate radius of a dot contour."""
    pts = contour.findall("point")
    xs = [float(p.get("x")) for p in pts]
    ys = [float(p.get("y")) for p in pts]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    # Use geometric mean for radius to handle non-square dots
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    radius = ((w * h) ** 0.5) / 2
    return cx, cy, radius


def build_circular_14pt(cx, cy, radius):
    """Build 14 points forming a circle with the required type pattern.

    Pattern: curve, line, off, off, curve, off, off, curve, line, off, off, curve, off, off
    LINE points are placed coincident with adjacent CURVE points (degenerate segments).
    """
    k = KAPPA
    r = radius

    top = (cx, cy + r)
    right = (cx + r, cy)
    bottom = (cx, cy - r)
    left = (cx - r, cy)

    return [
        (left[0], left[1], "curve"),
        (left[0], left[1], "line"),       # degenerate
        (cx - r, cy - r * k, None),
        (cx - r * k, cy - r, None),
        (bottom[0], bottom[1], "curve"),
        (cx + r * k, cy - r, None),
        (cx + r, cy - r * k, None),
        (right[0], right[1], "curve"),
        (right[0], right[1], "line"),     # degenerate
        (cx + r, cy + r * k, None),
        (cx + r * k, cy + r, None),
        (top[0], top[1], "curve"),
        (cx - r * k, cy + r, None),
        (cx - r, cy + r * k, None),
    ]


def replace_contour_with_circle(contour, radius_override=None):
    """Replace a 14-point dot contour with a circular one."""
    pts = contour.findall("point")
    if len(pts) != 14:
        return False

    cx, cy, auto_radius = get_contour_center_and_radius(contour)
    radius = radius_override if radius_override else auto_radius

    new_pts = build_circular_14pt(cx, cy, radius)
    assert len(new_pts) == 14

    for i, (x, y, pt_type) in enumerate(new_pts):
        pts[i].set("x", fmt(x))
        pts[i].set("y", fmt(y))
        if pt_type is not None:
            pts[i].set("type", pt_type)
        elif "type" in pts[i].attrib:
            del pts[i].attrib["type"]
        if pt_type == "curve":
            pts[i].set("smooth", "yes")
        elif "smooth" in pts[i].attrib:
            del pts[i].attrib["smooth"]

    return True


# Radius overrides per weight for dotaccentcomb (i/j dots)
# These are in source units — the built font scales them down
DOTACCENT_RADII = {
    "A": 32,
    "B": 68,
    "C": 82,
}

# Period/ellipsis dots use auto-radius (preserve existing size)
# but we can override if needed
PERIOD_RADII = {
    "A": None,  # auto
    "B": None,
    "C": None,
}


def process_file(glyph_path, contour_indices=None, radius_override=None):
    """Make specified contours circular in a glyph file."""
    tree = ET.parse(glyph_path)
    root = tree.getroot()
    outline = root.find("outline")
    if outline is None:
        return False

    contours = outline.findall("contour")
    if contour_indices is None:
        contour_indices = range(len(contours))

    modified = False
    for idx in contour_indices:
        if idx < len(contours):
            if replace_contour_with_circle(contours[idx], radius_override):
                modified = True

    if modified:
        tree.write(glyph_path, xml_declaration=True, encoding="UTF-8")
    return modified


def main():
    total = 0

    for family_dir, family_name in FAMILIES:
        ufo_root = os.path.join(SRC_ROOT, family_dir)
        for style in STYLES:
            for weight in WEIGHTS:
                for slant in SLANTS:
                    ufo_name = f"Recursive {family_name}-{style} {weight}{slant}.ufo"
                    ufo_path = os.path.join(ufo_root, ufo_name)

                    if not os.path.isdir(ufo_path):
                        continue

                    label = f"{family_name} {style} {weight}{slant}"
                    glyphs_dir = os.path.join(ufo_path, "glyphs")

                    # dotaccentcomb — use weight-specific radius
                    gpath = os.path.join(glyphs_dir, "dotaccentcomb.glif")
                    if os.path.exists(gpath):
                        r = DOTACCENT_RADII[weight]
                        if process_file(gpath, radius_override=r):
                            print(f"  {label}: dotaccentcomb -> circular (r={r})")
                            total += 1

                    # period — use auto radius
                    gpath = os.path.join(glyphs_dir, "period.glif")
                    if os.path.exists(gpath):
                        if process_file(gpath):
                            print(f"  {label}: period -> circular")
                            total += 1

                    # ellipsis — all 3 contours
                    gpath = os.path.join(glyphs_dir, "ellipsis.glif")
                    if os.path.exists(gpath):
                        if process_file(gpath):
                            print(f"  {label}: ellipsis -> circular")
                            total += 1

                    # question — contour 0 only (the dot)
                    gpath = os.path.join(glyphs_dir, "question.glif")
                    if os.path.exists(gpath):
                        if process_file(gpath, contour_indices=[0]):
                            print(f"  {label}: question dot -> circular")
                            total += 1

    print(f"\nDone: {total} glyph contours updated")


if __name__ == "__main__":
    main()
