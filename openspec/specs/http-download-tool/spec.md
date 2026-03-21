## ADDED Requirements

### Requirement: http_download tool fetches a binary file and saves it to disk

The library SHALL register an `http_download` tool in the `"builtin"` group with `domain="http"`.
It SHALL accept `url: str` and `path: str` (the destination file path).

It SHALL be registered with `validators={"url": http_url_validator, "path": file_path_validator}`
so both the URL and the destination path are validated before any I/O.

It SHALL download the file using httpx in binary mode and write the raw bytes directly to the
resolved path via `path.write_bytes()`. Binary data SHALL NOT be returned to the caller or
placed in the LLM context window.

It SHALL use `sandbox.timeout` as the request timeout.

It SHALL create any missing parent directories before writing.

It SHALL return the resolved absolute path as a string.

It SHALL overwrite an existing file at the destination path without raising an error.

#### Scenario: Binary file is downloaded and saved to disk

- **WHEN** `http_download` is called with a reachable public URL and a writable path
- **THEN** the file is written to disk at the resolved path and the path string is returned

#### Scenario: Missing parent directories are created

- **WHEN** `http_download` is called with a path whose parent directory does not exist
- **THEN** the parent directories are created and the file is saved successfully

#### Scenario: Existing file is overwritten silently

- **WHEN** `http_download` is called with a path that already has a file
- **THEN** the file is overwritten without error

#### Scenario: Private IP is blocked before request

- **WHEN** `http_download` is called with a URL resolving to a private IP and `block_private_ips=True`
- **THEN** raises `PermissionError` from `http_url_validator` before any network connection

#### Scenario: Path outside base_dir is blocked

- **WHEN** `http_download` is called with a path outside the FileSandbox `base_dir`
- **THEN** raises `PermissionError` from `file_path_validator`

#### Scenario: Request times out

- **WHEN** the remote server does not respond within `sandbox.timeout` seconds
- **THEN** raises `TimeoutError`

### Requirement: http_download is auto-registered on import

`http_download` SHALL be registered automatically when `from agent import tools` is executed.

#### Scenario: http_download available after import

- **WHEN** `from agent import tools` is executed
- **THEN** `"http_download"` appears in `tools.names("builtin")`
