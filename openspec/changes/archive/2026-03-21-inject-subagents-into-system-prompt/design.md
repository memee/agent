## Context

The `agent.profile` module already owns the `AgentProfileRegistry` and `AgentProfile` types. When building the main agent's `Conversation`, callers set a system prompt as a plain string — there is no automatic mechanism to enrich it with runtime context like available sub-agents.

The `delegate` tool schema currently embeds sub-agent descriptions in both the tool-level description and the `profile` parameter description. The gap is that the main agent's system prompt (the persistent planning context) does not include this information. Once sub-agent info moves to the system prompt, the redundant prose in the tool schema becomes noise and should be removed — the `profile` enum (for validation) is sufficient.

## Goals / Non-Goals

**Goals:**

- Add a pure utility function `format_subagents_section(registry)` → `str` that renders available sub-agent names and descriptions as a Markdown block
- Add a convenience function `build_system_prompt(base_prompt, registry)` that appends the formatted section to any base system prompt string
- Keep both functions in `agent/profile.py` alongside the registry they depend on
- Simplify `_build_delegate_schema()` in `delegate.py`: keep the `profile` enum but remove sub-agent prose descriptions from the tool and parameter descriptions

**Non-Goals:**

- Automatic injection (no monkey-patching of `run()` or `Conversation`)
- Modifying the `run()` function signature
- Changing existing behavior for any callers that do not opt in

## Decisions

### Decision: Pure functions in `agent/profile.py`, not a `Conversation` method

**Chosen:** Two free functions `format_subagents_section` and `build_system_prompt` added to `agent/profile.py`.

**Alternatives considered:**

- *Method on `AgentProfileRegistry`*: would require callers to import the registry just to build a string — the registry is already a singleton, but a method would conflate registry responsibilities with prompt construction.
- *Helper in `agent/conversation.py`*: `Conversation` currently has no dependency on profiles; adding one would create a circular coupling risk.
- *Parameter on `run()`*: would change the public API of `run()` and force every caller to be aware of profiles, even sub-agents that don't support delegation.

**Rationale:** Pure functions are easy to test in isolation, don't require changes to existing call sites, and naturally live next to the registry they read from.

### Decision: Opt-in, not automatic

**Chosen:** Callers explicitly call `build_system_prompt(base, registry)` when constructing the main agent's `Conversation`.

**Rationale:** Sub-agents (launched by `delegate`) should not see a "here are your sub-agents" section in their system prompts — they get a fixed system prompt from their profile file. Automatic injection would require distinguishing main-agent vs sub-agent execution, adding complexity with no benefit.

## Risks / Trade-offs

- [Stale output if profiles change at runtime] → `format_subagents_section` reads from the registry at call time; since profiles are loaded once at import, this is effectively stable for the lifetime of a process.
- [Section placement] → `build_system_prompt` appends to the base; if the caller's base prompt ends with specific formatting, the appended section may look jarring → callers can use `format_subagents_section` directly for custom placement.
