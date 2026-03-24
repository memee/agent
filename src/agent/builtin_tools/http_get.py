import json

import httpx

from agent.sandbox import HttpSandbox
from agent.tool import tool
from agent.validators import http_url_validator


@tool("http_get", group="builtin", validators={"url": http_url_validator}, domain="http")
def http_get(url: str, headers: str = "{}", sandbox: HttpSandbox = HttpSandbox.default()) -> str:
    """Perform an HTTP GET request and return the response body as text.

    The URL is validated against the current sandbox before the request is made.
    The headers argument is an optional JSON object string of extra request headers.
    Raises ValueError if headers is not valid JSON.
    Raises PermissionError if the URL resolves to a private IP or is not in the
    allowed hosts list. Raises ValueError if the response body exceeds the size
    limit. Raises TimeoutError if the server does not respond in time.
    """
    try:
        parsed_headers = json.loads(headers)
    except json.JSONDecodeError as e:
        raise ValueError(f"headers is not valid JSON: {e}") from e

    try:
        with httpx.Client(timeout=sandbox.timeout, follow_redirects=True, max_redirects=5) as client:
            response = client.get(url, headers=parsed_headers)
    except httpx.TimeoutException as e:
        raise TimeoutError(f"Request to '{url}' timed out after {sandbox.timeout}s") from e

    content = response.content
    if len(content) > sandbox.max_response_bytes:
        raise ValueError(
            f"Response from '{url}' is {len(content)} bytes, exceeding the limit of "
            f"{sandbox.max_response_bytes} bytes"
        )

    return response.text
