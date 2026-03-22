#!/usr/bin/env python3
"""
Replace default glyphs with italic variants for preferred characters.

Characters that should ALWAYS use italic form (their .italic becomes the default):
All chars EXCEPT: y, a, s, g, h, j, k, z, x, c, n, m

So always-italic base chars: b, d, e, f, i, l, q, r, u, v, w, dotlessi
(dotlessj stays excluded since j is excluded)
"""

import os
import re
import plistlib
import shutil
import glob as globmod

# Base characters that should ALWAYS use italic
# (all lowercase with italic variants, EXCEPT y a s g h j k z x c n m)
ALWAYS_ITALIC_BASES = {'b', 'd', 'e', 'f', 'i', 'l', 'q', 'r', 'u', 'v', 'w', 'dotlessi'}

# Characters to KEEP roman (excluded from always-italic)
EXCLUDED_BASES = {'y', 'a', 's', 'g', 'h', 'j', 'k', 'z', 'x', 'c', 'n', 'm', 'dotlessj'}

# Root directory
ROOT = "/home/user/recursive-charon"
UFO_DIR = os.path.join(ROOT, "src/ufo")

def get_all_ufos():
    """Find all UFO directories."""
    ufos = []
    for subdir in ['mono', 'sans']:
        path = os.path.join(UFO_DIR, subdir)
        for name in sorted(os.listdir(path)):
            if name.endswith('.ufo'):
                ufos.append(os.path.join(path, name))
    return ufos

def get_base_char(glyph_name):
    """Get the base character from an accented glyph name.
    e.g., 'eacute.italic' -> 'e', 'uhorn.italic' -> 'u', 'dotlessi.italic' -> 'dotlessi'
    """
    # Remove .italic suffix
    name = glyph_name.replace('.italic', '')

    # Special cases
    if name.startswith('dotlessi'):
        return 'dotlessi'
    if name.startswith('dotlessj'):
        return 'dotlessj'

    # For ligatures
    if name in ('fi', 'fl', 'f_f', 'f_f_i', 'f_f_l'):
        return name  # Handle ligatures separately
    if name in ('dz', 'dzcaron', 'lj', 'nj', 'Lj', 'Nj'):
        return name  # Mixed ligatures

    # For single-letter bases: the base char is the first letter
    # e.g., eacute -> e, uhorn -> u, etc.
    if len(name) == 1:
        return name

    # For accented forms, the base is typically the first character
    return name[0]

def should_always_be_italic(glyph_name):
    """Check if a glyph's .italic variant should become the default."""
    if not glyph_name.endswith('.italic'):
        return False

    base_name = glyph_name.replace('.italic', '')
    base_char = get_base_char(glyph_name)

    # Handle ligatures
    if base_name in ('fi', 'fl', 'f_f', 'f_f_i', 'f_f_l'):
        return True  # All components are always-italic
    if base_name in ('dz', 'dzcaron', 'lj', 'nj', 'Lj', 'Nj'):
        return False  # Mixed/excluded components

    return base_char in ALWAYS_ITALIC_BASES

def process_ufo(ufo_path):
    """Process a single UFO directory."""
    glyphs_dir = os.path.join(ufo_path, 'glyphs')
    contents_path = os.path.join(glyphs_dir, 'contents.plist')

    if not os.path.exists(contents_path):
        print(f"  No contents.plist in {ufo_path}")
        return

    with open(contents_path, 'rb') as f:
        contents = plistlib.load(f)

    # Find all italic glyphs that should become defaults
    italics_to_merge = {}
    for glyph_name in list(contents.keys()):
        if should_always_be_italic(glyph_name):
            base_name = glyph_name.replace('.italic', '')
            if base_name in contents:
                italics_to_merge[glyph_name] = base_name

    if not italics_to_merge:
        print(f"  No italic glyphs to merge in {os.path.basename(ufo_path)}")
        return

    print(f"  Processing {os.path.basename(ufo_path)}: {len(italics_to_merge)} glyphs to merge")

    # Step 1: Replace default glyphs with italic content
    for italic_name, base_name in italics_to_merge.items():
        italic_filename = contents[italic_name]
        base_filename = contents[base_name]

        italic_path = os.path.join(glyphs_dir, italic_filename)
        base_path = os.path.join(glyphs_dir, base_filename)

        if not os.path.exists(italic_path):
            print(f"    WARNING: {italic_filename} not found, skipping")
            continue

        # Read the italic glif
        with open(italic_path, 'r', encoding='utf-8') as f:
            italic_content = f.read()

        # Change the glyph name from "X.italic" to "X"
        italic_content = re.sub(
            r'(<glyph\s+name=")' + re.escape(italic_name) + r'"',
            r'\g<1>' + base_name + '"',
            italic_content
        )

        # Write to the base glyph file
        with open(base_path, 'w', encoding='utf-8') as f:
            f.write(italic_content)

        # Delete the italic glif file
        os.remove(italic_path)

        # Remove italic entry from contents
        del contents[italic_name]

    # Step 2: Update component references in ALL remaining glyphs
    # Any component base="X.italic" where X is always-italic -> base="X"
    for glyph_name, filename in contents.items():
        filepath = os.path.join(glyphs_dir, filename)
        if not os.path.exists(filepath) or filename == 'contents.plist':
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Update component references
        for italic_name in italics_to_merge.keys():
            base_name = italic_name.replace('.italic', '')
            # Replace base="X.italic" with base="X"
            content = content.replace(f'base="{italic_name}"', f'base="{base_name}"')

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

    # Save updated contents.plist
    with open(contents_path, 'wb') as f:
        plistlib.dump(contents, f)

    print(f"    Done. Merged {len(italics_to_merge)} italic glyphs.")

