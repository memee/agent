## ADDED Requirements

### Requirement: FileSandbox holds file-access constraints

`FileSandbox` SHALL be a dataclass in `agent/sandbox.py` with the following fields:

- `base_dir: Path | None` — if set, all file paths must resolve within this directory; `None` means no directory restriction
- `blocked_paths: list[str]` — glob patterns matched against the resolved path; matching paths are rejected
- `max_file_bytes: int` — maximum number of bytes a file operation may read or write

Default values: `base_dir=None`, `blocked_paths=[".env", ".git"]`, `max_file_bytes=1_000_000`.

#### Scenario: Default construction

- **WHEN** `FileSandbox()` is instantiated with no arguments
- **THEN** `base_dir` is `None`, `blocked_paths` includes `".env"` and `".git"`, `max_file_bytes` is `1_000_000`

### Requirement: FileSandbox provides three class-method presets

`FileSandbox` SHALL expose three class methods:

- `FileSandbox.default()` — same as default construction
- `FileSandbox.strict(base_dir: Path)` — mandatory `base_dir`, additional blocked patterns (`*.key`, `*.pem`), `max_file_bytes=100_000`
- `FileSandbox.off()` — no restrictions: `base_dir=None`, empty `blocked_paths`, `max_file_bytes=100_000_000`

#### Scenario: strict preset sets base_dir

- **WHEN** `FileSandbox.strict(Path("/workspace"))` is called
- **THEN** `base_dir` equals `Path("/workspace")` and `max_file_bytes` is `100_000`

#### Scenario: off preset disables all restrictions

- **WHEN** `FileSandbox.off()` is used
- **THEN** `base_dir` is `None` and `blocked_paths` is empty
