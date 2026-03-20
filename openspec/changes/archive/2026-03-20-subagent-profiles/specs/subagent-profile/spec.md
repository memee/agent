## ADDED Requirements

### Requirement: Sub-agent profile file format

A sub-agent profile SHALL be a Markdown file with YAML frontmatter delimited by `---` and a Markdown body.

The frontmatter SHALL support the following fields:

- `name` (string, required): unique identifier used as the profile key and enum value in the `delegate` tool
- `description` (string, required): one-line description shown to the orchestrator LLM for profile selection
- `model` (string, required): model identifier passed to the LLM client
- `tools` (list of strings, required): names of tools the sub-agent may call
- `sandbox` (object, optional): per-domain sandbox config; if absent, all domains use their `default` preset

The Markdown body (everything after the closing `---`) SHALL be used verbatim as the sub-agent's system prompt.

#### Scenario: Valid profile file is parsed correctly

- **WHEN** a profile file with all required frontmatter fields and a non-empty body is loaded
- **THEN** `name`, `description`, `model`, `tools`, and `sandbox` are accessible on the resulting `AgentProfile`, and `system_prompt` equals the Markdown body stripped of leading/trailing whitespace

#### Scenario: Missing required field raises an error

- **WHEN** a profile file omits a required frontmatter field (e.g. `model`)
- **THEN** loading the file raises a `ValueError` identifying the missing field and the file path

### Requirement: Sandbox section supports preset and field overrides

The `sandbox` frontmatter field SHALL accept a mapping where each key is a domain name (`http`, `filesystem`).

Each domain value SHALL accept:

- `preset` (string, optional): one of `default`, `strict`, `off` — selects the base configuration; defaults to `default` if absent
- Additional keys matching field names of the domain's sandbox dataclass — applied as overrides on top of the preset

#### Scenario: Preset-only domain config

- **WHEN** a profile specifies `sandbox.http.preset: strict` with no additional keys
- **THEN** the resulting `HttpSandbox` equals `HttpSandbox.strict()`

#### Scenario: Preset with field override

- **WHEN** a profile specifies `sandbox.http.preset: strict` and `sandbox.http.allowed_hosts: ["api.example.com"]`
- **THEN** the resulting `HttpSandbox` starts from `HttpSandbox.strict()` and has `allowed_hosts == ["api.example.com"]`

#### Scenario: Domain with no preset key defaults to default preset

- **WHEN** a profile specifies `sandbox.filesystem: {}` or omits `preset` under a domain
- **THEN** the resulting `FileSandbox` equals `FileSandbox.default()`

#### Scenario: Entire sandbox section absent

- **WHEN** a profile file has no `sandbox` key in frontmatter
- **THEN** the resulting `SandboxConfig` equals `SandboxConfig.default()`
