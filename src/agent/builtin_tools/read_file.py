from pathlib import Path

from agent import tools
from agent.sandbox import FileSandbox
from agent.validators import file_path_validator


@tools.register("read_file", "builtin", validators={"path": file_path_validator}, domain="filesystem")
def read_file(path: str, sandbox: FileSandbox = FileSandbox.default()) -> str:
    """Read a file from disk and return its text content.

    The path is validated and resolved against the current sandbox before the
    file is opened. Raises PermissionError if the path is outside the allowed
    directory or matches a blocked pattern. Raises ValueError if the file
    exceeds the sandbox size limit.
    """
    # After validation, path is an absolute Path object
    resolved = path if isinstance(path, Path) else Path(path)

    size = resolved.stat().st_size
    if size > sandbox.max_file_bytes:
        raise ValueError(
            f"File '{resolved}' is {size} bytes, exceeding the limit of "
            f"{sandbox.max_file_bytes} bytes"
        )

    return resolved.read_text()
