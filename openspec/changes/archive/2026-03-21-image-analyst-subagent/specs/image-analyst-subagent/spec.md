## ADDED Requirements

### Requirement: image_analyst sub-agent profile exists and is loadable

The repository SHALL contain a sub-agent profile file at `src/agent/subagents/image_analyst.md`.

The profile frontmatter SHALL specify:

- `name: image_analyst`
- `model: openai/gpt-4o-mini`
- `tools: [http_download, analyze_image]`
- `sandbox.http.preset: strict`
- `sandbox.filesystem.preset: default` with `base_dir: "./workspace"`

#### Scenario: Profile is loaded by AgentProfileRegistry

- **WHEN** `AgentProfileRegistry` scans `src/agent/subagents/`
- **THEN** a profile named `"image_analyst"` is available via `profile_registry.get("image_analyst")`

#### Scenario: Profile exposes correct tools

- **WHEN** the `image_analyst` profile is loaded
- **THEN** `profile.tools` equals `["http_download", "analyze_image"]`

### Requirement: image_analyst handles a remote image URL end-to-end

The `image_analyst` sub-agent SHALL be capable of receiving a task containing a remote image URL, downloading the image, analyzing it, and returning the analysis along with the local file path — without any orchestrator assistance.

#### Scenario: Remote URL is downloaded and analyzed

- **WHEN** the `image_analyst` sub-agent receives a task containing a remote image URL and an analysis question
- **THEN** it calls `http_download` to save the image to `./workspace/`, then calls `analyze_image` with the saved path, and returns a response containing the textual analysis and the local file path

### Requirement: image_analyst handles a local file path

When delegated a task that includes a local file path (already on disk), the `image_analyst` sub-agent SHALL call `analyze_image` directly without invoking `http_download`.

#### Scenario: Local path is analyzed without download

- **WHEN** the `image_analyst` sub-agent receives a task containing a local file path within the sandbox
- **THEN** it calls `analyze_image` with that path and returns the analysis result
