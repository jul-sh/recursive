#!/usr/bin/env python3
"""
Transform Recursive UFO sources to match Iosevka Charon's construction and proportions.

Target metrics (Iosevka Charon, 1000 UPM):
  - Mono cell width: 500 (vs Recursive's 600)
  - Cap height: 735
  - x-height: 520
  - Ascender: 735 (= cap height)
  - Descender: -215
  - Stroke at Regular: ~70 (handled by weight axis, not transformed here)

Strategy:
  1. Horizontal compression: scale all x-coordinates by 0.8333 (500/600)
     to match Iosevka's narrow character cell.
  2. Vertical re-proportioning: apply a piecewise vertical scale that maps:
     - baseline (0) stays at 0
     - x-height zone: current x-height -> 520
     - cap height zone: current cap height (700) -> 735
     - ascender: current ascender (750) -> 735 (compressed above cap)
     - descender: current descender (-250) -> -215
  3. Update all fontinfo.plist metrics to match new proportions.
  4. Scale anchors, kerning, and all layers.
"""

import os
import sys
import glob
import copy
import plistlib
import re
import math
from pathlib import Path
from xml.etree import ElementTree as ET


# === CONFIGURATION ===

# Horizontal scale factor: Iosevka cell width / Recursive cell width
H_SCALE = 500.0 / 600.0  # 0.8333

# Target vertical metrics (Iosevka Charon)
TARGET_CAP_HEIGHT = 735
TARGET_ASCENDER = 735
TARGET_DESCENDER = -215

# Iosevka x-height is 520, but we use per-master targets since Recursive
# varies x-height by weight (A=526, B=540, C=550).
# We'll compute a per-master x-height target that preserves Iosevka's x/cap ratio.
IOSEVKA_X_CAP_RATIO = 520.0 / 735.0  # 0.7075

# Source vertical metrics (Recursive, consistent across masters)
SRC_CAP_HEIGHT = 700
SRC_ASCENDER = 750

SRC_DESCENDER = -250

# Root of UFO sources
UFO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")


def compute_vertical_scale_params(src_xheight):
    """
    Compute piecewise vertical scaling parameters for a given master.

    We define 4 zones with linear scaling:
      1. Below descender: extrapolate from descender zone
      2. Descender to baseline: scale descender zone
      3. Baseline to cap height: scale based on cap ratio
      4. Cap height to ascender: compress to match Iosevka's ascender=cap

    Returns a function that maps old y -> new y.
    """
    target_xheight = round(TARGET_CAP_HEIGHT * IOSEVKA_X_CAP_RATIO)  # 520

    # Key control points (old_y -> new_y)
    control_points = [
        (SRC_DESCENDER, TARGET_DESCENDER),       # -250 -> -215
        (0, 0),                                     # baseline stays
        (src_xheight, target_xheight),              # x-height maps
        (SRC_CAP_HEIGHT, TARGET_CAP_HEIGHT),        # 700 -> 735
        (SRC_ASCENDER, TARGET_ASCENDER),            # 750 -> 735
    ]

    def scale_y(y):
        # Find which segment this y falls in
        if y <= control_points[0][0]:
            # Below descender: extrapolate from descender-baseline segment
            old_range = control_points[1][0] - control_points[0][0]
            new_range = control_points[1][1] - control_points[0][1]
            ratio = new_range / old_range if old_range != 0 else 1.0
            return control_points[0][1] + (y - control_points[0][0]) * ratio

        for i in range(len(control_points) - 1):
            old_lo, new_lo = control_points[i]
            old_hi, new_hi = control_points[i + 1]
            if y <= old_hi:
                if old_hi == old_lo:
                    return new_lo
                t = (y - old_lo) / (old_hi - old_lo)
                return new_lo + t * (new_hi - new_lo)

        # Above ascender: extrapolate from cap-ascender segment
        old_lo, new_lo = control_points[-2]
        old_hi, new_hi = control_points[-1]
        old_range = old_hi - old_lo
        new_range = new_hi - new_lo
        ratio = new_range / old_range if old_range != 0 else 1.0
        return new_hi + (y - old_hi) * ratio

    return scale_y


