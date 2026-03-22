#!/usr/bin/env python3
"""Generate comparison images showing font variants across different configurations."""

import os

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

ALL_LC = "abcdefghijklmnopqrstuvwxyz"
ALL_UC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
UPRIGHT_CHARS = "yasghj kzxcnm"  # chars that keep upright forms (italic only in italic mode)
ITALIC_DEFAULT_CHARS = "bdefi lruvw"  # chars always using italic form

OUTPUT_DIR = "comparison_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_label_font(size=16):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def create_full_alphabet():
    """Full lowercase + uppercase alphabet for each variant."""
    font_size = 48
    label_size = 14
    row_height = 80
    width = 1200
    height = 30 + len(FONTS) * row_height * 2 + 20

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    label_font = get_label_font(label_size)

    y = 20
    for name, path in FONTS.items():
        draw.text((20, y), name, fill='#666', font=label_font)
        y += 20
        try:
            font = ImageFont.truetype(path, font_size)
            draw.text((20, y), ALL_LC, fill='black', font=font)
            y += 55
            draw.text((20, y), ALL_UC, fill='black', font=font)
        except Exception as e:
            draw.text((20, y), f"Error: {e}", fill='red', font=label_font)
        y += row_height - 20
        draw.line([(20, y), (width - 20, y)], fill='#eee')
        y += 10

    img = img.crop((0, 0, width, y + 20))
    img.save(os.path.join(OUTPUT_DIR, "full_alphabet.png"))
    print(f"Saved full_alphabet.png")


def create_italic_grid():
    """Grid showing italic-default chars across all variants."""
    font_size = 60
    label_size = 18
    char_width = 70
    row_height = 90
    label_width = 250

    chars_display = [c for c in ITALIC_DEFAULT_CHARS if c != ' ']
    width = label_width + len(chars_display) * char_width + 20
    height = 60 + len(FONTS) * row_height + 20

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    label_font = get_label_font(label_size)

    for i, c in enumerate(chars_display):
        x = label_width + i * char_width + char_width // 2
        draw.text((x - 5, 10), c, fill='gray', font=label_font)

    draw.line([(0, 45), (width, 45)], fill='lightgray')

    for row, (name, path) in enumerate(FONTS.items()):
        y = 55 + row * row_height
        draw.text((10, y + 20), name, fill='black', font=label_font)
        try:
            font = ImageFont.truetype(path, font_size)
        except Exception:
            continue
        for i, c in enumerate(chars_display):
            x = label_width + i * char_width
            draw.text((x + 10, y + 10), c, fill='black', font=font)
        draw.line([(0, y + row_height - 5), (width, y + row_height - 5)], fill='#eee')

    img.save(os.path.join(OUTPUT_DIR, "italic_default_grid.png"))
    print(f"Saved italic_default_grid.png")


def create_upright_grid():
    """Grid showing upright-default chars (italic only when italic active)."""
    font_size = 60
    label_size = 18
    char_width = 70
    row_height = 90
    label_width = 250

    chars_display = [c for c in UPRIGHT_CHARS if c != ' ']
    width = label_width + len(chars_display) * char_width + 20
    height = 60 + len(FONTS) * row_height + 20

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    label_font = get_label_font(label_size)

    for i, c in enumerate(chars_display):
        x = label_width + i * char_width + char_width // 2
        draw.text((x - 5, 10), c, fill='gray', font=label_font)

    draw.line([(0, 45), (width, 45)], fill='lightgray')

    for row, (name, path) in enumerate(FONTS.items()):
        y = 55 + row * row_height
        draw.text((10, y + 20), name, fill='black', font=label_font)
        try:
            font = ImageFont.truetype(path, font_size)
        except Exception:
            continue
        for i, c in enumerate(chars_display):
            x = label_width + i * char_width
            draw.text((x + 10, y + 10), c, fill='black', font=font)
        draw.line([(0, y + row_height - 5), (width, y + row_height - 5)], fill='#eee')

    img.save(os.path.join(OUTPUT_DIR, "upright_default_grid.png"))
    print(f"Saved upright_default_grid.png")


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

    text = ALL_LC
    row_height = 110
    width = 1200
    height = 30 + len(pairs) * row_height + 20

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    label_font = get_label_font(label_size)

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


