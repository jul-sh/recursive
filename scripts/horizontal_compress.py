"""
Horizontally compress all UFO sources by 0.8333x (5/6).

Scales:
- Glyph advance widths
- Outline point x coordinates
- Component xOffset values
- Anchor x positions
- Guideline x positions (in glif files)
- Kerning values (sans masters)
- postscriptStemSnapH in fontinfo.plist
"""

import re
import plistlib
from pathlib import Path

SCALE = 5 / 6  # 0.8333...
SRC = Path(__file__).resolve().parent.parent / "src" / "ufo"


def scale_val(s):
    """Scale a numeric string (int or float) and return rounded int as string."""
    return str(round(float(s) * SCALE))


def scale_glif(glif_path):
    """Scale horizontal values in a .glif file."""
    with open(glif_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Scale advance width (always int)
    content = re.sub(
        r'<advance width="(\d+)"',
        lambda m: f'<advance width="{scale_val(m.group(1))}"',
        content,
    )

    # Scale point x coordinates (may be float or negative)
    content = re.sub(
        r'(<point\s+)x="(-?[\d.]+)"',
        lambda m: f'{m.group(1)}x="{scale_val(m.group(2))}"',
        content,
    )

    # Scale component xOffset (may be negative)
    content = re.sub(
        r'(xOffset=")(-?[\d.]+)(")',
        lambda m: f'{m.group(1)}{scale_val(m.group(2))}{m.group(3)}',
        content,
    )

    # Scale anchor x
    content = re.sub(
        r'(<anchor\s[^>]*\bx=")(-?[\d.]+)(")',
        lambda m: f'{m.group(1)}{scale_val(m.group(2))}{m.group(3)}',
        content,
    )

    # Scale guideline x (vertical guidelines have x position)
    content = re.sub(
        r'(<guideline\s[^>]*\bx=")(-?[\d.]+)(")',
        lambda m: f'{m.group(1)}{scale_val(m.group(2))}{m.group(3)}',
        content,
    )

    with open(glif_path, "w", encoding="utf-8") as f:
        f.write(content)


def scale_kerning(kerning_path):
    """Scale all kerning values in a kerning.plist."""
    with open(kerning_path, "rb") as f:
        kerning = plistlib.load(f)

    for left in kerning:
        for right in kerning[left]:
            kerning[left][right] = round(kerning[left][right] * SCALE)

    with open(kerning_path, "wb") as f:
        plistlib.dump(kerning, f)


def scale_fontinfo(fontinfo_path):
    """Scale postscriptStemSnapH values in fontinfo.plist."""
    with open(fontinfo_path, "rb") as f:
        info = plistlib.load(f)

    if "postscriptStemSnapH" in info:
        info["postscriptStemSnapH"] = [round(v * SCALE) for v in info["postscriptStemSnapH"]]

    with open(fontinfo_path, "wb") as f:
        plistlib.dump(info, f)


def process_ufo(ufo_path):
    """Process a single UFO directory."""
    ufo = Path(ufo_path)
    print(f"Processing {ufo.name}")

    # Scale all glyph layers
    for item in sorted(ufo.iterdir()):
        if item.is_dir() and item.name.startswith("glyphs"):
            glifs = list(item.glob("*.glif"))
            for glif in glifs:
                scale_glif(glif)
            print(f"  {item.name}: {len(glifs)} glifs")

    # Scale kerning if present
    kerning = ufo / "kerning.plist"
    if kerning.exists():
        scale_kerning(kerning)
        print(f"  Scaled kerning")

    # Scale fontinfo
    fontinfo = ufo / "fontinfo.plist"
    if fontinfo.exists():
        scale_fontinfo(fontinfo)
        print(f"  Scaled fontinfo")


def main():
    ufo_dirs = []
    for subdir in ["mono", "sans", "extras"]:
        d = SRC / subdir
        if d.exists():
            for item in sorted(d.iterdir()):
                if item.suffix == ".ufo" and item.is_dir():
                    ufo_dirs.append(item)

    print(f"Found {len(ufo_dirs)} UFO sources")
    print(f"Scale factor: {SCALE:.6f}")
    print()

    for ufo in ufo_dirs:
        process_ufo(ufo)

    print("\nDone!")


if __name__ == "__main__":
    main()
