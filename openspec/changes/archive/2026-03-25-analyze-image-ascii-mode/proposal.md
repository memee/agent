## Why

Vision LLMs sometimes struggle to count or reason about discrete grid-like
structures (e.g. cells in a table, pixels in a sprite, characters in a grid
puzzle) when given a raw image. Converting the image to ASCII art first gives
the model a character grid it can process as plain text, which significantly
improves accuracy for these tasks.

## What Changes

- New `_image_to_ascii(image_path, width)` helper in `analyze_image.py` using
  Pillow: resizes the image to `width` columns (aspect-ratio-corrected for
  monospace char height), converts to grayscale, maps brightness to ASCII chars.
- `analyze_image` tool gains an optional `as_ascii: bool = False` parameter.
  When `True`, the image is converted to ASCII and sent as a plain-text message
  instead of a base64-encoded multimodal attachment.
- `Pillow>=11.0` added to project dependencies.
- Minor: `if image_url is not None:` → `if image_url:` in `delegate.py` (two sites).

## Capabilities

### New Capabilities

- `analyze-image-ascii-mode`: ASCII rendering of images via Pillow as an
  alternative input mode for the `analyze_image` tool.

### Modified Capabilities

- `analyze-image-tool`: `analyze_image` tool signature extended with `as_ascii`
  parameter; behaviour when `as_ascii=False` is unchanged.

## Impact

- **Modified**: `src/agent/builtin_tools/analyze_image.py`
- **Modified**: `src/agent/builtin_tools/delegate.py` (cosmetic only)
- **New dependency**: `Pillow>=11.0` in `pyproject.toml`
- **No breaking changes** — `as_ascii` defaults to `False`, existing callers unaffected.
