#!/usr/bin/env python3
"""
Copy round dot contours from Casual masters to Linear masters.

In Recursive, Linear masters have square dots and Casual masters have round dots.
At CASL=0.5 (SemiCasual), dots interpolate to a halfway shape that looks neither
square nor round. To match Iosevka Charon's round dots at all CASL values,
we copy the Casual dot contour coordinates to the Linear masters.

Affected glyphs:
  - period.glif (used as component by colon, semicolon, exclam, periodcentered)
  - dotaccentcomb.glif (used as component by i, j, and many accented chars)
  - question.glif (contour 0 is the dot, contour 1 is the curve)
  - ellipsis.glif (3 dot contours)
"""

import os
import copy
from xml.etree import ElementTree as ET

SRC_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")
UFO_ROOTS = [os.path.join(SRC_ROOT, "mono"), os.path.join(SRC_ROOT, "sans")]

WEIGHTS = ["A", "B", "C"]
SLANTS = ["", " Slanted"]

# Glyphs where we copy ALL contours from Casual to Linear
FULL_COPY_GLYPHS = ["period.glif", "dotaccentcomb.glif", "ellipsis.glif"]

# Glyphs where we copy only the dot contour (first contour) from Casual to Linear
DOT_CONTOUR_GLYPHS = [("question.glif", 0)]  # (filename, contour_index)


def copy_contour_points(src_contour, dst_contour):
    """Copy point coordinates from src contour to dst contour, preserving point types."""
    src_points = src_contour.findall("point")
    dst_points = dst_contour.findall("point")

    if len(src_points) != len(dst_points):
        raise ValueError(f"Point count mismatch: {len(src_points)} vs {len(dst_points)}")

    for sp, dp in zip(src_points, dst_points):
        dp.set("x", sp.get("x"))
        dp.set("y", sp.get("y"))
        # Preserve type from source too, in case curve vs line differs
        src_type = sp.get("type")
        dst_type = dp.get("type")
        if src_type != dst_type:
            if src_type is not None:
                dp.set("type", src_type)
            elif "type" in dp.attrib:
                del dp.attrib["type"]


def process_glyph(casual_path, linear_path, contour_indices=None):
    """Copy contour points from casual to linear glyph.

    If contour_indices is None, copy all contours.
    Otherwise, only copy the specified contour indices.
    """
    casual_tree = ET.parse(casual_path)
    linear_tree = ET.parse(linear_path)

    casual_contours = casual_tree.getroot().find("outline").findall("contour")
    linear_contours = linear_tree.getroot().find("outline").findall("contour")

    if contour_indices is None:
        contour_indices = range(len(casual_contours))

    for idx in contour_indices:
        copy_contour_points(casual_contours[idx], linear_contours[idx])

    linear_tree.write(linear_path, xml_declaration=True, encoding="UTF-8")
    return True


def main():
    total = 0

    for ufo_root in UFO_ROOTS:
        family = "Mono" if "mono" in ufo_root else "Sans"
        for weight in WEIGHTS:
            for slant in SLANTS:
                casual_ufo = os.path.join(ufo_root, f"Recursive {family}-Casual {weight}{slant}.ufo")
                linear_ufo = os.path.join(ufo_root, f"Recursive {family}-Linear {weight}{slant}.ufo")

                if not os.path.isdir(casual_ufo) or not os.path.isdir(linear_ufo):
                    print(f"  SKIP: Missing UFO for {family} {weight}{slant}")
                    continue

                label = f"{family} {weight}{slant}"

                # Full contour copy glyphs
                for glyph in FULL_COPY_GLYPHS:
                    casual_path = os.path.join(casual_ufo, "glyphs", glyph)
                    linear_path = os.path.join(linear_ufo, "glyphs", glyph)
                    if os.path.exists(casual_path) and os.path.exists(linear_path):
                        process_glyph(casual_path, linear_path)
                        print(f"  {label}: {glyph} -> round dots")
                        total += 1

                # Partial contour copy glyphs (just the dot contour)
                for glyph, contour_idx in DOT_CONTOUR_GLYPHS:
                    casual_path = os.path.join(casual_ufo, "glyphs", glyph)
                    linear_path = os.path.join(linear_ufo, "glyphs", glyph)
                    if os.path.exists(casual_path) and os.path.exists(linear_path):
                        process_glyph(casual_path, linear_path, [contour_idx])
                        print(f"  {label}: {glyph} contour {contour_idx} -> round dot")
                        total += 1

    print(f"\nDone: {total} glyph files updated")


if __name__ == "__main__":
    main()
