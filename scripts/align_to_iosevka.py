"""
Align Recursive Charon glyph designs toward Iosevka Charon style.

Modifies glyph outlines in UFO sources to visually match Iosevka Charon's
character designs and curve geometry. Only moves existing points — never
adds or removes them — so interpolation compatibility is preserved.

Key design alignment targets (from Iosevka Charon build plan):
- Tighter, more geometric curves (higher tension)
- Curly v/w/y forms (rounded bottoms)
- Open-contour 6/9
- Curly V/W/Y/A uppercase forms
- More rounded e
"""

import math
from pathlib import Path
from defcon import Font


SRC = Path(__file__).resolve().parent.parent / "src" / "ufo"

# Curve tightening factor — how much to pull off-curve points
# toward the "geometric ideal" (midpoint of neighboring on-curves).
CURVE_TIGHTEN = 0.12


def get_master_weight(ufo_name):
    """Extract weight designation from UFO name."""
    name = ufo_name
    if name.endswith(" A.ufo") or " A Slanted" in name:
        return "A"
    if name.endswith(" B.ufo") or " B Slanted" in name:
        return "B"
    if name.endswith(" C.ufo") or " C Slanted" in name:
        return "C"
    return "B"


def tighten_contour_curves(contour, factor=CURVE_TIGHTEN):
    """Pull off-curve control points closer to create tighter, more
    geometric curves like Iosevka.

    For each off-curve point, moves it toward the midpoint of its
    neighboring on-curve points by `factor`.
    """
    points = list(contour)
    if len(points) < 3:
        return False

    changed = False
    for i, pt in enumerate(points):
        if pt.segmentType is not None:
            continue  # on-curve point, skip

        # Find adjacent on-curve points
        prev_on = None
        next_on = None

        for j in range(1, len(points)):
            idx = (i - j) % len(points)
            if points[idx].segmentType is not None:
                prev_on = points[idx]
                break

        for j in range(1, len(points)):
            idx = (i + j) % len(points)
            if points[idx].segmentType is not None:
                next_on = points[idx]
                break

        if prev_on is None or next_on is None:
            continue

        # Calculate midpoint of on-curve neighbors
        mid_x = (prev_on.x + next_on.x) / 2
        mid_y = (prev_on.y + next_on.y) / 2

        # Move off-curve point toward midpoint
        new_x = round(pt.x + (mid_x - pt.x) * factor)
        new_y = round(pt.y + (mid_y - pt.y) * factor)

        if new_x != pt.x or new_y != pt.y:
            pt.x = new_x
            pt.y = new_y
            changed = True

    return changed


def round_bottom_vertex(glyph, weight, y_range=(0, 150), x_range=(100, 400),
                        lift_amounts=None):
    """Lift bottom vertex on-curve points upward to create a rounder bottom.

    Used for v, w, V, W etc.
    """
    if lift_amounts is None:
        lift_amounts = {"A": 25, "B": 35, "C": 45}
    lift = lift_amounts.get(weight, 35)

    changed = False
    for contour in glyph:
        for pt in contour:
            if (pt.segmentType is not None and
                y_range[0] <= pt.y <= y_range[1] and
                x_range[0] <= pt.x <= x_range[1]):
                pt.y += lift
                changed = True
    return changed


def adjust_v_bottom(glyph, weight="B"):
    """Make 'v' bottom more rounded/curly."""
    return round_bottom_vertex(
        glyph, weight,
        y_range=(0, 150), x_range=(150, 350),
        lift_amounts={"A": 30, "B": 40, "C": 50}
    )


def adjust_w_bottom(glyph, weight="B"):
    """Make 'w' inner valleys more rounded."""
    return round_bottom_vertex(
        glyph, weight,
        y_range=(0, 140), x_range=(100, 420),
        lift_amounts={"A": 25, "B": 32, "C": 40}
    )


def adjust_y_descender(glyph, weight="B"):
    """Make 'y' descender turn smoother like Iosevka's curly-turn."""
    adj = {"A": 18, "B": 22, "C": 28}.get(weight, 22)

    changed = False
    for contour in glyph:
        for pt in contour:
            # y descender turn points around y=-70 to y=-100
            if pt.y <= -50 and pt.y >= -110 and pt.x < 220:
                pt.y += adj
                changed = True
    return changed


