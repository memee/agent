from pathlib import Path

from agent.sandbox import FileSandbox
from agent.tool import tool
from agent.validators import file_path_validator


@tool("write_file", group="builtin", validators={"path": file_path_validator}, domain="filesystem")
def write_file(path: str, content: str, sandbox: FileSandbox = FileSandbox.default()) -> str:
    """Write UTF-8 text content to a file on disk and return the resolved path.

    The path is validated against the current sandbox before writing.
    Parent directories are created if they do not exist.
    An existing file at the destination is overwritten silently.
    Raises PermissionError if the path is outside the allowed directory or
    matches a blocked pattern. Raises ValueError if the content exceeds the
    sandbox size limit.
    """
    resolved = path if isinstance(path, Path) else Path(path)

    encoded = content.encode("utf-8")
    if len(encoded) > sandbox.max_file_bytes:
        raise ValueError(
            f"Content is {len(encoded)} bytes, exceeding the limit of "
            f"{sandbox.max_file_bytes} bytes"
        )

    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_bytes(encoded)
    return str(resolved)
