#!/usr/bin/env python3
"""
Fix PostScript blue value zones: values must be strictly ascending.
When cap height = ascender = 735, merge overlapping zones.
"""

import os
import glob
import plistlib

UFO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "ufo")


def fix_ascending_blues(values):
    """Ensure blue value pairs are strictly ascending, merging overlaps."""
    if not values or len(values) < 2:
        return values

    # Parse into pairs
    pairs = []
    for i in range(0, len(values) - 1, 2):
        pairs.append((values[i], values[i + 1]))

    # Merge overlapping or duplicate pairs
    merged = [pairs[0]]
    for bottom, top in pairs[1:]:
        prev_bottom, prev_top = merged[-1]
        if bottom <= prev_top:
            # Overlapping or touching - merge
            merged[-1] = (min(prev_bottom, bottom), max(prev_top, top))
        else:
            merged.append((bottom, top))

    # Ensure each pair has distinct values
    result = []
    for bottom, top in merged:
        if bottom == top:
            top = bottom + 10
        result.extend([bottom, top])

    return result


def fix_fontinfo(fontinfo_path):
    with open(fontinfo_path, "rb") as f:
        info = plistlib.load(f)

    name = info.get("styleName", "unknown")
    changes = []

    for key in ["postscriptBlueValues", "postscriptOtherBlues"]:
        if key in info:
            old = list(info[key])
            fixed = fix_ascending_blues(old)
            if fixed != old:
                info[key] = fixed
                changes.append(f"{key}: {old} -> {fixed}")

    if changes:
        with open(fontinfo_path, "wb") as f:
            plistlib.dump(info, f, sort_keys=True)
        print(f"  {name}: {'; '.join(changes)}")
    else:
        print(f"  {name}: OK")


def main():
    print("Fixing blue value zone ordering...")
    for ufo_path in sorted(glob.glob(os.path.join(UFO_ROOT, "mono", "*.ufo")) +
                           glob.glob(os.path.join(UFO_ROOT, "sans", "*.ufo"))):
        fontinfo_path = os.path.join(ufo_path, "fontinfo.plist")
        if os.path.exists(fontinfo_path):
            fix_fontinfo(fontinfo_path)
    print("\nDone.")


if __name__ == "__main__":
    main()