def open_six_contour(glyph, weight="B"):
    """Make '6' more open at the top like Iosevka's open-contour variant."""
    pull = {"A": 40, "B": 55, "C": 70}.get(weight, 55)

    changed = False
    for contour in glyph:
        for pt in contour:
            # The 6's top terminal — rightmost points near the top
            if pt.x > 360 and pt.y > 520:
                pt.x -= pull
                changed = True
            # Also pull the top-right curve points
            elif pt.x > 320 and pt.y > 560 and pt.y < 650:
                pt.x -= pull // 2
                changed = True
    return changed


def open_nine_contour(glyph, weight="B"):
    """Make '9' more open at the bottom (mirror of 6 adjustment)."""
    pull = {"A": 40, "B": 55, "C": 70}.get(weight, 55)

    changed = False
    for contour in glyph:
        for pt in contour:
            # The 9's bottom terminal — leftmost points near the bottom
            if pt.x < 140 and pt.y < 180 and pt.y > 20:
                pt.x += pull
                changed = True
            elif pt.x < 180 and pt.y < 140 and pt.y > -20:
                pt.x += pull // 2
                changed = True
    return changed


def adjust_A_pointy(glyph, weight="B"):
    """Make 'A' apex narrower/more pointed like Iosevka's curly-serifless."""
    narrow = {"A": 8, "B": 12, "C": 15}.get(weight, 12)

    changed = False
    for contour in glyph:
        for pt in contour:
            # A apex area — points near y=550-610, narrowing from center
            if pt.y >= 540 and pt.y <= 620:
                if pt.x < 250:
                    pt.x += narrow
                    changed = True
                elif pt.x > 250:
                    pt.x -= narrow
                    changed = True
    return changed


def adjust_V_curly(glyph, weight="B"):
    """Make 'V' more curly at the bottom."""
    return round_bottom_vertex(
        glyph, weight,
        y_range=(0, 60), x_range=(150, 380),
        lift_amounts={"A": 22, "B": 30, "C": 38}
    )


def adjust_W_curly(glyph, weight="B"):
    """Make 'W' more curly at bottom valleys."""
    return round_bottom_vertex(
        glyph, weight,
        y_range=(0, 50), x_range=(80, 450),
        lift_amounts={"A": 18, "B": 25, "C": 32}
    )


def adjust_Y_curly(glyph, weight="B"):
    """Make 'Y' junction more curly."""
    lift = {"A": 15, "B": 20, "C": 25}.get(weight, 20)

    changed = False
    for contour in glyph:
        for pt in contour:
            # Y fork junction — around y=200-380, near center
            if pt.segmentType is not None and 180 <= pt.y <= 390 and 170 <= pt.x <= 340:
                pt.y += lift
                changed = True
    return changed


def adjust_e_rounder(glyph, weight="B"):
    """Make 'e' aperture more open like Iosevka's rounded variant.

    The main difference between Recursive's e and Iosevka's e is the
    aperture (opening on the right side). Iosevka's is much more open —
    the terminal stays low instead of curving back up.

    We achieve this by:
    1. Pulling the terminal cap points downward (opening the aperture)
    2. Pulling inward slightly on the right side for a rounder shape
    """
    # How much to drop the terminal (the part that curves up on the right)
    drop = {"A": 30, "B": 45, "C": 55}.get(weight, 45)
    # How much to pull rightmost bowl points inward
    inward = {"A": 8, "B": 12, "C": 16}.get(weight, 12)

    changed = False
    for contour in glyph:
        for pt in contour:
            # Terminal area: right side, below the crossbar (y < 120),
            # where the stroke end curves up. Pull these DOWN.
            if pt.x > 380 and 40 <= pt.y <= 120:
                pt.y -= drop
                changed = True
            # Also drop the off-curve points leading into the terminal
            elif pt.x > 350 and 30 <= pt.y <= 100 and pt.segmentType is None:
                pt.y -= drop // 2
                changed = True
            # Pull rightmost bowl points inward for rounder shape
            elif pt.x > 400 and 200 <= pt.y <= 340:
                pt.x -= inward
                changed = True
    return changed


