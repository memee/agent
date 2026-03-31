## 1. AgentProfileRegistry

- [x] 1.1 Extend `src/agent/profile.py` so `AgentProfileRegistry` stores autodiscovered and programmatically registered profiles as separate sources and returns a merged view through `all()`, `names()`, and `get()`.
- [x] 1.2 Add a public API for registering a single `AgentProfile` without requiring prior `load_all()` and preserve alphabetical, deterministic ordering of results.
- [x] 1.3 Add duplicate-name validation across both profile sources so conflicts raise `ValueError` instead of silently overwriting entries.

## 2. Delegate Schema Refresh

- [x] 2.1 Change `src/agent/builtin_tools/delegate.py` so the `delegate` tool schema reflects the current state of `AgentProfileRegistry`, including programmatic profile registration after module import.
- [x] 2.2 Keep `delegate(profile, task, image_url=None)` execution unchanged and ensure newly registered profiles resolve correctly at call time.

## 3. Verification

- [x] 3.1 Add tests in `tests/test_profile.py` for registration before first read, after `load_all()`, alphabetical ordering of results, and duplicate-name conflicts.
- [x] 3.2 Add tests in `tests/test_builtin_tools.py` confirming that the `profile` enum in the `delegate` schema refreshes after programmatic registration of a new profile.
- [x] 3.3 Run the relevant profile and `delegate` test suite to confirm there are no regressions in autodiscovery or delegation.
