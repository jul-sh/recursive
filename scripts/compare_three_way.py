"""Three-way comparison: Original Recursive Charon vs Modified vs Iosevka Charon."""
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
    original = Path("/home/user/recursive-charon/fonts/ArrowType-Recursive-1.085/Recursive_Desktop/Recursive_VF_1.085.ttf")
    modified = Path("/tmp/RecursiveCharon_static_test2.ttf")
    iosevka = Path("/tmp/iosevka-charon-fonts/iosevkacharonmono/IosevkaCharonMono-Regular.ttf")
    output = Path("/home/user/recursive-charon/comparison_output")
    output.mkdir(exist_ok=True)

    test_strings = {
        "lowercase": "abcdefghijklmnopqrstuvwxyz",
        "uppercase": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "digits": "0123456789",
        "key_chars": "adefgijlrtuvwy ADQVWY",
        "code": "fn main() { let x = 42; }",
    }

    for name, text in test_strings.items():
        try:
            # For the VF, set mono linear regular
            orig_font = ImageFont.truetype(str(original), 56)
            orig_font.set_variation_by_axes([1.0, 0.0, 400.0, 0.0, 0.5])

            dummy = Image.new("L", (1, 1))
            dd = ImageDraw.Draw(dummy)
            bbox = dd.textbbox((0, 0), text, font=orig_font)
            w = bbox[2] - bbox[0] + 40
            h = bbox[3] - bbox[1] + 40
            orig_img = Image.new("L", (max(w, 1), max(h, 1)), 255)
            draw = ImageDraw.Draw(orig_img)
            draw.text((20 - bbox[0], 20 - bbox[1]), text, font=orig_font, fill=0)

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