def transform_glif_file(glif_path, h_scale, scale_y_func):
    """Transform a single .glif file: scale outlines, anchors, guidelines, advance width."""
    try:
        tree = ET.parse(glif_path)
    except ET.ParseError:
        print(f"  WARNING: Could not parse {glif_path}, skipping")
        return False

    root = tree.getroot()
    modified = False

    # Scale advance width (horizontal only)
    advance = root.find("advance")
    if advance is not None:
        width = advance.get("width")
        if width is not None:
            new_width = round(float(width) * h_scale)
            advance.set("width", str(new_width))
            modified = True
        height = advance.get("height")
        if height is not None:
            new_height = round(scale_y_func(float(height)))
            advance.set("height", str(new_height))
            modified = True

    # Scale outline points
    for outline in root.findall("outline"):
        for contour in outline.findall("contour"):
            for point in contour.findall("point"):
                x = point.get("x")
                y = point.get("y")
                if x is not None:
                    old_x = float(x)
                    new_x = round(old_x * h_scale, 4)
                    # Clean up trailing zeros
                    if new_x == int(new_x):
                        point.set("x", str(int(new_x)))
                    else:
                        point.set("x", str(new_x))
                    modified = True
                if y is not None:
                    old_y = float(y)
                    new_y = round(scale_y_func(old_y), 4)
                    if new_y == int(new_y):
                        point.set("y", str(int(new_y)))
                    else:
                        point.set("y", str(new_y))
                    modified = True

        # Scale components
        for component in outline.findall("component"):
            # Component offsets
            x_offset = component.get("xOffset")
            y_offset = component.get("yOffset")
            if x_offset is not None:
                new_xo = round(float(x_offset) * h_scale, 4)
                if new_xo == int(new_xo):
                    component.set("xOffset", str(int(new_xo)))
                else:
                    component.set("xOffset", str(new_xo))
                modified = True
            if y_offset is not None:
                new_yo = round(scale_y_func(float(y_offset)), 4)
                if new_yo == int(new_yo):
                    component.set("yOffset", str(int(new_yo)))
                else:
                    component.set("yOffset", str(new_yo))
                modified = True

            # Component scale values
            x_scale = component.get("xScale")
            y_scale = component.get("yScale")
            # xScale and yScale are multipliers, not coordinates - leave as-is
            # But if there's a xyScale or yxScale (shear), adjust
            # These are transformation matrix entries, not positional

    # Scale anchors
    for anchor in root.findall("anchor"):
        x = anchor.get("x")
        y = anchor.get("y")
        if x is not None:
            old_x = float(x)
            new_x = round(old_x * h_scale, 4)
            if new_x == int(new_x):
                anchor.set("x", str(int(new_x)))
            else:
                anchor.set("x", str(new_x))
            modified = True
        if y is not None:
            old_y = float(y)
            new_y = round(scale_y_func(old_y), 4)
            if new_y == int(new_y):
                anchor.set("y", str(int(new_y)))
            else:
                anchor.set("y", str(new_y))
            modified = True

    # Scale guidelines in the glyph
    for guideline in root.findall("guideline"):
        x = guideline.get("x")
        y = guideline.get("y")
        if x is not None:
            old_x = float(x)
            new_x = round(old_x * h_scale, 4)
            if new_x == int(new_x):
                guideline.set("x", str(int(new_x)))
            else:
                guideline.set("x", str(new_x))
            modified = True
        if y is not None:
            old_y = float(y)
            new_y = round(scale_y_func(old_y), 4)
            if new_y == int(new_y):
                guideline.set("y", str(int(new_y)))
            else:
                guideline.set("y", str(new_y))
            modified = True

    if modified:
        tree.write(glif_path, xml_declaration=True, encoding="UTF-8")

    return modified


def transform_layer(layer_dir, h_scale, scale_y_func):
    """Transform all .glif files in a layer directory."""
    glif_files = glob.glob(os.path.join(layer_dir, "*.glif"))
    count = 0
    for glif_path in glif_files:
        if transform_glif_file(glif_path, h_scale, scale_y_func):
            count += 1
    return count


def get_master_xheight(fontinfo_path):
    """Read x-height from fontinfo.plist."""
    with open(fontinfo_path, "rb") as f:
        info = plistlib.load(f)
    return info.get("xHeight", 540)


