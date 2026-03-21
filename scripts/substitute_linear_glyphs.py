#!/usr/bin/env python3
"""
Substitute Linear A outlines into Casual A for specific glyphs.
Preserves the Casual A glyph metadata (unicode, advance, anchors, lib).
"""

import os
import sys
from xml.etree import ElementTree as ET


# Glyphs to substitute from Linear A into Casual A
SUBSTITUTE_GLYPHS = ['S_.glif', 'e.glif', 'g.glif', 'g.mono.glif']


def substitute_outline(linear_glif, casual_glif):
    """Copy outline from linear glif into casual glif, preserving metadata."""
    linear_tree = ET.parse(linear_glif)
    casual_tree = ET.parse(casual_glif)

    linear_root = linear_tree.getroot()
    casual_root = casual_tree.getroot()

    # Get the linear outline
    linear_outline = linear_root.find('outline')
    if linear_outline is None:
        print(f"  No outline in {linear_glif}")
        return False

    # Remove the casual outline
    casual_outline = casual_root.find('outline')
    if casual_outline is not None:
        casual_root.remove(casual_outline)

    # Insert the linear outline at the correct position
    # (after advance, before anchor/lib)
    insert_idx = 0
    for i, child in enumerate(casual_root):
        if child.tag in ('unicode', 'advance'):
            insert_idx = i + 1
    casual_root.insert(insert_idx, linear_outline)

    casual_tree.write(casual_glif, xml_declaration=True, encoding='UTF-8')
    return True


def main():
    base = 'src/ufo'

    for category in ['mono', 'sans']:
        casual_dir = os.path.join(base, category, f'Recursive {"Mono" if category == "mono" else "Sans"}-Casual A.ufo', 'glyphs')
        linear_dir = os.path.join(base, category, f'Recursive {"Mono" if category == "mono" else "Sans"}-Linear A.ufo', 'glyphs')

        if not os.path.exists(casual_dir) or not os.path.exists(linear_dir):
            continue

        print(f"\n{os.path.basename(os.path.dirname(casual_dir))}:")

        for glif_name in SUBSTITUTE_GLYPHS:
            casual_path = os.path.join(casual_dir, glif_name)
            linear_path = os.path.join(linear_dir, glif_name)

            if not os.path.exists(casual_path):
                print(f"  {glif_name}: casual not found")
                continue
            if not os.path.exists(linear_path):
                print(f"  {glif_name}: linear not found")
                continue

            if substitute_outline(linear_path, casual_path):
                print(f"  {glif_name}: substituted Linear A outline")


if __name__ == '__main__':
    main()
