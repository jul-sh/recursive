# Recursive Charon

A customized fork of [Recursive Sans & Mono](https://github.com/arrowtype/recursive) adapted to match the proportions of Iosevka Charon.

## What changed

### Narrower character cell

The monospace cell width was compressed from 600 units to 500 units (a ~17% reduction), bringing it in line with Iosevka Charon's proportions. All horizontal coordinates, advance widths, component offsets, anchors, guidelines, kerning, and stem snap values were scaled accordingly. Vertical metrics were left untouched.

### Rounder dots

Dot contours across the family (period, ellipsis, question mark, dot accents) were replaced with proper circular Bezier curves. Rounded dots from the Casual masters were also propagated to the Linear masters for consistency. Dots on `i` and `j` were shrunk by 20%.

### Default stylistic sets

Several stylistic sets are enabled by default via contextual alternates: `ss02`, `ss04`, `ss05`, `ss06`, `ss07`, `ss08`, and `ss12`.

### Cursive default

The `CRSV` (Cursive) axis default was changed from `0.5` (auto) to `1` (always cursive).

### Design fixes

- Fixed italic `f` rendering across all masters
- Fixed top-bar overhangs on B, R, F, P, E, D, J
- Corrected Cursive axis coordinates
- Flattened weight scaling
- Improved macOS Font Book display via STAT table elidable flags

## Variable axes

Same as the original Recursive, with the noted default change on the Cursive axis:

| Axis      | Tag    | Range       | Default | Description                          |
| --------- | ------ | ----------- | ------- | ------------------------------------ |
| Monospace | `MONO` | 0 to 1      | 0       | Sans (proportional) to Mono (fixed)  |
| Casual    | `CASL` | 0 to 1      | 0       | Linear to Casual                     |
| Weight    | `wght` | 300 to 1000 | 300     | Light to ExtraBlack                  |
| Slant     | `slnt` | 0 to -15    | 0       | Upright to Slanted (~15 degrees)     |
| Cursive   | `CRSV` | 0, 0.5, 1   | **1**   | Roman (0), auto (0.5), cursive (1)   |

## Building

Fonts are built automatically via GitHub Actions on push to `main`. To build locally:

```bash
virtualenv -p python3 venv
source venv/bin/activate
pip install -U -r requirements.txt
cd mastering
python build.py --all --version 1.085
```

## License

Licensed under the [SIL Open Font License v1.1](OFL.txt), same as the original Recursive.

## Credits

- Original [Recursive](https://github.com/arrowtype/recursive) design by Stephen Nixon / [Arrow Type](https://arrowtype.com)
- Charon modifications by Juliette Pluto
