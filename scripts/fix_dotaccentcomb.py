#!/usr/bin/env python3
"""
Replace dotaccentcomb contours with circular shapes while preserving
the 14-point structure (curve, line, off, off, curve, off, off, curve,
line, off, off, curve, off, off) required for interpolation.

The two `line` points are placed coincident with adjacent curve points
so they create zero-length line segments, making the curve segments
produce a circular shape.
"""

import os
import math
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


def get_contour_center(glyph_path):
    """Get center of existing dotaccentcomb contour."""
    tree = ET.parse(glyph_path)
    root = tree.getroot()
    contour = root.find("outline").find("contour")
    pts = contour.findall("point")
    xs = [float(p.get("x")) for p in pts]
    ys = [float(p.get("y")) for p in pts]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def build_circular_14pt(cx, cy, radius):
    """Build 14 points forming a circle with the required type pattern.

    Pattern: curve, line, off, off, curve, off, off, curve, line, off, off, curve, off, off

    We use 6 cardinal/intermediate points on the circle for the curve/line points,
    with off-curve control points creating cubic Bezier arcs between them.
    The `line` points sit right on the circle, creating a 6-point circular polygon
    with Bezier curves filling in the arcs.

    Actually, simpler: treat it as a 6-segment curve where 4 segments use Bezier
    and 2 are degenerate lines. We place the 6 on-curve points evenly around the circle.
    """
    k = KAPPA
    r = radius

    # 6 on-curve points at 60-degree intervals around the circle
    # But we need the Bezier control points to work for the cubic segments.
    #
    # Simpler approach: 4 main quadrant points + 2 extra points very close
    # to where the `line` segments are. The line points go at top-left and
    # bottom-right (matching the original contour flow).

    # Original flow: starts top-left, goes to top-left (line=same spot),
    # curves down to bottom-left, curves across to bottom-right,
    # line to bottom-right, curves up to top-right, curves back to top-left.
    #
    # Let's use a simple 4-quadrant circle with the two `line` points
    # coincident with the top-left and bottom-right curve points.

    # Point 0: curve - top-left (actually just "top" or "left" of circle)
    # Point 1: line - same as point 0 (degenerate zero-length line)
    # Points 2,3: offcurve - controls for arc to point 4
    # Point 4: curve - bottom
    # Points 5,6: offcurve - controls for arc to point 7
    # Point 7: curve - bottom-right (actually just "right")
    # Point 8: line - same as point 7 (degenerate)
    # Points 9,10: offcurve - controls for arc to point 11
    # Point 11: curve - top
    # Points 12,13: offcurve - controls for arc back to point 0

    # Top of circle
    top = (cx, cy + r)
    # Right of circle
    right = (cx + r, cy)
    # Bottom of circle
    bottom = (cx, cy - r)
    # Left of circle
    left = (cx - r, cy)

    points = [
        # Point 0: curve at LEFT
        (left[0], left[1], "curve"),
        # Point 1: line at LEFT (degenerate - same position)
        (left[0], left[1], "line"),
        # Points 2,3: offcurve controls LEFT -> BOTTOM
        (cx - r, cy - r * k, None),
        (cx - r * k, cy - r, None),
        # Point 4: curve at BOTTOM
        (bottom[0], bottom[1], "curve"),
        # Points 5,6: offcurve controls BOTTOM -> RIGHT
        (cx + r * k, cy - r, None),
        (cx + r, cy - r * k, None),
        # Point 7: curve at RIGHT
        (right[0], right[1], "curve"),
        # Point 8: line at RIGHT (degenerate)
        (right[0], right[1], "line"),
        # Points 9,10: offcurve controls RIGHT -> TOP
        (cx + r, cy + r * k, None),
        (cx + r * k, cy + r, None),
        # Point 11: curve at TOP
        (top[0], top[1], "curve"),
        # Points 12,13: offcurve controls TOP -> LEFT
        (cx - r * k, cy + r, None),
        (cx - r, cy + r * k, None),
    ]
    return points


def replace_dotaccentcomb(glyph_path, radius):
    """Replace the dotaccentcomb contour with a circular one."""
    tree = ET.parse(glyph_path)
    root = tree.getroot()
    outline = root.find("outline")
    old_contour = outline.find("contour")

    cx, cy = get_contour_center(glyph_path)

    # Build new points
    new_pts = build_circular_14pt(cx, cy, radius)

    # Verify we have 14 points
    assert len(new_pts) == 14, f"Expected 14 points, got {len(new_pts)}"

    # Verify type pattern matches
    old_pts = old_contour.findall("point")
    for i, (_, _, new_type) in enumerate(new_pts):
        old_type = old_pts[i].get("type")
        expected = "line" if new_type == "line" else ("curve" if new_type == "curve" else None)
        # Don't assert - just update

    # Update point positions in existing contour (preserve smooth attrs, etc.)
    for i, (x, y, pt_type) in enumerate(new_pts):
        old_pts[i].set("x", fmt(x))
        old_pts[i].set("y", fmt(y))
        if pt_type is not None:
            old_pts[i].set("type", pt_type)
        elif "type" in old_pts[i].attrib:
            del old_pts[i].attrib["type"]
        # Set smooth on curve points
        if pt_type == "curve":
            old_pts[i].set("smooth", "yes")
        elif "smooth" in old_pts[i].attrib and pt_type != "curve":
            del old_pts[i].attrib["smooth"]

    tree.write(glyph_path, xml_declaration=True, encoding="UTF-8")
    return True


# Radii per weight. These are the actual circle radius in font units.
# Iosevka's i dot: 125x125 = radius 62.5
# For Recursive, the Regular weight is B.
WEIGHT_RADII = {
    "A": 60,    # Light weight
    "B": 125,   # Regular weight
    "C": 150,   # Heavy weight
}


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

                    glyph_path = os.path.join(ufo_path, "glyphs", "dotaccentcomb.glif")
                    if not os.path.exists(glyph_path):
                        continue

                    label = f"{family_name} {style} {weight}{slant}"
                    radius = WEIGHT_RADII[weight]

                    cx, cy = get_contour_center(glyph_path)
                    replace_dotaccentcomb(glyph_path, radius)
                    print(f"  {label}: r={radius} center=({cx:.0f},{cy:.0f})")
                    total += 1

    print(f"\nDone: {total} files updated")


if __name__ == "__main__":
    main()
