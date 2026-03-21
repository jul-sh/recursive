"""Three-way comparison: Original Recursive Charon vs Modified vs Iosevka Charon."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def render_text(font_path, text, size=56):
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


def main():
    original = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/RecursiveCharon_static_original.ttf")
    modified = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/RecursiveCharon_static_current.ttf")
    iosevka = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("/tmp/iosevka-charon-fonts/iosevkacharonmono/IosevkaCharonMono-Regular.ttf")
    output = Path("/home/user/recursive-charon/comparison_output")
    output.mkdir(exist_ok=True)

    test_strings = {
        "lowercase": "abcdefghijklmnopqrstuvwxyz",
        "uppercase": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "digits": "0123456789",
        "key_chars": "adefgijlrtuvwy ADQVWY",
        "punctuation": "@&${}[]()<>|/\\",
        "code": "fn main() { let x = 42; }",
    }

    for name, text in test_strings.items():
        try:
            orig_img = render_text(original, text, 56)
            mod_img = render_text(modified, text, 56)
            ios_img = render_text(iosevka, text, 56)
        except Exception as e:
            print(f"  Skipping {name}: {e}")
            continue

        max_w = max(orig_img.width, mod_img.width, ios_img.width)
        total_h = orig_img.height + mod_img.height + ios_img.height + 70
        combined = Image.new("L", (max_w, total_h), 255)
        draw = ImageDraw.Draw(combined)

        y = 0
        draw.text((10, y + 2), "Original Recursive Charon", fill=0)
        combined.paste(orig_img, (0, y + 18))
        y += orig_img.height + 22

        draw.text((10, y + 2), "Modified Recursive Charon", fill=0)
        combined.paste(mod_img, (0, y + 18))
        y += mod_img.height + 22

        draw.text((10, y + 2), "Iosevka Charon (target)", fill=0)
        combined.paste(ios_img, (0, y + 18))

        out = output / f"three_way_{name}.png"
        combined.save(str(out))
        print(f"  Saved {out.name}")

    print("Done!")


if __name__ == "__main__":
    main()
