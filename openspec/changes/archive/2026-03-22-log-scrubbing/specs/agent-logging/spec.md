## MODIFIED Requirements

### Requirement: Dual-handler logging configuration

The system SHALL configure the `agent` logger with two handlers on initialization:

- A `StreamHandler` writing to stdout with a human-readable format
- A `FileHandler` writing to a JSON file (one JSON object per line)

Both handlers SHALL have a `ScrubFilter` attached that masks secrets before
any formatter serializes the log record.

The log file path SHALL default to `agent.log` in the current working directory and be overridable via the `AGENT_LOG_FILE` environment variable.

#### Scenario: Stdout handler emits human-readable output

- **WHEN** a log record is emitted at INFO level
- **THEN** stdout receives a line in the format: `[HH:MM:SS] LEVEL agent_name(depth) | message key=value ...`

#### Scenario: File handler emits structured JSON

- **WHEN** a log record is emitted at INFO level
- **THEN** the log file receives a single JSON line containing: `timestamp`, `level`, `event`, and all `extra` fields (run_id, agent_name, depth, iteration, etc.)

#### Scenario: Log file path overridden via environment variable

- **WHEN** `AGENT_LOG_FILE=/tmp/run.log` is set in the environment
- **THEN** the file handler writes to `/tmp/run.log`

#### Scenario: Secrets scrubbed before emission on stdout

- **WHEN** a log record containing a secret (e.g. `sk-proj-XXXX...`) is emitted
- **THEN** stdout output contains `sk-***` instead of the original value

#### Scenario: Secrets scrubbed before emission in log file

- **WHEN** a log record containing a secret is emitted
- **THEN** the JSON log file contains `***` instead of the original secret value
