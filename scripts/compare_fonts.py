"""
Compare Recursive Charon vs Iosevka Charon side by side.
Renders key characters and saves comparison images.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def render_text(font_path, text, size=72):
    """Render text using a font and return an Image."""
    font = ImageFont.truetype(str(font_path), size)

    dummy = Image.new("L", (1, 1))
    dd = ImageDraw.Draw(dummy)
    bbox = dd.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 40
    h = bbox[3] - bbox[1] + 40

    img = Image.new("L", (max(w, 1), max(h, 1)), 255)
    draw = ImageDraw.Draw(img)
    draw.text((20 - bbox[0], 20 - bbox[1]), text, font=font, fill=0)
    return img


def make_comparison(recursive_path, iosevka_path, output_dir, label=""):
    """Create side-by-side comparison images."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    test_strings = {
        "lowercase": "abcdefghijklmnopqrstuvwxyz",
        "uppercase": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "digits": "0123456789",
        "key_chars": "adefgijlrtuvwy ADQVWY",
        "punctuation": "@&${}[]()<>|/\\",
        "code_sample": "fn main() { let x = 42; }",
        "mixed": "The quick brown fox jumps",
    }

    for name, text in test_strings.items():
        try:
            rec_img = render_text(recursive_path, text, 64)
            ios_img = render_text(iosevka_path, text, 64)
        except Exception as e:
            print(f"  Skipping {name}: {e}")
            continue

        max_w = max(rec_img.width, ios_img.width)
        combined = Image.new("L", (max_w, rec_img.height + ios_img.height + 40), 255)

        draw = ImageDraw.Draw(combined)
        draw.text((10, 2), "Recursive Charon", fill=0)
        combined.paste(rec_img, (0, 20))
        draw.text((10, rec_img.height + 22), "Iosevka Charon", fill=0)
        combined.paste(ios_img, (0, rec_img.height + 40))

        out = output_dir / f"compare_{label}_{name}.png"
        combined.save(str(out))
        print(f"  Saved {out.name}")


def main():
    import sys
    recursive = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/RecursiveCharon_static_test.ttf")
    iosevka = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/iosevka-charon-fonts/iosevkacharonmono/IosevkaCharonMono-Regular.ttf")
    output = Path("/home/user/recursive-charon/comparison_output")

    print(f"Comparing:\n  Recursive: {recursive}\n  Iosevka: {iosevka}\n")
    make_comparison(recursive, iosevka, output, label="v2")
    print("\nDone!")


if __name__ == "__main__":
    main()