def update_fontinfo(fontinfo_path, scale_y_func):
    """Update fontinfo.plist with new metrics."""
    with open(fontinfo_path, "rb") as f:
        info = plistlib.load(f)

    src_xheight = info.get("xHeight", 540)
    target_xheight = round(TARGET_CAP_HEIGHT * IOSEVKA_X_CAP_RATIO)  # 520

    # Core vertical metrics
    info["xHeight"] = target_xheight
    info["capHeight"] = TARGET_CAP_HEIGHT
    info["ascender"] = TARGET_ASCENDER
    info["descender"] = TARGET_DESCENDER

    # OpenType vertical metrics
    # Hhea metrics: scale proportionally
    info["openTypeHheaAscender"] = round(scale_y_func(info.get("openTypeHheaAscender", 950)))
    info["openTypeHheaDescender"] = round(scale_y_func(info.get("openTypeHheaDescender", -250)))
    info["openTypeHheaLineGap"] = info.get("openTypeHheaLineGap", 0)

    # OS/2 Typo metrics
    info["openTypeOS2TypoAscender"] = round(scale_y_func(info.get("openTypeOS2TypoAscender", 950)))
    info["openTypeOS2TypoDescender"] = round(scale_y_func(info.get("openTypeOS2TypoDescender", -250)))
    info["openTypeOS2TypoLineGap"] = info.get("openTypeOS2TypoLineGap", 0)

    # Win metrics (used for clipping)
    info["openTypeOS2WinAscent"] = round(scale_y_func(info.get("openTypeOS2WinAscent", 1207)))
    info["openTypeOS2WinDescent"] = abs(round(scale_y_func(-info.get("openTypeOS2WinDescent", 271))))

    # Strikeout and underline (vertical positions need scaling)
    if "openTypeOS2StrikeoutPosition" in info:
        info["openTypeOS2StrikeoutPosition"] = round(scale_y_func(info["openTypeOS2StrikeoutPosition"]))
    if "openTypeOS2StrikeoutSize" in info:
        # Size is a thickness, scale by average vertical factor around that zone
        pos = info.get("openTypeOS2StrikeoutPosition", 300)
        size = info["openTypeOS2StrikeoutSize"]
        new_top = scale_y_func(pos + size / 2)
        new_bot = scale_y_func(pos - size / 2)
        info["openTypeOS2StrikeoutSize"] = round(abs(new_top - new_bot))

    if "postscriptUnderlinePosition" in info:
        info["postscriptUnderlinePosition"] = round(scale_y_func(info["postscriptUnderlinePosition"]))
    if "postscriptUnderlineThickness" in info:
        # Scale thickness by descender zone ratio
        thickness = info["postscriptUnderlineThickness"]
        pos = info.get("postscriptUnderlinePosition", -175)
        new_top = scale_y_func(pos + thickness / 2)
        new_bot = scale_y_func(pos - thickness / 2)
        info["postscriptUnderlineThickness"] = round(abs(new_top - new_bot))

    # PostScript blue values (alignment zones)
    if "postscriptBlueValues" in info:
        blues = info["postscriptBlueValues"]
        info["postscriptBlueValues"] = [round(scale_y_func(v)) for v in blues]

    if "postscriptOtherBlues" in info:
        other_blues = info["postscriptOtherBlues"]
        info["postscriptOtherBlues"] = [round(scale_y_func(v)) for v in other_blues]

    # Stem snap values: horizontal stems scale by H_SCALE, vertical stems stay
    if "postscriptStemSnapH" in info:
        info["postscriptStemSnapH"] = [round(v * H_SCALE) for v in info["postscriptStemSnapH"]]

    # Vertical stems: scale by vertical factor around x-height midpoint
    if "postscriptStemSnapV" in info:
        mid = src_xheight / 2
        v_factor = (scale_y_func(mid + 50) - scale_y_func(mid - 50)) / 100.0
        info["postscriptStemSnapV"] = [round(v * v_factor) for v in info["postscriptStemSnapV"]]

    # Guidelines
    if "guidelines" in info:
        for gl in info["guidelines"]:
            if "x" in gl:
                gl["x"] = round(gl["x"] * H_SCALE)
            if "y" in gl:
                gl["y"] = round(scale_y_func(gl["y"]))

    with open(fontinfo_path, "wb") as f:
        plistlib.dump(info, f, sort_keys=True)


