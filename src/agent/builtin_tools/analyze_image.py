import base64
import mimetypes
import os
from pathlib import Path

from agent.client import create_client
from agent.sandbox import FileSandbox
from agent.tool import tool
from agent.validators import file_path_validator


@tool("analyze_image", group="builtin", validators={"image_path": file_path_validator}, domain="filesystem")
def analyze_image(
    image_path: str, prompt: str, sandbox: FileSandbox = FileSandbox.default()
) -> str:
    """Analyze a local image file using a vision-capable LLM.

    Reads the file at image_path, base64-encodes it, and sends a one-shot
    vision request to the model specified by the VISION_MODEL environment
    variable (default: gpt-4o).

    Returns the model's textual response.
    Raises PermissionError if image_path fails filesystem sandbox validation.
    """
    # image_path is already resolved to an absolute Path by the registry validator
    image_bytes = Path(image_path).read_bytes()
    encoded = base64.b64encode(image_bytes).decode("ascii")

    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type:
        mime_type = "image/jpeg"

    data_url = f"data:{mime_type};base64,{encoded}"

    model = os.environ.get("VISION_MODEL") or "gpt-4o"
    client = create_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    return response.choices[0].message.content
