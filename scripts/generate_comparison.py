#!/usr/bin/env python3
"""Generate comparison images showing italic shapes used as default across all variants."""

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
import os
import struct

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not found, trying alternative...")
    raise

FONTS = {
    "Mono Linear Light": "fonts_inspect/Static_OTF/Recursive Mono-Linear A.otf",
    "Mono Linear ExtraBold": "fonts_inspect/Static_OTF/Recursive Mono-Linear B.otf",
    "Mono Casual Light": "fonts_inspect/Static_OTF/Recursive Mono-Casual A.otf",
    "Sans Linear Light": "fonts_inspect/Static_OTF/Recursive Sans-Linear A.otf",
    "Sans Casual Light": "fonts_inspect/Static_OTF/Recursive Sans-Casual A.otf",
    "Mono Linear Slanted": "fonts_inspect/Static_OTF/Recursive Mono-Linear A Slanted.otf",
    "Mono Casual Slanted": "fonts_inspect/Static_OTF/Recursive Mono-Casual A Slanted.otf",
}

TARGET_CHARS = "yasghj kzxcnm"
ALL_CHARS = "abcdefghijklmnopqrstuvwxyz"
SAMPLE_TEXT = "the quick brown fox jumps"

OUTPUT_DIR = "comparison_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def render_text_with_font(font_path, text, size=48):
    """Render text using PIL with the specified font."""
    try:
        font = ImageFont.truetype(font_path, size)
    except Exception as e:
        print(f"  Error loading font {font_path}: {e}")
        return None

    # Calculate text bounding box
    dummy = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 20
    h = bbox[3] - bbox[1] + 20

    img = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(img)
    draw.text((10 - bbox[0], 10 - bbox[1]), text, fill='black', font=font)
    return img


def create_grid_comparison():
    """Create a grid showing target chars across all font variants."""
    font_size = 60
    label_size = 18
    char_width = 70
    row_height = 90
    label_width = 250

    chars_to_show = list("yasghj kzxcnm")
    # Remove space for display
    chars_display = [c for c in chars_to_show if c != ' ']

    width = label_width + len(chars_display) * char_width + 20
    height = 60 + len(FONTS) * row_height + 20

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    try:
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", label_size)
    except:
        label_font = ImageFont.load_default()

    # Header
    for i, c in enumerate(chars_display):
        x = label_width + i * char_width + char_width // 2
        draw.text((x - 5, 10), c, fill='gray', font=label_font)

    # Draw a line under header
    draw.line([(0, 45), (width, 45)], fill='lightgray')

    # Each font variant
    for row, (name, path) in enumerate(FONTS.items()):
        y = 55 + row * row_height
        draw.text((10, y + 20), name, fill='black', font=label_font)

        try:
            font = ImageFont.truetype(path, font_size)
        except:
            continue

        for i, c in enumerate(chars_display):
            x = label_width + i * char_width
            draw.text((x + 10, y + 10), c, fill='black', font=font)

        # Separator line
        draw.line([(0, y + row_height - 5), (width, y + row_height - 5)], fill='#eee')

    img.save(os.path.join(OUTPUT_DIR, "italic_shapes_grid.png"))
    print(f"Saved italic_shapes_grid.png ({width}x{height})")


def create_text_specimen():
    """Create text specimens with all variants."""
    font_size = 36
    label_size = 16
    row_height = 70
    margin = 20

    texts = [
        "the quick brown fox jumps",
        "pack my box with five dozen",
        "amazingly few discotheques",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    ]

    width = 900
    height = margin + len(FONTS) * (len(texts) * 50 + 40) + margin

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    try:
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", label_size)
    except:
        label_font = ImageFont.load_default()

    y = margin
    for name, path in FONTS.items():
        draw.text((margin, y), name, fill='#666', font=label_font)
        y += 25

        try:
            font = ImageFont.truetype(path, font_size)
        except:
            y += len(texts) * 50
            continue

        for text in texts:
            draw.text((margin, y), text, fill='black', font=font)
            y += 45

        y += 15
        draw.line([(margin, y), (width - margin, y)], fill='#ddd')
        y += 10

    # Crop to actual height
    img = img.crop((0, 0, width, min(y + margin, height)))
    img.save(os.path.join(OUTPUT_DIR, "text_specimen.png"))
    print(f"Saved text_specimen.png")


def create_upright_vs_slanted():
    """Compare upright and slanted versions side by side."""
    font_size = 72
    label_size = 16

    pairs = [
        ("Mono Linear Upright", "fonts_inspect/Static_OTF/Recursive Mono-Linear A.otf"),
        ("Mono Linear Slanted", "fonts_inspect/Static_OTF/Recursive Mono-Linear A Slanted.otf"),
        ("Mono Casual Upright", "fonts_inspect/Static_OTF/Recursive Mono-Casual A.otf"),
        ("Mono Casual Slanted", "fonts_inspect/Static_OTF/Recursive Mono-Casual A Slanted.otf"),
    ]

    text = "yasghj kzxcnm"
    row_height = 110
    width = 1000
    height = 30 + len(pairs) * row_height + 20

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    try:
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", label_size)
    except:
        label_font = ImageFont.load_default()

    y = 20
    for name, path in pairs:
        draw.text((20, y), name, fill='#666', font=label_font)
        y += 22

        try:
            font = ImageFont.truetype(path, font_size)
            draw.text((20, y), text, fill='black', font=font)
        except Exception as e:
            draw.text((20, y), f"Error: {e}", fill='red', font=label_font)

        y += row_height - 22

    img = img.crop((0, 0, width, y + 20))
    img.save(os.path.join(OUTPUT_DIR, "upright_vs_slanted.png"))
    print(f"Saved upright_vs_slanted.png")


def create_full_alphabet():
    """Show full alphabet for each variant to verify all chars look right."""
    font_size = 48
    label_size = 14

    row_height = 80
    width = 1200
    height = 30 + len(FONTS) * row_height + 20

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    try:
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", label_size)
    except:
        label_font = ImageFont.load_default()

    y = 20
    for name, path in FONTS.items():
        draw.text((20, y), name, fill='#666', font=label_font)
        y += 20

        try:
            font = ImageFont.truetype(path, font_size)
            draw.text((20, y), ALL_CHARS, fill='black', font=font)
        except Exception as e:
            draw.text((20, y), f"Error: {e}", fill='red', font=label_font)

        y += row_height - 20

    img = img.crop((0, 0, width, y + 20))
    img.save(os.path.join(OUTPUT_DIR, "full_alphabet.png"))
    print(f"Saved full_alphabet.png")


if __name__ == '__main__':
    create_grid_comparison()
    create_text_specimen()
    create_upright_vs_slanted()
    create_full_alphabet()
    print("\nAll comparison images generated in comparison_output/")
