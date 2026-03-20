## ADDED Requirements

### Requirement: http_get tool performs an HTTP GET request

The library SHALL register an `http_get` tool in the `"builtin"` group. It SHALL accept a single `url: str` argument and return the response body as a string.

It SHALL be registered with `validators={"url": http_url_validator}` so the URL is validated before the request is made.

It SHALL use `sandbox.http_timeout` as the request timeout and raise `ValueError` if the response body exceeds `sandbox.max_response_bytes`.

#### Scenario: Public URL returns response body

- **WHEN** `http_get` is called with a reachable public URL
- **THEN** returns the response body as a string

#### Scenario: Private IP is blocked before request is made

- **WHEN** `http_get` is called with a URL resolving to a private IP and `block_private_ips=True`
- **THEN** raises `PermissionError` (from `http_url_validator`) before any network connection is made

#### Scenario: Response exceeding size limit is rejected

- **WHEN** `http_get` receives a response body larger than `sandbox.max_response_bytes`
- **THEN** raises `ValueError` with a message indicating the size limit

#### Scenario: Request times out

- **WHEN** the remote server does not respond within `sandbox.http_timeout` seconds
- **THEN** raises `TimeoutError`

### Requirement: http_get is auto-registered on import

`http_get` SHALL be registered automatically when `from agent import tools` is executed.

#### Scenario: http_get available after import

- **WHEN** `from agent import tools` is executed
- **THEN** `"http_get"` appears in `tools.names("builtin")`