def create_text_specimen():
    """Text specimens with all variants."""
    font_size = 36
    label_size = 16
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
    label_font = get_label_font(label_size)

    y = margin
    for name, path in FONTS.items():
        draw.text((margin, y), name, fill='#666', font=label_font)
        y += 25
        try:
            font = ImageFont.truetype(path, font_size)
        except Exception:
            y += len(texts) * 50
            continue
        for text in texts:
            draw.text((margin, y), text, fill='black', font=font)
            y += 45
        y += 15
        draw.line([(margin, y), (width - margin, y)], fill='#ddd')
        y += 10

    img = img.crop((0, 0, width, min(y + margin, height)))
    img.save(os.path.join(OUTPUT_DIR, "text_specimen.png"))
    print(f"Saved text_specimen.png")


def create_cap_C_comparison():
    """Show capital C across all font configs at large size."""
    font_size = 120
    label_size = 16
    cell_width = 200
    row_height = 170
    label_width = 250

    # Show C alongside similar shapes for context
    chars = ['C', 'G', 'O', 'Q', 'c', 'e', 'o']

    width = label_width + len(chars) * cell_width + 20
    height = 60 + len(FONTS) * row_height + 20

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    label_font = get_label_font(label_size)

    # Header
    for i, c in enumerate(chars):
        x = label_width + i * cell_width + cell_width // 2
        draw.text((x - 5, 10), c, fill='gray', font=label_font)

    draw.line([(0, 40), (width, 40)], fill='lightgray')

    for row, (name, path) in enumerate(FONTS.items()):
        y = 50 + row * row_height
        draw.text((10, y + 60), name, fill='black', font=label_font)
        try:
            font = ImageFont.truetype(path, font_size)
        except Exception:
            continue
        for i, c in enumerate(chars):
            x = label_width + i * cell_width + 20
            draw.text((x, y + 10), c, fill='black', font=font)
        draw.line([(0, y + row_height - 5), (width, y + row_height - 5)], fill='#eee')

    img = img.crop((0, 0, width, 50 + len(FONTS) * row_height + 20))
    img.save(os.path.join(OUTPUT_DIR, "cap_C_comparison.png"))
    print(f"Saved cap_C_comparison.png")


def create_cap_C_closeup():
    """Large closeup of capital C in each configuration."""
    font_size = 200
    label_size = 18
    margin = 30

    configs = [
        ("Mono Linear", "fonts_inspect/Static_OTF/Recursive Mono-Linear A.otf"),
        ("Mono Linear Slanted", "fonts_inspect/Static_OTF/Recursive Mono-Linear A Slanted.otf"),
        ("Mono Casual", "fonts_inspect/Static_OTF/Recursive Mono-Casual A.otf"),
        ("Mono Casual Slanted", "fonts_inspect/Static_OTF/Recursive Mono-Casual A Slanted.otf"),
        ("Mono Linear Bold", "fonts_inspect/Static_OTF/Recursive Mono-Linear B.otf"),
        ("Sans Linear", "fonts_inspect/Static_OTF/Recursive Sans-Linear A.otf"),
        ("Sans Casual", "fonts_inspect/Static_OTF/Recursive Sans-Casual A.otf"),
    ]

    col_width = 320
    row_height = 280
    cols = 4
    rows = (len(configs) + cols - 1) // cols

    width = margin + cols * col_width + margin
    height = margin + rows * row_height + margin

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    label_font = get_label_font(label_size)

    for idx, (name, path) in enumerate(configs):
        col = idx % cols
        row = idx // cols
        x = margin + col * col_width
        y = margin + row * row_height

        draw.text((x + 10, y + 5), name, fill='#666', font=label_font)
        try:
            font = ImageFont.truetype(path, font_size)
            draw.text((x + 40, y + 30), "C", fill='black', font=font)
        except Exception as e:
            draw.text((x + 10, y + 40), f"Error", fill='red', font=label_font)

        # Border
        draw.rectangle([(x, y), (x + col_width - 10, y + row_height - 10)], outline='#ddd')

    img = img.crop((0, 0, width, margin + rows * row_height + margin))
    img.save(os.path.join(OUTPUT_DIR, "cap_C_closeup.png"))
    print(f"Saved cap_C_closeup.png")


if __name__ == '__main__':
    create_full_alphabet()
    create_italic_grid()
    create_upright_grid()
    create_upright_vs_slanted()
    create_text_specimen()
    create_cap_C_comparison()
    create_cap_C_closeup()
    print("\nAll comparison images generated in comparison_output/")
