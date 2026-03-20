## MODIFIED Requirements

### Requirement: read_file tool reads a file from disk

The library SHALL register a `read_file` tool in the `"builtin"` group with `domain="filesystem"`. It SHALL accept a single `path: str` argument and return the file's text content as a string.

It SHALL be registered with `validators={"path": file_path_validator}` so the path is validated and resolved before the file is opened.

It SHALL raise `ValueError` if the resolved file exceeds `sandbox.max_file_bytes`, where `sandbox` is the `FileSandbox` instance routed by the registry.

#### Scenario: File within sandbox is read

- **WHEN** `read_file` is called with a path that resolves to a readable file within the sandbox
- **THEN** returns the full text content of the file

#### Scenario: File exceeding size limit is rejected

- **WHEN** `read_file` is called with a path to a file larger than `sandbox.max_file_bytes`
- **THEN** raises `ValueError` with a message indicating the size limit

#### Scenario: Blocked path is rejected before file is opened

- **WHEN** `read_file` is called with `".env"` and `".env"` matches `sandbox.blocked_paths`
- **THEN** raises `PermissionError` (from `file_path_validator`) before the file is opened

### Requirement: read_file is auto-registered on import

`read_file` SHALL be registered automatically when `from agent import tools` is executed.

#### Scenario: read_file available after import

- **WHEN** `from agent import tools` is executed
- **THEN** `"read_file"` appears in `tools.names("builtin")`
