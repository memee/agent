import base64
import mimetypes
import os
from pathlib import Path

from agent.client import create_client
from agent.sandbox import FileSandbox
from agent.tool import tool
from agent.validators import file_path_validator

# ASCII chars ordered from dark to light
_ASCII_CHARS = "@%#*+=-:. "


def _image_to_ascii(image_path: str, width: int = 100) -> str:
    """Convert an image file to an ASCII art string.

    Resizes the image to `width` columns (preserving aspect ratio, correcting
    for the ~2:1 height/width ratio of monospace characters), converts to
    grayscale, and maps each pixel to an ASCII character.
    """
    from PIL import Image

    img = Image.open(image_path).convert("L")
    orig_w, orig_h = img.size
    # Monospace chars are ~twice as tall as wide, so halve the height
    height = max(1, int(orig_h / orig_w * width * 0.5))
    img = img.resize((width, height))

    lines: list[str] = []
    for y in range(height):
        row = ""
        for x in range(width):
            brightness = img.getpixel((x, y))  # 0–255
            index = brightness * (len(_ASCII_CHARS) - 1) // 255
            row += _ASCII_CHARS[index]
        lines.append(row)

    return "\n".join(lines)


@tool("analyze_image", group="builtin", validators={"image_path": file_path_validator}, domain="filesystem")
def analyze_image(
    image_path: str,
    prompt: str,
    as_ascii: bool = False,
    sandbox: FileSandbox = FileSandbox.default(),
) -> str:
    """Analyze a local image file using a vision-capable LLM.

    By default (as_ascii=False) reads the file, base64-encodes it, and sends
    a multimodal vision request to the model specified by the VISION_MODEL
    environment variable (default: gpt-4o).

    When as_ascii=True, converts the image to ASCII art first and sends the
    prompt together with the ASCII representation as a plain-text message
    (no image attachment). Useful when the model struggles to count discrete
    grid cells from a raw image — ASCII gives it a character grid it can
    reason over directly.

    Returns the model's textual response.
    Raises PermissionError if image_path fails filesystem sandbox validation.
    """
    model = os.environ.get("VISION_MODEL") or "gpt-4o"
    client = create_client()

    if as_ascii:
        ascii_art = _image_to_ascii(image_path)
        text = f"{prompt}\n\nASCII representation of the image:\n```\n{ascii_art}\n```"
        messages = [{"role": "user", "content": text}]
    else:
        image_bytes = Path(image_path).read_bytes()
        encoded = base64.b64encode(image_bytes).decode("ascii")
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if not mime_type:
            mime_type = "image/jpeg"
        data_url = f"data:{mime_type};base64,{encoded}"
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content
