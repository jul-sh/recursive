#!/usr/bin/env python3
"""
Apply designspace mono substitution rules to a static instance UFO.

In the variable font, designspace rules substitute .mono glyphs when MONO>=0.5.
For static Mono instances built via ufoProcessor, these substitutions aren't applied.
This script swaps the .mono glyph contours into the base glyph positions.

Usage: python3 scripts/apply_mono_subs.py <instance.ufo>
"""

import os
import shutil
import sys
from xml.etree import ElementTree as ET

# Mono substitutions from the designspace (rule "mono", upright/non-cursive)
MONO_SUBS = {
    "dotlessi": "dotlessi.mono",
    "f": "f.mono",
    "g": "g.mono",
    "i": "i.mono",
    "iacute": "iacute.mono",
    "ibreve": "ibreve.mono",
    "icircumflex": "icircumflex.mono",
    "idieresis": "idieresis.mono",
    "idotaccent": "idotaccent.mono",
    "igrave": "igrave.mono",
    "imacron": "imacron.mono",
    "iogonek": "iogonek.mono",
    "itilde": "itilde.mono",
    "l": "l.mono",
    "ldot": "ldot.mono",
    "lcaron": "lcaron.mono",
    "lacute": "lacute.mono",
    "lslash": "lslash.mono",
    "r": "r.mono",
    "racute": "racute.mono",
    "rcaron": "rcaron.mono",
}

# Additional substitutions to match Iosevka's geometric style.
# Applied AFTER mono subs, so these override .mono with .simple where available.
# The .simple variants have single-story g, simpler f/l/r, etc.
SIMPLE_SUBS = {
    "g": "g.simple",
    "gcircumflex": "gcircumflex.simple",
    "gbreve": "gbreve.simple",
    "gdotaccent": "gdotaccent.simple",
    "gcaron": "gcaron.simple",
    "i": "i.simple",
    "igrave": "igrave.simple",
    "iacute": "iacute.simple",
    "icircumflex": "icircumflex.simple",
    "idieresis": "idieresis.simple",
    "itilde": "itilde.simple",
    "imacron": "imacron.simple",
    "ibreve": "ibreve.simple",
    "iogonek": "iogonek.simple",
    "idotaccent": "idotaccent.simple",
    "l": "l.simple",
    "lacute": "lacute.simple",
    "lcaron": "lcaron.simple",
    "ldot": "ldot.simple",
    "lslash": "lslash.simple",
}


def get_glyph_filename(contents_plist, glyph_name):
    """Get the filename for a glyph from contents.plist."""
    tree = ET.parse(contents_plist)
    root = tree.getroot()
    d = root.find("dict")
    elements = list(d)
    for i in range(0, len(elements), 2):
        if elements[i].tag == "key" and elements[i].text == glyph_name:
            return elements[i + 1].text
    return None


def apply_subs(ufo_path):
    """Replace base glyph contours with .mono variant contours."""
    glyphs_dir = os.path.join(ufo_path, "glyphs")
    contents_plist = os.path.join(glyphs_dir, "contents.plist")

    if not os.path.exists(contents_plist):
        print(f"ERROR: {contents_plist} not found")
        return

    applied = 0
    for base_name, mono_name in MONO_SUBS.items():
        base_file = get_glyph_filename(contents_plist, base_name)
        mono_file = get_glyph_filename(contents_plist, mono_name)

        if not base_file or not mono_file:
            continue

        base_path = os.path.join(glyphs_dir, base_file)
        mono_path = os.path.join(glyphs_dir, mono_file)

        if not os.path.exists(mono_path):
            continue

        # Read mono glyph
        mono_tree = ET.parse(mono_path)
        mono_root = mono_tree.getroot()

        # Read base glyph
        base_tree = ET.parse(base_path)
        base_root = base_tree.getroot()

        # Copy outline from mono to base
        mono_outline = mono_root.find("outline")
        base_outline = base_root.find("outline")

        if mono_outline is not None and base_outline is not None:
            # Replace base outline with mono outline
            base_root.remove(base_outline)
            base_root.append(mono_outline)

            # Also copy advance width if present
            mono_advance = mono_root.find("advance")
            base_advance = base_root.find("advance")
            if mono_advance is not None and base_advance is not None:
                base_advance.set("width", mono_advance.get("width", "500"))

            base_tree.write(base_path, xml_declaration=True, encoding="UTF-8")
            applied += 1

    # Apply simple subs (override mono with simpler forms for Iosevka-like style)
    simple_applied = 0
    for base_name, simple_name in SIMPLE_SUBS.items():
        base_file = get_glyph_filename(contents_plist, base_name)
        simple_file = get_glyph_filename(contents_plist, simple_name)

        if not base_file or not simple_file:
            continue

        base_path = os.path.join(glyphs_dir, base_file)
        simple_path = os.path.join(glyphs_dir, simple_file)

        if not os.path.exists(simple_path):
            continue

        simple_tree = ET.parse(simple_path)
        simple_root = simple_tree.getroot()

        base_tree = ET.parse(base_path)
        base_root = base_tree.getroot()

        simple_outline = simple_root.find("outline")
        base_outline = base_root.find("outline")

        if simple_outline is not None and base_outline is not None:
            base_root.remove(base_outline)
            base_root.append(simple_outline)

            simple_advance = simple_root.find("advance")
            base_advance = base_root.find("advance")
            if simple_advance is not None and base_advance is not None:
                base_advance.set("width", simple_advance.get("width", "500"))

            base_tree.write(base_path, xml_declaration=True, encoding="UTF-8")
            simple_applied += 1

    print(f"  Applied {applied} mono + {simple_applied} simple substitutions to {os.path.basename(ufo_path)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/apply_mono_subs.py <instance.ufo>")
        sys.exit(1)
    apply_subs(sys.argv[1])
