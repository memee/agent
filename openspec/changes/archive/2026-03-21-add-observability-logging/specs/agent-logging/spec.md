## ADDED Requirements

### Requirement: Dual-handler logging configuration

The system SHALL configure the `agent` logger with two handlers on initialization:

- A `StreamHandler` writing to stdout with a human-readable format
- A `FileHandler` writing to a JSON file (one JSON object per line)

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

### Requirement: Context fields injected into every log record

The system SHALL inject the current execution context fields (run_id, parent_run_id, depth, agent_name, iteration) into every log record emitted by the `agent` logger, regardless of where in the codebase the log is produced.

#### Scenario: Log record contains context fields

- **WHEN** any `logger.info(...)` call is made within a `run()` execution
- **THEN** the resulting log record contains run_id, depth, agent_name, and iteration from the current context

#### Scenario: Missing context does not crash

- **WHEN** a log is emitted outside of a `run()` context (e.g., at import time)
- **THEN** context fields default to safe values (run_id=None, depth=0, agent_name="unknown", iteration=0)