def update_kerning(kerning_path, h_scale):
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
                pairs[second_glyph] = round(value * h_scale)
                count += 1

    with open(kerning_path, "wb") as f:
        plistlib.dump(kerning, f, sort_keys=True)

    return count


def process_ufo(ufo_path):
    """Process a single UFO master: transform all layers, update metrics, scale kerning."""
    ufo_name = os.path.basename(ufo_path)
    print(f"\nProcessing: {ufo_name}")

    fontinfo_path = os.path.join(ufo_path, "fontinfo.plist")
    if not os.path.exists(fontinfo_path):
        print(f"  ERROR: No fontinfo.plist found, skipping")
        return

    # Get this master's x-height for vertical scaling
    src_xheight = get_master_xheight(fontinfo_path)
    print(f"  Source x-height: {src_xheight}")

    # Build the vertical scale function for this master
    scale_y_func = compute_vertical_scale_params(src_xheight)

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
        count = transform_layer(layer_dir, H_SCALE, scale_y_func)
        print(f"  Layer '{layer_name}' ({layer_dir_name}): {count} glyphs transformed")
        total_glyphs += count

    # Update fontinfo.plist
    update_fontinfo(fontinfo_path, scale_y_func)
    print(f"  Updated fontinfo.plist")

    # Scale kerning
    kerning_path = os.path.join(ufo_path, "kerning.plist")
    kern_count = update_kerning(kerning_path, H_SCALE)
    if kern_count > 0:
        print(f"  Scaled {kern_count} kerning pairs")

    print(f"  Total: {total_glyphs} glyphs across all layers")


def update_designspace(ds_path):
    """Update designspace file metrics if needed."""
    print(f"\nUpdating designspace: {os.path.basename(ds_path)}")
    tree = ET.parse(ds_path)
    root = tree.getroot()

    # The designspace references sources by filename, which don't change.
    # But we may need to update any default values or rules that reference
    # coordinate positions.

    # Check for any <dimension> or <location> elements with coordinate values
    # These typically reference axis positions, not glyph coordinates, so
    # they should stay the same.

    tree.write(ds_path, xml_declaration=True, encoding="UTF-8")
    print(f"  Designspace preserved (axis positions unchanged)")


def main():
    print("=" * 70)
    print("Recursive -> Iosevka Charon Proportion Transform")
    print("=" * 70)
    print(f"\nHorizontal scale: {H_SCALE:.4f} (600 -> 500 unit width)")
    print(f"Target cap height: {TARGET_CAP_HEIGHT}")
    print(f"Target x-height: {round(TARGET_CAP_HEIGHT * IOSEVKA_X_CAP_RATIO)}")
    print(f"Target ascender: {TARGET_ASCENDER}")
    print(f"Target descender: {TARGET_DESCENDER}")
    print()

    # Find all UFO masters
    mono_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")))
    sans_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo")))

    all_ufos = mono_ufos + sans_ufos
    print(f"Found {len(all_ufos)} UFO masters ({len(mono_ufos)} mono, {len(sans_ufos)} sans)")

    # Process each UFO
    for ufo_path in all_ufos:
        process_ufo(ufo_path)

    # Update designspace files
    ds_files = glob.glob(os.path.join(UFO_ROOT, "*.designspace"))
    ds_files += glob.glob(os.path.join(UFO_ROOT, "mono", "*.designspace"))
    ds_files += glob.glob(os.path.join(UFO_ROOT, "sans", "*.designspace"))
    for ds_path in ds_files:
        update_designspace(ds_path)

    print("\n" + "=" * 70)
    print("Transform complete!")
    print(f"  Horizontal scale applied: {H_SCALE:.4f}")
    print(f"  Mono advance width: 600 -> {round(600 * H_SCALE)}")
    print(f"  Vertical metrics updated to match Iosevka Charon")
    print("=" * 70)


if __name__ == "__main__":
    main()
