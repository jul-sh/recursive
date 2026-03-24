#!/usr/bin/env python3
"""
Remove the flag/tab element from f.italic.glif across all UFO masters.

The "flag" is a structural element at the top of the f's ascender in contour 0.
It consists of points that descend from the ascender peak (~y=700), go down to a
horizontal tab, then come back up. This script removes those points and replaces
them with 3 points that create a smooth curve bridging P_start to the kept
off-curves before P_end.

The edit has already been applied to Recursive Mono-Linear A.ufo, so that master
is skipped.
"""

import xml.etree.ElementTree as ET
import glob
import os
import sys
import re

UFO_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "src", "ufo", "mono")

# Already edited -- skip
SKIP_UFOS = ["Recursive Mono-Linear A.ufo"]


def parse_num(val):
    """Parse a coordinate string to float."""
    return float(val)


def find_flag_region(points):
    """
    Find the flag region in contour 0's point list.

    Returns (start_idx, flag_end_idx, pend_idx) where:
    - start_idx: index of P_start (the non-smooth "curve" point, KEPT)
    - flag_end_idx: last index of the flag (inclusive, to be REMOVED)
    - pend_idx: index of P_end (curve smooth, KEPT along with 2 off-curves before it)

    The flag points to remove are indices start_idx+1 through flag_end_idx (inclusive).
    The 2 off-curves at flag_end_idx+1 and flag_end_idx+2 are KEPT.
    P_end at pend_idx = flag_end_idx+3 is KEPT.
    """
    # Find P_start: on-curve "curve" point, NOT smooth, with y ~ 560-710
    # followed by points that go DOWN (the flag descent)
    candidates = []
    for i, pt in enumerate(points):
        pt_type = pt.get('type')
        pt_smooth = pt.get('smooth')
        y = parse_num(pt.get('y'))

        if pt_type == 'curve' and pt_smooth is None and 560 <= y <= 710:
            if i + 1 < len(points):
                next_y = parse_num(points[i + 1].get('y'))
                if next_y < y:
                    candidates.append(i)

    if not candidates:
        return None

    # Pick the candidate with highest y (the ascender peak)
    best_start = max(candidates, key=lambda idx: parse_num(points[idx].get('y')))
    start_idx = best_start

    # Find P_end: first "curve smooth" point after start_idx with y > 715
    pend_idx = None
    for i in range(start_idx + 1, len(points)):
        pt_type = points[i].get('type')
        pt_smooth = points[i].get('smooth')
        y = parse_num(points[i].get('y'))

        if pt_type == 'curve' and pt_smooth == 'yes' and y > 715:
            pend_idx = i
            break

    if pend_idx is None:
        return None

    # The 2 points immediately before P_end should be off-curve control points.
    # These are KEPT. The flag ends at pend_idx - 3 (the last flag point).
    offcurve1_idx = pend_idx - 2
    offcurve2_idx = pend_idx - 1

    # Verify they are off-curve (no type attribute)
    if points[offcurve1_idx].get('type') is not None:
        print(f"  WARNING: Expected off-curve at [{offcurve1_idx}], got type={points[offcurve1_idx].get('type')}")
    if points[offcurve2_idx].get('type') is not None:
        print(f"  WARNING: Expected off-curve at [{offcurve2_idx}], got type={points[offcurve2_idx].get('type')}")

    flag_end_idx = pend_idx - 3  # Last flag point to remove

    if flag_end_idx < start_idx + 1:
        print(f"  WARNING: flag_end_idx ({flag_end_idx}) < start_idx+1 ({start_idx+1})")
        return None

    return (start_idx, flag_end_idx, pend_idx)


def compute_replacement_points(p_start_pt, first_kept_offcurve):
    """
    Compute the 3 replacement points.

    Based on the reference (Linear A):
    - P_start: (435, 700) type="curve"
    - first_kept_offcurve: (475, 727) -- the off-curve before P_end that was kept
    - Replacement:
      - off-curve 1: (446, 681) = (P_start.x + 11, P_start.y - 19)
      - off-curve 2: (475, 723) = (kept_offcurve.x, kept_offcurve.y - 4)
      - on-curve:    (475, 723) = same as off-curve 2, type="curve"
    """
    sx = parse_num(p_start_pt.get('x'))
    sy = parse_num(p_start_pt.get('y'))
    kx = parse_num(first_kept_offcurve.get('x'))
    ky = parse_num(first_kept_offcurve.get('y'))

    # off-curve 1: slight rightward and downward from P_start
    off1_x = round(sx + 11, 4)
    off1_y = round(sy - 19, 4)

    # on-curve (and off-curve 2 at same position): at kept off-curve's x, y - 4
    on_x = round(kx, 4)
    on_y = round(ky - 4, 4)

    return [
        {'x': off1_x, 'y': off1_y},  # off-curve
        {'x': on_x, 'y': on_y},      # off-curve
        {'x': on_x, 'y': on_y},      # on-curve type="curve"
    ]


def format_coord(val):
    """Format a coordinate value, removing unnecessary trailing zeros."""
    if val == int(val):
        return str(int(val))
    s = f"{val:.10f}".rstrip('0').rstrip('.')
    return s


