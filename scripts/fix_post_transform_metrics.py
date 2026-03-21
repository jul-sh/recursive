#!/usr/bin/env python3
"""
Fix post-transform metric issues in UFO masters:
1. Blue value zones: pairs must have distinct values (no zero-width zones)
2. hhea/typo ascender: must be high enough for accented characters
3. WinAscent/WinDescent: must encompass all glyphs including accents
"""

import os
import glob
import plistlib
from pathlib import Path

UFO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")

# Iosevka uses leading=1250, so total line height = 1250
# With cap=735, ascender=735, descender=-215, total glyph range = 950
# Line gap should be 1250 - 950 = 300, split as extra ascender space
# For accented chars, we need headroom above 735
HHEA_ASCENDER = 935   # 735 + 200 for tall accents/stacking marks
HHEA_DESCENDER = -215
TYPO_ASCENDER = 935
TYPO_DESCENDER = -215
WIN_ASCENT = 1050     # Conservative, covers tallest stacked accents
WIN_DESCENT = 250     # Covers deepest descenders + subscripts


def fix_blue_values(values):
    """Fix blue value pairs to ensure each pair has distinct bottom/top."""
    if not values or len(values) < 2:
        return values

    fixed = list(values)
    # Blue values come in pairs: [bottom, top, bottom, top, ...]
    for i in range(0, len(fixed) - 1, 2):
        if fixed[i] == fixed[i + 1]:
            # Zero-width zone - add minimum overshoot
            fixed[i + 1] = fixed[i] + 10
    return fixed


def fix_fontinfo(fontinfo_path):
    """Fix metrics issues in a fontinfo.plist."""
    with open(fontinfo_path, "rb") as f:
        info = plistlib.load(f)

    name = info.get("styleName", "unknown")
    changes = []

    # Fix hhea metrics
    if info.get("openTypeHheaAscender") != HHEA_ASCENDER:
        info["openTypeHheaAscender"] = HHEA_ASCENDER
        changes.append(f"hheaAscender -> {HHEA_ASCENDER}")
    if info.get("openTypeHheaDescender") != HHEA_DESCENDER:
        info["openTypeHheaDescender"] = HHEA_DESCENDER
        changes.append(f"hheaDescender -> {HHEA_DESCENDER}")

    # Fix typo metrics
    if info.get("openTypeOS2TypoAscender") != TYPO_ASCENDER:
        info["openTypeOS2TypoAscender"] = TYPO_ASCENDER
        changes.append(f"typoAscender -> {TYPO_ASCENDER}")
    if info.get("openTypeOS2TypoDescender") != TYPO_DESCENDER:
        info["openTypeOS2TypoDescender"] = TYPO_DESCENDER
        changes.append(f"typoDescender -> {TYPO_DESCENDER}")

    # Fix Win metrics
    if info.get("openTypeOS2WinAscent") != WIN_ASCENT:
        info["openTypeOS2WinAscent"] = WIN_ASCENT
        changes.append(f"winAscent -> {WIN_ASCENT}")
    if info.get("openTypeOS2WinDescent") != WIN_DESCENT:
        info["openTypeOS2WinDescent"] = WIN_DESCENT
        changes.append(f"winDescent -> {WIN_DESCENT}")

    # Fix blue values
    if "postscriptBlueValues" in info:
        old_blues = list(info["postscriptBlueValues"])
        fixed_blues = fix_blue_values(old_blues)
        if fixed_blues != old_blues:
            info["postscriptBlueValues"] = fixed_blues
            changes.append(f"blueValues: {old_blues} -> {fixed_blues}")

    if "postscriptOtherBlues" in info:
        old_other = list(info["postscriptOtherBlues"])
        fixed_other = fix_blue_values(old_other)
        if fixed_other != old_other:
            info["postscriptOtherBlues"] = fixed_other
            changes.append(f"otherBlues: {old_other} -> {fixed_other}")

    if changes:
        with open(fontinfo_path, "wb") as f:
            plistlib.dump(info, f, sort_keys=True)
        print(f"  {name}: {', '.join(changes)}")
    else:
        print(f"  {name}: no fixes needed")


def main():
    print("Fixing post-transform metrics...")
    print()

    mono_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")))
    sans_ufos = sorted(glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo")))

    for ufo_path in mono_ufos + sans_ufos:
        fontinfo_path = os.path.join(ufo_path, "fontinfo.plist")
        if os.path.exists(fontinfo_path):
            fix_fontinfo(fontinfo_path)

    print("\nDone.")


if __name__ == "__main__":
    main()
