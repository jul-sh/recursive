#!/usr/bin/env python3
"""
Remove decorative second contours (tabs) from capital L and Z.

- L: has a tab at the bottom-right end of its horizontal bar (second contour)
- Z: has a collapsed flag element at top-left (second contour, already mostly
  flattened but still renders as a tiny artifact)

This script removes the second contour from both glyphs in all UFO masters.
"""

import os
import glob
import plistlib
from xml.etree import ElementTree as ET

GLYPH_FILES = ["L_.glif", "Z_.glif"]

UFO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")


def fix_glyph(glif_path):
    """Remove the second (decorative) contour from a glyph."""
    try:
        tree = ET.parse(glif_path)
    except ET.ParseError:
        print(f"  WARNING: Could not parse {glif_path}, skipping")
        return False

    root = tree.getroot()

    for outline in root.findall("outline"):
        contours = outline.findall("contour")
        if len(contours) < 2:
            print(f"  {os.path.basename(glif_path)}: only {len(contours)} contour(s), skipping")
            return False

        # Remove the second contour (index 1) - it's the decorative tab
        outline.remove(contours[1])
        print(f"  Removed second contour from {os.path.basename(glif_path)}")

    tree.write(glif_path, xml_declaration=True, encoding="UTF-8")
    return True


def process_ufo(ufo_path):
    """Process a single UFO master."""
    ufo_name = os.path.basename(ufo_path)
    print(f"\n{ufo_name}:")

    glyph_dirs = [os.path.join(ufo_path, "glyphs")]

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
                if fix_glyph(glif_path):
                    total_fixed += 1

    return total_fixed


def main():
    print("=" * 70)
    print("Fix L and Z tabs: remove decorative second contours")
    print("=" * 70)

    mono_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")))
    sans_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo")))
    all_ufos = mono_ufos + sans_ufos

    print(f"\nFound {len(all_ufos)} UFO masters ({len(mono_ufos)} mono, {len(sans_ufos)} sans)")

    total = 0
    for ufo_path in all_ufos:
        total += process_ufo(ufo_path)

    print(f"\n{'=' * 70}")
    print(f"Done! Removed tabs from {total} glyph files.")
    print("=" * 70)


if __name__ == "__main__":
    main()
