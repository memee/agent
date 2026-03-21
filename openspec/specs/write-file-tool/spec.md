## ADDED Requirements

### Requirement: write_file tool writes UTF-8 text content to a file

The library SHALL register a `write_file` tool in the `"builtin"` group with `domain="filesystem"`.
It SHALL accept `path: str` and `content: str`.

It SHALL be registered with `validators={"path": file_path_validator}` so the destination path
is validated against the FileSandbox before any write.

It SHALL write `content` encoded as UTF-8 to the resolved path, creating or overwriting the file.

It SHALL create any missing parent directories before writing.

It SHALL raise `ValueError` if `len(content.encode("utf-8"))` exceeds `sandbox.max_file_bytes`.

It SHALL return the resolved absolute path as a string.

#### Scenario: Text content is written to a new file

- **WHEN** `write_file` is called with a valid path and a text string
- **THEN** the file is created at the resolved path containing the UTF-8-encoded content, and the path string is returned

#### Scenario: Existing file is overwritten silently

- **WHEN** `write_file` is called with a path that already has a file
- **THEN** the file is overwritten with the new content without error

#### Scenario: Missing parent directories are created

- **WHEN** `write_file` is called with a path whose parent directory does not exist
- **THEN** the parent directories are created and the file is written successfully

#### Scenario: Content exceeding size limit is rejected

- **WHEN** `write_file` is called with content whose UTF-8 byte length exceeds `sandbox.max_file_bytes`
- **THEN** raises `ValueError` with a message indicating the size limit, before any write

#### Scenario: Path outside base_dir is blocked

- **WHEN** `write_file` is called with a path outside the FileSandbox `base_dir`
- **THEN** raises `PermissionError` from `file_path_validator`

#### Scenario: Blocked path pattern is rejected

- **WHEN** `write_file` is called with a path matching a `blocked_paths` pattern (e.g., `.env`)
- **THEN** raises `PermissionError` from `file_path_validator`

### Requirement: write_file is auto-registered on import

`write_file` SHALL be registered automatically when `from agent import tools` is executed.

#### Scenario: write_file available after import

- **WHEN** `from agent import tools` is executed
- **THEN** `"write_file"` appears in `tools.names("builtin")`
