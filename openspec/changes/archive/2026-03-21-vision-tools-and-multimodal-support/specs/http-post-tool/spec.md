## ADDED Requirements

### Requirement: http_post tool sends an HTTP POST request with JSON body

The library SHALL register an `http_post` tool in the `"builtin"` group with `domain="http"`.
It SHALL accept `url: str` and `body: str` (a JSON-encoded string).

It SHALL parse `body` with `json.loads()` and pass the result as `json=` to httpx, so the
request is sent with `Content-Type: application/json`.

It SHALL be registered with `validators={"url": http_url_validator}` so the URL is validated
before the request is made.

It SHALL use `sandbox.timeout` as the request timeout and raise `ValueError` if the response
body exceeds `sandbox.max_response_bytes`, where `sandbox` is the `HttpSandbox` instance
routed by the registry.

It SHALL return the response body as a string.

#### Scenario: POST with valid JSON body returns response

- **WHEN** `http_post` is called with a reachable public URL and a valid JSON string body
- **THEN** sends a POST request with `Content-Type: application/json` and returns the response body as a string

#### Scenario: Invalid JSON body raises ValueError before request

- **WHEN** `http_post` is called with a body string that is not valid JSON
- **THEN** raises `ValueError` before any network request is made

#### Scenario: Private IP is blocked before request

- **WHEN** `http_post` is called with a URL resolving to a private IP and `block_private_ips=True`
- **THEN** raises `PermissionError` from `http_url_validator` before any network connection

#### Scenario: Response exceeding size limit is rejected

- **WHEN** `http_post` receives a response body larger than `sandbox.max_response_bytes`
- **THEN** raises `ValueError` with a message indicating the size limit

#### Scenario: Request times out

- **WHEN** the remote server does not respond within `sandbox.timeout` seconds
- **THEN** raises `TimeoutError`

### Requirement: http_post is auto-registered on import

`http_post` SHALL be registered automatically when `from agent import tools` is executed.

#### Scenario: http_post available after import

- **WHEN** `from agent import tools` is executed
- **THEN** `"http_post"` appears in `tools.names("builtin")`
