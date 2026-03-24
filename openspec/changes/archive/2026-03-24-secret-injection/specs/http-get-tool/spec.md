## MODIFIED Requirements

### Requirement: http_get tool performs an HTTP GET request

The library SHALL register an `http_get` tool in the `"builtin"` group with `domain="http"`.
It SHALL accept `url: str` and `headers: str` (an optional JSON-encoded object string, defaulting to `"{}"`).
It SHALL return the response body as a string.

It SHALL parse `headers` with `json.loads()` and merge the result into the outgoing request headers.
It SHALL raise `ValueError` if `headers` is not valid JSON.

It SHALL be registered with `validators={"url": http_url_validator}` so the URL is validated before the request is made.

It SHALL use `sandbox.timeout` as the request timeout and raise `ValueError` if the response body exceeds `sandbox.max_response_bytes`, where `sandbox` is the `HttpSandbox` instance routed by the registry.

#### Scenario: Public URL returns response body

- **WHEN** `http_get` is called with a reachable public URL
- **THEN** returns the response body as a string

#### Scenario: GET with custom headers sends them in the request

- **WHEN** `http_get` is called with `headers='{"X-Api-Key": "secret123"}'`
- **THEN** the outgoing request includes the `X-Api-Key` header with value `"secret123"`

#### Scenario: GET with default empty headers works normally

- **WHEN** `http_get` is called without a `headers` argument
- **THEN** the request is sent without extra headers (default behaviour unchanged)

#### Scenario: Invalid JSON headers raises ValueError before request

- **WHEN** `http_get` is called with a `headers` string that is not valid JSON
- **THEN** raises `ValueError` before any network request is made

#### Scenario: Private IP is blocked before request is made

- **WHEN** `http_get` is called with a URL resolving to a private IP and `block_private_ips=True`
- **THEN** raises `PermissionError` (from `http_url_validator`) before any network connection is made

#### Scenario: Response exceeding size limit is rejected

- **WHEN** `http_get` receives a response body larger than `sandbox.max_response_bytes`
- **THEN** raises `ValueError` with a message indicating the size limit

#### Scenario: Request times out

- **WHEN** the remote server does not respond within `sandbox.timeout` seconds
- **THEN** raises `TimeoutError`

### Requirement: http_get is auto-registered on import

`http_get` SHALL be registered automatically when `from agent import tools` is executed.

#### Scenario: http_get available after import

- **WHEN** `from agent import tools` is executed
- **THEN** `"http_get"` appears in `tools.names("builtin")`
