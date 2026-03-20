## ADDED Requirements

### Requirement: HttpSandbox holds HTTP-access constraints

`HttpSandbox` SHALL be a dataclass in `agent/sandbox.py` with the following fields:

- `block_private_ips: bool` — if `True`, requests to private/loopback IP ranges are rejected
- `allowed_hosts: list[str] | None` — if set, only these hostnames are permitted; `None` allows all
- `timeout: float` — timeout in seconds for HTTP requests
- `max_response_bytes: int` — maximum response body size in bytes

Default values: `block_private_ips=True`, `allowed_hosts=None`, `timeout=10.0`, `max_response_bytes=500_000`.

#### Scenario: Default construction

- **WHEN** `HttpSandbox()` is instantiated with no arguments
- **THEN** `block_private_ips` is `True`, `allowed_hosts` is `None`, `timeout` is `10.0`, `max_response_bytes` is `500_000`

### Requirement: HttpSandbox provides three class-method presets

`HttpSandbox` SHALL expose three class methods:

- `HttpSandbox.default()` — same as default construction
- `HttpSandbox.strict()` — `block_private_ips=True`, `timeout=5.0`, `max_response_bytes=100_000`
- `HttpSandbox.off()` — no restrictions: `block_private_ips=False`, `allowed_hosts=None`, `timeout=60.0`, `max_response_bytes=100_000_000`

#### Scenario: strict preset reduces limits

- **WHEN** `HttpSandbox.strict()` is called
- **THEN** `block_private_ips` is `True`, `timeout` is `5.0`, and `max_response_bytes` is `100_000`

#### Scenario: off preset disables all restrictions

- **WHEN** `HttpSandbox.off()` is used
- **THEN** `block_private_ips` is `False` and `timeout` is `60.0`