def narrow_f(glyph, weight="B"):
    """Make 'f' narrower like Iosevka's narrow-serifless variant.

    Pull the rightmost points inward.
    """
    adj = {"A": 8, "B": 12, "C": 16}.get(weight, 12)

    changed = False
    for contour in glyph:
        for pt in contour:
            # f's crossbar extends to the right - pull it in
            if pt.x > 400 and 400 <= pt.y <= 560:
                pt.x -= adj
                changed = True
    return changed


def narrow_r(glyph, weight="B"):
    """Make 'r' narrower like Iosevka's narrow-hook variant.

    Pull the right hook inward.
    """
    adj = {"A": 10, "B": 15, "C": 20}.get(weight, 15)

    changed = False
    for contour in glyph:
        for pt in contour:
            # r's right hook/arm — rightmost points in upper area
            if pt.x > 350 and pt.y > 350:
                pt.x -= adj
                changed = True
    return changed


def adjust_t_hook(glyph, weight="B"):
    """Adjust 't' to be narrower with a more bent hook like Iosevka."""
    adj = {"A": 8, "B": 12, "C": 16}.get(weight, 12)

    changed = False
    for contour in glyph:
        for pt in contour:
            # t's crossbar right end and hook
            if pt.x > 380 and pt.y < 120 and pt.y > -30:
                pt.x -= adj
                changed = True
    return changed


def process_ufo(ufo_path):
    """Process a single UFO, applying design alignment modifications."""
    ufo = Font(str(ufo_path))
    weight = get_master_weight(ufo_path.name)
    name = ufo_path.name

    print(f"Processing {name} (weight={weight})")

    total_changed = 0

    # 1. Specific character form adjustments
    char_adjustments = {
        "v": lambda g: adjust_v_bottom(g, weight),
        "w": lambda g: adjust_w_bottom(g, weight),
        "y": lambda g: adjust_y_descender(g, weight),
        "six": lambda g: open_six_contour(g, weight),
        "nine": lambda g: open_nine_contour(g, weight),
        "A": lambda g: adjust_A_pointy(g, weight),
        "V": lambda g: adjust_V_curly(g, weight),
        "W": lambda g: adjust_W_curly(g, weight),
        "Y": lambda g: adjust_Y_curly(g, weight),
        "e": lambda g: adjust_e_rounder(g, weight),
        "f": lambda g: narrow_f(g, weight),
        "r": lambda g: narrow_r(g, weight),
        "t": lambda g: adjust_t_hook(g, weight),
    }

    for glyph_name, adj_fn in char_adjustments.items():
        if glyph_name in ufo:
            glyph = ufo[glyph_name]
            if adj_fn(glyph):
                glyph.dirty = True
                total_changed += 1
                print(f"  Adjusted {glyph_name}")

    # 2. General curve tightening across all glyphs
    curve_count = 0
    for glyph_name in ufo.keys():
        glyph = ufo[glyph_name]
        glyph_changed = False
        for contour in glyph:
            if tighten_contour_curves(contour, CURVE_TIGHTEN):
                glyph_changed = True

        if glyph_changed:
            glyph.dirty = True
            curve_count += 1

    if curve_count:
        print(f"  Tightened curves in {curve_count} glyphs")
        total_changed += curve_count

    if total_changed > 0:
        print(f"  Saving {name}...")
        ufo.save()
    else:
        print(f"  No changes needed")

    return total_changed


def main():
    """Process all UFO sources."""
    ufo_dirs = []
    for subdir in ["mono", "sans"]:
        d = SRC / subdir
        if d.exists():
            for item in sorted(d.iterdir()):
                if item.suffix == ".ufo" and item.is_dir():
                    ufo_dirs.append(item)

    print(f"Found {len(ufo_dirs)} UFO sources")
    print(f"Curve tightening factor: {CURVE_TIGHTEN}")
    print()

    grand_total = 0
    for ufo in ufo_dirs:
        grand_total += process_ufo(ufo)
        print()

    print(f"Grand total: {grand_total} modifications across {len(ufo_dirs)} UFOs")


if __name__ == "__main__":
    main()
