from pathlib import Path

import httpx

from agent.sandbox import SandboxConfig
from agent.tool import tool
from agent.validators import file_path_validator, http_url_validator


@tool("http_download", group="builtin", domain=None)
def http_download(
    url: str, path: str, sandbox: SandboxConfig = SandboxConfig.default()
) -> str:
    """Download a binary file from a URL and save it directly to disk.

    Binary data never enters the LLM context window — only the resolved path
    is returned.
    The URL is validated against the HTTP sandbox before the request is made.
    The destination path is validated against the filesystem sandbox.
    Parent directories are created if they do not exist.
    An existing file at the destination is overwritten silently.
    Raises PermissionError if the URL or path fails sandbox validation.
    Raises TimeoutError if the server does not respond in time.
    """
    http_url_validator(url, sandbox.http)
    resolved = file_path_validator(path, sandbox.filesystem)
    resolved.parent.mkdir(parents=True, exist_ok=True)

    try:
        with httpx.Client(
            timeout=sandbox.http.timeout, follow_redirects=True, max_redirects=5
        ) as client:
            response = client.get(url)
    except httpx.TimeoutException as e:
        raise TimeoutError(
            f"Request to '{url}' timed out after {sandbox.http.timeout}s"
        ) from e

    resolved.write_bytes(response.content)
    return str(resolved)
