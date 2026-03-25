## ADDED Requirements

### Requirement: Image can be converted to ASCII art using Pillow

The system SHALL provide an internal `_image_to_ascii(image_path: str, width: int = 100) -> str`
function in `src/agent/builtin_tools/analyze_image.py`.

It SHALL open the image with `PIL.Image`, convert it to grayscale (`"L"` mode),
resize it to `width` columns with height computed as
`max(1, int(orig_h / orig_w * width * 0.5))` to correct for monospace aspect ratio,
and map each pixel's brightness (0–255) to a character from
`_ASCII_CHARS = "@%#*+=-:. "` (index 0 = darkest, index 9 = lightest).

It SHALL return the result as a multi-line string with one line per row.

#### Scenario: Dark pixel maps to dense character

- **WHEN** a pixel has brightness 0
- **THEN** it maps to `"@"` (index 0 in `_ASCII_CHARS`)

#### Scenario: Light pixel maps to sparse character

- **WHEN** a pixel has brightness 255
- **THEN** it maps to `" "` (last character in `_ASCII_CHARS`)

#### Scenario: Aspect ratio corrected for monospace font

- **WHEN** a 200×100 image is converted with `width=100`
- **THEN** the output has 100 columns and approximately 25 rows (0.5 factor applied)

#### Scenario: Minimum height is 1 row

- **WHEN** an image is very wide and `width` is very small, causing computed height < 1
- **THEN** height is clamped to 1
