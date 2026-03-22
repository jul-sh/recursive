#!/usr/bin/env python3
"""
Swap italic glyph outlines into base glyphs for specified characters and their accented forms.

For each target character and its accented variants, this script:
1. Reads the .italic.glif file (italic letterform shape)
2. Copies its <outline> and <anchor> elements into the base .glif file
3. Preserves the base glyph's name, unicode, advance width, and lib metadata
4. Makes the .italic.glif have the same outline (substitution becomes no-op)
"""

import os
import sys
import xml.etree.ElementTree as ET
import glob
import copy
import re

# Base characters to swap
TARGET_CHARS = ['a', 's', 'g', 'h', 'j', 'k', 'z', 'x', 'c', 'n', 'm', 'y']

# Find all UFO directories
UFO_DIRS = []
for pattern in ['src/ufo/mono/*.ufo', 'src/ufo/sans/*.ufo']:
    UFO_DIRS.extend(sorted(glob.glob(pattern)))


def find_all_italic_variants(ufo_dir):
    """Find all .italic.glif files that correspond to target chars or their accented forms."""
    glyphs_dir = os.path.join(ufo_dir, 'glyphs')
    variants = []

    for italic_file in sorted(glob.glob(os.path.join(glyphs_dir, '*.italic.glif'))):
        basename = os.path.basename(italic_file)
        # Extract the glyph name without .italic.glif
        glyph_name = basename.replace('.italic.glif', '')

        # Check if this is one of our target chars or an accented variant
        for tc in TARGET_CHARS:
            if glyph_name == tc or (glyph_name.startswith(tc) and len(glyph_name) > len(tc)):
                # Make sure it's not a false match (e.g., "zero" starting with "z")
                if glyph_name == tc:
                    variants.append(glyph_name)
                    break
                # For accented forms, verify the suffix looks like an accent
                suffix = glyph_name[len(tc):]
                # The suffix should start with a lowercase letter (accent name)
                if suffix[0].islower():
                    variants.append(glyph_name)
                    break

    return variants


def swap_glyph(ufo_dir, glyph_name):
    """Copy outline from glyph_name.italic.glif into glyph_name.glif."""
    base_path = os.path.join(ufo_dir, 'glyphs', f'{glyph_name}.glif')
    italic_path = os.path.join(ufo_dir, 'glyphs', f'{glyph_name}.italic.glif')

    if not os.path.exists(base_path):
        return False
    if not os.path.exists(italic_path):
        return False

    # Parse both files
    base_tree = ET.parse(base_path)
    italic_tree = ET.parse(italic_path)
    base_root = base_tree.getroot()
    italic_root = italic_tree.getroot()

    # Remove existing outline and anchors from base
    for elem in base_root.findall('outline'):
        base_root.remove(elem)
    for elem in base_root.findall('anchor'):
        base_root.remove(elem)

    # Copy outline and anchors from italic to base
    lib_elem = base_root.find('lib')
    insert_idx = list(base_root).index(lib_elem) if lib_elem is not None else len(list(base_root))

    for elem in italic_root.findall('outline'):
        base_root.insert(insert_idx, copy.deepcopy(elem))
        insert_idx += 1
    for elem in italic_root.findall('anchor'):
        base_root.insert(insert_idx, copy.deepcopy(elem))
        insert_idx += 1

    # Write back
    base_tree.write(base_path, xml_declaration=True, encoding='UTF-8')

    # Now make the italic file have the same outline
    for elem in italic_root.findall('outline'):
        italic_root.remove(elem)
    for elem in italic_root.findall('anchor'):
        italic_root.remove(elem)

    italic_lib = italic_root.find('lib')
    italic_insert_idx = list(italic_root).index(italic_lib) if italic_lib is not None else len(list(italic_root))

    for elem in base_root.findall('outline'):
        italic_root.insert(italic_insert_idx, copy.deepcopy(elem))
        italic_insert_idx += 1
    for elem in base_root.findall('anchor'):
        italic_root.insert(italic_insert_idx, copy.deepcopy(elem))
        italic_insert_idx += 1

    italic_tree.write(italic_path, xml_declaration=True, encoding='UTF-8')

    return True


def main():
    total = 0
    # First, discover all variants from the first UFO
    sample_variants = find_all_italic_variants(UFO_DIRS[0])
    print(f"Found {len(sample_variants)} italic variants to swap")

    for ufo_dir in UFO_DIRS:
        ufo_name = os.path.basename(ufo_dir)
        variants = find_all_italic_variants(ufo_dir)
        for glyph_name in variants:
            if swap_glyph(ufo_dir, glyph_name):
                total += 1

    print(f"\nSwapped {total} glyphs across {len(UFO_DIRS)} UFOs")


if __name__ == '__main__':
    main()
