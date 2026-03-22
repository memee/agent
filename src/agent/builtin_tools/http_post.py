import json

import httpx

from agent.sandbox import HttpSandbox
from agent.tool import tool
from agent.validators import http_url_validator


@tool("http_post", group="builtin", validators={"url": http_url_validator}, domain="http")
def http_post(url: str, body: str, sandbox: HttpSandbox = HttpSandbox.default()) -> str:
    """Send an HTTP POST request with a JSON body and return the response body as text.

    The URL is validated against the current sandbox before the request is made.
    The body must be a valid JSON string — it is parsed internally and sent with
    Content-Type: application/json.
    Raises ValueError if body is not valid JSON.
    Raises PermissionError if the URL resolves to a private IP or is not in the
    allowed hosts list. Raises ValueError if the response body exceeds the size
    limit. Raises TimeoutError if the server does not respond in time.
    """
    try:
        parsed_body = json.loads(body)
    except json.JSONDecodeError as e:
        raise ValueError(f"body is not valid JSON: {e}") from e

    try:
        with httpx.Client(timeout=sandbox.timeout, follow_redirects=True, max_redirects=5) as client:
            response = client.post(url, json=parsed_body)
    except httpx.TimeoutException as e:
        raise TimeoutError(f"Request to '{url}' timed out after {sandbox.timeout}s") from e

    content = response.content
    if len(content) > sandbox.max_response_bytes:
        raise ValueError(
            f"Response from '{url}' is {len(content)} bytes, exceeding the limit of "
            f"{sandbox.max_response_bytes} bytes"
        )

    return response.text
