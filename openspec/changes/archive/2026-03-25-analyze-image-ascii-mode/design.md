## Context

`analyze_image` is the framework's only vision tool. It sends images as
base64-encoded multimodal attachments to a vision-capable LLM. This works well
for natural language description tasks, but fails for tasks requiring precise
counting or spatial reasoning over discrete grids (e.g. "how many black cells
are in row 3?") — vision models tend to approximate rather than enumerate.

ASCII art encoding trades visual fidelity for a character grid the model can
read token-by-token. The `Pillow` library is the standard Python image
processing library and is already widely available in the ecosystem.

## Goals / Non-Goals

**Goals:**

- Add `as_ascii=True` mode to `analyze_image` that converts the image to ASCII
  art via Pillow and sends it as plain text instead of a multimodal attachment.
- Correct for monospace font aspect ratio so the ASCII output is not vertically
  squashed.
- Keep `as_ascii=False` (default) behaviour completely unchanged.

**Non-Goals:**

- Color ASCII art (ANSI escape codes).
- Configurable ASCII character sets or width beyond the existing `width` parameter.
- Streaming responses.
- Supporting URLs in `as_ascii` mode (only local files).

## Decisions

### 1. Pillow imported lazily inside `_image_to_ascii`

**Decision**: `from PIL import Image` is placed inside the helper function body,
not at module top level.

**Rationale**: Keeps the import error local to the code path that actually needs
Pillow. If someone uses `analyze_image` with `as_ascii=False` and hasn't
installed Pillow, they get no error. Consistent with how other optional
dependencies are handled in the codebase.

### 2. Grayscale conversion + single brightness-to-char mapping

**Decision**: Convert image to `"L"` (grayscale) mode and map brightness
linearly to `_ASCII_CHARS = "@%#*+=-:. "` (dark to light, 10 levels).

**Rationale**: Simple and deterministic. The goal is a character grid for
counting/reasoning, not aesthetics — 10 brightness levels is sufficient.
Colour information is irrelevant for most grid-reasoning tasks.

### 3. Aspect ratio correction with 0.5 height factor

**Decision**: `height = int(orig_h / orig_w * width * 0.5)` halves the computed
height to compensate for monospace characters being ~2× taller than wide.

**Rationale**: Without this correction, the ASCII output appears vertically
stretched by 2×, distorting spatial relationships. The 0.5 factor is a standard
approximation for terminal fonts.

### 4. `as_ascii` as a bool parameter, not a separate tool

**Decision**: Extend `analyze_image` with `as_ascii: bool = False` rather than
registering a new `analyze_image_ascii` tool.

**Rationale**: The two modes share the same sandbox validation, model selection,
and client creation logic. A single tool with a mode flag is simpler for the LLM
to use — it only needs to remember one tool name and set a flag when appropriate.

## Risks / Trade-offs

- **ASCII quality at low resolution** — very small images produce coarse ASCII
  with little detail. Acceptable since the use case is grid puzzles / structured
  images, not photorealistic content.
- **Token cost** — a 100-char wide ASCII image with 50 rows is ~5 000 characters,
  comparable to or larger than a base64-encoded small image. For high-resolution
  images `as_ascii=True` may actually be more expensive in tokens.
  → Mitigation: the `width` parameter (default 100) can be reduced by callers.
- **Pillow not installed** — if `Pillow` is missing and `as_ascii=True` is used,
  Python raises `ImportError` at call time, not at import.
  → Mitigation: `Pillow>=11.0` is declared in `pyproject.toml`; explicit error.
