#!/usr/bin/env python3
"""
Transform Recursive UFO sources to match Iosevka Charon's width.

Target: Mono cell width 500 (vs Recursive's 600), scale factor 0.8333.

This script ONLY adjusts horizontal width:
  - Scale all x-coordinates by 500/600
  - Scale advance widths
  - Scale component x-offsets
  - Scale anchor x-positions
  - Scale guideline x-positions
  - Scale kerning values
  - Update postscriptStemSnapH (horizontal stems)

Vertical metrics, y-coordinates, and all other vertical values are LEFT UNTOUCHED.
"""

import os
import sys
import glob
import plistlib
from pathlib import Path
from xml.etree import ElementTree as ET


# === CONFIGURATION ===

# Horizontal scale factor: Iosevka cell width / Recursive cell width
H_SCALE = 500.0 / 600.0  # 0.8333

# Root of UFO sources
UFO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")


def fmt(value):
    """Format a number: integer if whole, otherwise up to 4 decimals."""
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))
    return str(rounded)


def transform_glif_file(glif_path, h_scale):
    """Transform a single .glif file: scale x-coordinates and advance width only."""
    try:
        tree = ET.parse(glif_path)
    except ET.ParseError:
        print(f"  WARNING: Could not parse {glif_path}, skipping")
        return False

    root = tree.getroot()
    modified = False

    # Scale advance width
    advance = root.find("advance")
    if advance is not None:
        width = advance.get("width")
        if width is not None:
            advance.set("width", str(round(float(width) * h_scale)))
            modified = True

    # Scale outline point x-coordinates
    for outline in root.findall("outline"):
        for contour in outline.findall("contour"):
            for point in contour.findall("point"):
                x = point.get("x")
                if x is not None:
                    point.set("x", fmt(float(x) * h_scale))
                    modified = True

        # Scale component x-offsets
        for component in outline.findall("component"):
            x_offset = component.get("xOffset")
            if x_offset is not None:
                component.set("xOffset", fmt(float(x_offset) * h_scale))
                modified = True

    # Scale anchor x-positions
    for anchor in root.findall("anchor"):
        x = anchor.get("x")
        if x is not None:
            anchor.set("x", fmt(float(x) * h_scale))
            modified = True

    # Scale guideline x-positions
    for guideline in root.findall("guideline"):
        x = guideline.get("x")
        if x is not None:
            guideline.set("x", fmt(float(x) * h_scale))
            modified = True

    if modified:
        tree.write(glif_path, xml_declaration=True, encoding="UTF-8")

    return modified


def transform_layer(layer_dir, h_scale):
    """Transform all .glif files in a layer directory."""
    glif_files = glob.glob(os.path.join(layer_dir, "*.glif"))
    count = 0
    for glif_path in glif_files:
        if transform_glif_file(glif_path, h_scale):
            count += 1
    return count


def update_fontinfo(fontinfo_path):
    """Update only horizontal metrics in fontinfo.plist."""
    with open(fontinfo_path, "rb") as f:
        info = plistlib.load(f)

    # Scale horizontal stem snaps only
    if "postscriptStemSnapH" in info:
        info["postscriptStemSnapH"] = [round(v * H_SCALE) for v in info["postscriptStemSnapH"]]

    # Scale horizontal guidelines
    if "guidelines" in info:
        for gl in info["guidelines"]:
            if "x" in gl:
                gl["x"] = round(gl["x"] * H_SCALE)

    with open(fontinfo_path, "wb") as f:
        plistlib.dump(info, f, sort_keys=True)


def update_kerning(kerning_path):
    """Scale all kerning values by horizontal scale factor."""
    if not os.path.exists(kerning_path):
        return 0

    with open(kerning_path, "rb") as f:
        kerning = plistlib.load(f)

    if not kerning:
        return 0

    count = 0
    for first_glyph, pairs in kerning.items():
        for second_glyph, value in pairs.items():
            if isinstance(value, (int, float)):
                pairs[second_glyph] = round(value * H_SCALE)
                count += 1

    with open(kerning_path, "wb") as f:
        plistlib.dump(kerning, f, sort_keys=True)

    return count


def process_ufo(ufo_path):
    """Process a single UFO master: scale widths across all layers."""
    ufo_name = os.path.basename(ufo_path)
    print(f"\nProcessing: {ufo_name}")

    fontinfo_path = os.path.join(ufo_path, "fontinfo.plist")
    if not os.path.exists(fontinfo_path):
        print(f"  ERROR: No fontinfo.plist found, skipping")
        return

    # Read layer contents to find all glyph layers
    layercontents_path = os.path.join(ufo_path, "layercontents.plist")
    if os.path.exists(layercontents_path):
        with open(layercontents_path, "rb") as f:
            layers = plistlib.load(f)
    else:
        layers = [["foreground", "glyphs"]]

    # Transform each layer
    total_glyphs = 0
    for layer_name, layer_dir_name in layers:
        layer_dir = os.path.join(ufo_path, layer_dir_name)
        if not os.path.isdir(layer_dir):
            continue
        count = transform_layer(layer_dir, H_SCALE)
        print(f"  Layer '{layer_name}' ({layer_dir_name}): {count} glyphs transformed")
        total_glyphs += count

    # Update fontinfo.plist (horizontal metrics only)
    update_fontinfo(fontinfo_path)
    print(f"  Updated fontinfo.plist (horizontal metrics only)")

    # Scale kerning
    kerning_path = os.path.join(ufo_path, "kerning.plist")
    kern_count = update_kerning(kerning_path)
    if kern_count > 0:
        print(f"  Scaled {kern_count} kerning pairs")

    print(f"  Total: {total_glyphs} glyphs across all layers")


def main():
    print("=" * 70)
    print("Recursive -> Iosevka Charon Width Transform")
    print("=" * 70)
    print(f"\nHorizontal scale: {H_SCALE:.4f} (600 -> 500 unit width)")
    print(f"Vertical metrics: UNCHANGED")
    print()

    # Find all UFO masters
    mono_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")))
    sans_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo")))

    all_ufos = mono_ufos + sans_ufos
    print(f"Found {len(all_ufos)} UFO masters ({len(mono_ufos)} mono, {len(sans_ufos)} sans)")

    for ufo_path in all_ufos:
        process_ufo(ufo_path)

    print("\n" + "=" * 70)
    print("Transform complete!")
    print(f"  Horizontal scale applied: {H_SCALE:.4f}")
    print(f"  Mono advance width: 600 -> {round(600 * H_SCALE)}")
    print(f"  Vertical metrics: UNCHANGED")
    print("=" * 70)


if __name__ == "__main__":
    main()