def update_designspace():
    """Remove always-italic chars from autoitalic substitution rules."""
    ds_path = os.path.join(UFO_DIR, "recursive-MONO_CASL_wght_slnt_ital--full_gsub.designspace")

    with open(ds_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse and filter <sub> elements in autoitalic rules
    lines = content.split('\n')
    new_lines = []
    in_autoitalic = False
    removed = 0

    for line in lines:
        # Track if we're in an autoitalic rule
        if 'name="mono autoitalic"' in line or 'name="sans autoitalic"' in line:
            in_autoitalic = True
            new_lines.append(line)
            continue

        if in_autoitalic and '</rule>' in line:
            in_autoitalic = False
            new_lines.append(line)
            continue

        if in_autoitalic and '<sub ' in line:
            # Extract the glyph name being substituted
            match = re.search(r'name="([^"]+)".*with="([^"]+)"', line)
            if match:
                from_name = match.group(1)
                to_name = match.group(2)
                # Check if this is an always-italic glyph
                if to_name.endswith('.italic') and should_always_be_italic(to_name):
                    removed += 1
                    continue  # Skip this line

        new_lines.append(line)

    with open(ds_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"  Removed {removed} substitutions from autoitalic rules")

def update_feature_files():
    """Update feature files to reflect the changes."""
    features_dir = os.path.join(ROOT, "src/features/features")

    # --- Update common.fea ---
    common_path = os.path.join(features_dir, "common.fea")
    with open(common_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # @italI: i.italic etc no longer exist since i is always italic
    # These should now point to the base glyphs
    # @italI = [dotlessi.italic i.italic ...] -> [dotlessi i ...]
    # But wait - these classes are defined but might not be used in substitutions
    # We need to either remove them or update them

    # For @italI, @italL, @italR - update to point to base glyphs (since italic IS the base now)
    # Actually, these classes may still be needed for other features
    # Let's update them to reference the base glyphs

    # Update @italI: replace X.italic with X for always-italic chars
    content = re.sub(
        r'@italI = \[.*?\];',
        lambda m: update_class(m.group(0), 'italic'),
        content
    )

    # Update @italL
    content = re.sub(
        r'@italL = .*?\];',
        lambda m: update_class(m.group(0), 'italic'),
        content
    )

    # Update @italR
    content = re.sub(
        r'@italR = .*?\];',
        lambda m: update_class(m.group(0), 'italic'),
        content
    )

    # @smplI has dotlessi.italic as first element - update it
    content = re.sub(
        r'@smplI = \[.*?\];',
        lambda m: update_class(m.group(0), 'italic'),
        content
    )

    # Update @curvyDiagonals - remove always-italic chars (v, w and accented)
    # v.italic -> v, w.italic -> w (these are now the defaults)
    content = re.sub(
        r'@curvyDiagonals = \[.*?\];',
        lambda m: update_class(m.group(0), 'italic'),
        content
    )

    # Update @romanDiagonals to match - remove corresponding entries
    # This is tricky because @curvyDiagonals and @romanDiagonals must have same length
    # Since v.italic -> v and w.italic -> w, the curvy and roman are now the same for these
    # We need to remove both from both arrays

    # Actually, let me handle ss07 differently
    # After changes: v IS the curvy/italic shape, w IS the curvy/italic shape
    # ss07 substitutes curvy diagonals with roman diagonals
    # For v and w, there's no longer a roman version, so we need to remove them
    # For k, y, z, x (excluded) - k.italic, y.italic etc still exist

    # Let's rebuild these arrays properly
    curvy_items = re.search(r'@curvyDiagonals = \[(.*?)\]', content)
    roman_items = re.search(r'@romanDiagonals = \[(.*?)\]', content)

    if curvy_items and roman_items:
        curvy_list = curvy_items.group(1).split()
        roman_list = roman_items.group(1).split()

        new_curvy = []
        new_roman = []
        for c, r in zip(curvy_list, roman_list):
            # If the curvy version is an always-italic glyph, skip both
            if c.endswith('.italic') and should_always_be_italic(c):
                continue
            new_curvy.append(c)
            new_roman.append(r)

        content = content.replace(
            f'@curvyDiagonals = [{curvy_items.group(1)}]',
            f'@curvyDiagonals = [{" ".join(new_curvy)}]'
        )
        content = content.replace(
            f'@romanDiagonals = [{roman_items.group(1)}]',
            f'@romanDiagonals = [{" ".join(new_roman)}]'
        )

    # Update @j_for_ij, @i_for_ij, @iacute_for_ij
    # i.italic -> i (since i is always italic, i.italic no longer exists)
    # j.italic stays (j is excluded)
    # Replace i.italic with i, iacute.italic with iacute in these classes
    # But i is already in @i_for_ij, so just remove i.italic

    # @j_for_ij = [j j.italic]; -> keep as is (j is excluded)
    # @i_for_ij = [i i.mono i.italic i.simple] -> [i i.mono i.simple]
    # @iacute_for_ij = [iacute iacute.mono iacute.italic iacute.simple] -> [iacute iacute.mono iacute.simple]

    content = re.sub(r'\bi\.italic\b', 'i', content)
    content = re.sub(r'\biacute\.italic\b', 'iacute', content)

    # Fix any duplicates created (e.g., "i i" from replacing i.italic with i when i already exists)
    # Handle in @i_for_ij specifically
    content = re.sub(
        r'@i_for_ij\s*=\s*\[([^\]]+)\]',
        lambda m: '@i_for_ij = [' + ' '.join(dict.fromkeys(m.group(1).split())) + ']',
        content
    )
    content = re.sub(
        r'@iacute_for_ij\s*=\s*\[([^\]]+)\]',
        lambda m: '@iacute_for_ij = [' + ' '.join(dict.fromkeys(m.group(1).split())) + ']',
        content
    )

    with open(common_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("  Updated common.fea")

    # --- Update ccmp.fea ---
    ccmp_path = os.path.join(features_dir, "ccmp.fea")
    with open(ccmp_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # @base_lc: remove X.italic entries for always-italic chars (they're now just X)
    # Need to be careful not to create duplicates
    base_lc_match = re.search(r'@base_lc = \[(.*?)\]', content)
    if base_lc_match:
        items = base_lc_match.group(1).split()
        new_items = []
        seen = set()
        for item in items:
            if item.endswith('.italic'):
                base = item.replace('.italic', '')
                base_char = get_base_char(item)
                if base_char in ALWAYS_ITALIC_BASES:
                    # Skip - the base version already covers this
                    continue
            if item not in seen:
                new_items.append(item)
                seen.add(item)
        content = content.replace(
            f'@base_lc = [{base_lc_match.group(1)}]',
            f'@base_lc = [{" ".join(new_items)}]'
        )

    # Dotless lookup: [i i.italic i.mono j j.italic]
    # i.italic no longer exists, remove it (i already covers it)
    # j.italic stays (j is excluded)
    content = content.replace(
        "[i i.italic i.mono j j.italic]' [ @lc_marks_below @marks_below ] @lc_marks by [ dotlessi dotlessi.italic dotlessi.mono dotlessj dotlessj.italic ]",
        "[i i.mono j j.italic]' [ @lc_marks_below @marks_below ] @lc_marks by [ dotlessi dotlessi.mono dotlessj dotlessj.italic ]"
    )
    content = content.replace(
        "[i i.italic i.mono j j.italic]' @lc_marks by [ dotlessi dotlessi.italic dotlessi.mono dotlessj dotlessj.italic ]",
        "[i i.mono j j.italic]' @lc_marks by [ dotlessi dotlessi.mono dotlessj dotlessj.italic ]"
    )

    # caron lookup: l.italic no longer exists
    content = content.replace(
        "[l l.italic l.mono l.simple l.sans]",
        "[l l.mono l.simple l.sans]"
    )

    # replacements lookup: remove lines with always-italic .italic variants
    # Lines like: sub a.italic ogonekcomb by aogonek.italic; -> KEEP (a is excluded)
    # Lines like: sub e.italic ogonekcomb by eogonek.italic; -> REMOVE (e is always italic)
    # But wait - after the change, there is no e.italic. e IS italic.
    # So "sub e ogonekcomb by eogonek;" already handles this.

    lines = content.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # Check if this line references an always-italic .italic glyph
        skip = False
        if stripped.startswith('sub '):
            # Find all .italic references in the line
            italic_refs = re.findall(r'\b(\w+)\.italic\b', stripped)
            for ref in italic_refs:
                base_char = get_base_char(ref + '.italic')
                if base_char in ALWAYS_ITALIC_BASES:
                    skip = True
                    break
        if skip:
            continue
        new_lines.append(line)
    content = '\n'.join(new_lines)

    with open(ccmp_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("  Updated ccmp.fea")

    # --- Update liga.fea ---
    liga_path = os.path.join(features_dir, "liga.fea")
    with open(liga_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # sub f i.italic by fi; -> sub f i by fi; (i.italic no longer exists, i IS italic)
    # sub f f i.italic by f_f_i; -> sub f f i by f_f_i;
    content = content.replace('i.italic', 'i')

    with open(liga_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("  Updated liga.fea")

    # --- Update locl.fea ---
    locl_path = os.path.join(features_dir, "locl.fea")
    with open(locl_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # dotlessi.italic -> dotlessi (since dotlessi is always italic now)
    content = content.replace('dotlessi.italic', 'dotlessi')
    # Fix any duplicates in lists
    content = re.sub(r'\[dotlessi dotlessi dotlessi\.mono\]', '[dotlessi dotlessi.mono]', content)

    with open(locl_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("  Updated locl.fea")

    # --- Update aalt.fea ---
    aalt_path = os.path.join(features_dir, "aalt.fea")
    with open(aalt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # For always-italic chars, remove lines that reference X.italic
    # e.g., "sub b from [b b.italic];" -> "sub b from [b];" but that's weird
    # Actually, since X.italic no longer exists, we need to remove those references
    # "sub b from [b b.italic];" -> just remove b.italic from the list
    # "sub b.italic from [b.italic b];" -> remove entire line (b.italic doesn't exist)

    lines = content.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()

        if stripped.startswith('sub ') and 'from' in stripped:
            # Check if the "from" glyph (left of "from") is an always-italic .italic
            match = re.match(r'\s*sub\s+(\S+)\s+from\s+\[([^\]]*)\]', stripped)
            if match:
                from_glyph = match.group(1)
                alternatives = match.group(2).split()

                if from_glyph.endswith('.italic'):
                    base_char = get_base_char(from_glyph)
                    if base_char in ALWAYS_ITALIC_BASES:
                        # Skip entire line - this glyph no longer exists
                        continue

                # Remove always-italic .italic entries from alternatives list
                new_alts = []
                for alt in alternatives:
                    if alt.endswith('.italic'):
                        base_char = get_base_char(alt)
                        if base_char in ALWAYS_ITALIC_BASES:
                            continue
                    new_alts.append(alt)

                if new_alts != alternatives:
                    indent = line[:len(line) - len(line.lstrip())]
                    new_line = f"{indent}sub {from_glyph} from [{' '.join(new_alts)}];"
                    new_lines.append(new_line)
                    continue

        new_lines.append(line)

    content = '\n'.join(new_lines)

    with open(aalt_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("  Updated aalt.fea")

def update_class(class_def, suffix):
    """Update a glyph class definition, replacing always-italic .italic refs with base names."""
    # Extract the items
    match = re.search(r'\[(.*?)\]', class_def)
    if not match:
        return class_def

    items = match.group(1).split()
    new_items = []
    seen = set()
    for item in items:
        if item.endswith(f'.{suffix}'):
            base = item[:-len(f'.{suffix}')]
            base_char = get_base_char(item)
            if base_char in ALWAYS_ITALIC_BASES:
                # Replace with base name, but only if not already present
                if base not in seen:
                    new_items.append(base)
                    seen.add(base)
                continue
        if item not in seen:
            new_items.append(item)
            seen.add(item)

    return class_def[:match.start(1)] + ' '.join(new_items) + class_def[match.end(1):]

def main():
    print("=== Replacing default glyphs with italic variants ===")
    print(f"Always-italic base chars: {sorted(ALWAYS_ITALIC_BASES)}")
    print(f"Excluded (keep roman): {sorted(EXCLUDED_BASES)}")
    print()

    # Process all UFOs
    ufos = get_all_ufos()
    print(f"Found {len(ufos)} UFO directories")

    for ufo in ufos:
        process_ufo(ufo)

    print()
    print("=== Updating designspace ===")
    update_designspace()

    print()
    print("=== Updating feature files ===")
    update_feature_files()

    print()
    print("=== Done! ===")

if __name__ == '__main__':
    main()