def process_file(filepath):
    """Process a single f.italic.glif file to remove the flag."""
    tree = ET.parse(filepath)
    root = tree.getroot()

    outline = root.find('outline')
    if outline is None:
        print(f"  SKIP: No outline in {filepath}")
        return False

    contours = outline.findall('contour')
    if not contours:
        print(f"  SKIP: No contours in {filepath}")
        return False

    contour0 = contours[0]
    points = list(contour0.findall('point'))

    result = find_flag_region(points)
    if result is None:
        print(f"  SKIP: Could not find flag region in {filepath}")
        return False

    start_idx, flag_end_idx, pend_idx = result
    p_start = points[start_idx]
    p_end = points[pend_idx]
    first_kept_offcurve = points[flag_end_idx + 1]  # = pend_idx - 2

    flag_count = flag_end_idx - start_idx  # number of points to remove

    print(f"  P_start[{start_idx}]: ({p_start.get('x')}, {p_start.get('y')}) type={p_start.get('type')}")
    print(f"  Flag points: [{start_idx+1}] to [{flag_end_idx}] ({flag_count} points)")
    print(f"  Kept off-curve 1[{flag_end_idx+1}]: ({first_kept_offcurve.get('x')}, {first_kept_offcurve.get('y')})")
    print(f"  Kept off-curve 2[{flag_end_idx+2}]: ({points[flag_end_idx+2].get('x')}, {points[flag_end_idx+2].get('y')})")
    print(f"  P_end[{pend_idx}]: ({p_end.get('x')}, {p_end.get('y')}) type={p_end.get('type')} smooth={p_end.get('smooth')}")

    # Compute replacement points
    replacements = compute_replacement_points(p_start, first_kept_offcurve)

    with open(filepath, 'r') as f:
        content = f.read()

    # Detect indentation
    indent_match = re.search(r'^(\s+)<point ', content, re.MULTILINE)
    indent = indent_match.group(1) if indent_match else '\t\t\t'

    # Detect self-closing tag style
    has_space_before_close = ' />' in content
    close_tag = ' />' if has_space_before_close else '/>'

    return do_string_surgery(filepath, content, points, start_idx, flag_end_idx,
                             replacements, indent, close_tag)


def do_string_surgery(filepath, content, points, start_idx, flag_end_idx,
                      replacements, indent, close_tag):
    """Do the edit via string replacement to preserve file formatting."""
    lines = content.split('\n')

    # Find <point> line indices in the first contour
    point_lines = []
    in_first_contour = False
    first_contour_started = False

    for li, line in enumerate(lines):
        stripped = line.strip()
        if '<contour>' in stripped or '<contour ' in stripped:
            if not first_contour_started:
                in_first_contour = True
                first_contour_started = True
        elif '</contour>' in stripped:
            if in_first_contour:
                in_first_contour = False
        elif in_first_contour and stripped.startswith('<point '):
            point_lines.append(li)

    if not point_lines:
        print(f"  ERROR: Could not find point lines in {filepath}")
        return False

    # Lines to remove: flag points at indices start_idx+1 through flag_end_idx
    remove_start_line = point_lines[start_idx + 1]
    remove_end_line = point_lines[flag_end_idx]

    # Build replacement lines
    new_lines = []
    for j, rep in enumerate(replacements):
        x_str = format_coord(rep['x'])
        y_str = format_coord(rep['y'])
        if j == 2:
            new_lines.append(f'{indent}<point x="{x_str}" y="{y_str}" type="curve"{close_tag}')
        else:
            new_lines.append(f'{indent}<point x="{x_str}" y="{y_str}"{close_tag}')

    # Splice: remove flag lines, insert replacement lines
    result_lines = lines[:remove_start_line] + new_lines + lines[remove_end_line + 1:]

    new_content = '\n'.join(result_lines)

    with open(filepath, 'w') as f:
        f.write(new_content)

    print(f"  Wrote {filepath}")
    print(f"  Replacement points:")
    for j, rep in enumerate(replacements):
        tp = 'curve' if j == 2 else 'off-curve'
        print(f"    ({format_coord(rep['x'])}, {format_coord(rep['y'])}) {tp}")

    return True


def main():
    ufo_dirs = sorted(glob.glob(os.path.join(UFO_BASE, "*.ufo")))

    if not ufo_dirs:
        print(f"ERROR: No UFO directories found in {UFO_BASE}")
        sys.exit(1)

    processed = 0
    skipped = 0
    errors = 0

    for ufo_dir in ufo_dirs:
        ufo_name = os.path.basename(ufo_dir)
        glif_path = os.path.join(ufo_dir, "glyphs", "f.italic.glif")

        if not os.path.exists(glif_path):
            print(f"SKIP: {ufo_name} -- no f.italic.glif")
            skipped += 1
            continue

        if ufo_name in SKIP_UFOS:
            print(f"SKIP: {ufo_name} -- already edited")
            skipped += 1
            continue

        print(f"\nProcessing: {ufo_name}")
        try:
            if process_file(glif_path):
                processed += 1
            else:
                errors += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            errors += 1

    print(f"\n{'='*60}")
    print(f"Done. Processed: {processed}, Skipped: {skipped}, Errors: {errors}")


if __name__ == "__main__":
    main()
