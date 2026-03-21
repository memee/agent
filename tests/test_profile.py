"""Tests for AgentProfile, sandbox_from_profile, and AgentProfileRegistry."""
from __future__ import annotations

import pytest

from agent.profile import (
    AgentProfile,
    AgentProfileRegistry,
    _parse_profile_file,
    build_system_prompt,
    format_subagents_section,
    sandbox_from_profile,
)
from agent.sandbox import FileSandbox, HttpSandbox, SandboxConfig


# ---------------------------------------------------------------------------
# Task 5.1: sandbox_from_profile
# ---------------------------------------------------------------------------

def test_sandbox_from_profile_empty_returns_default():
    """Empty config produces SandboxConfig.default()."""
    result = sandbox_from_profile({})
    assert result == SandboxConfig.default()


def test_sandbox_from_profile_preset_only_strict_http():
    """HTTP strict preset without overrides equals HttpSandbox.strict()."""
    result = sandbox_from_profile({"http": {"preset": "strict"}})
    assert result.http == HttpSandbox.strict()
    assert result.filesystem == FileSandbox.default()


def test_sandbox_from_profile_preset_with_override():
    """HTTP strict preset with allowed_hosts override applies the override."""
    result = sandbox_from_profile({
        "http": {"preset": "strict", "allowed_hosts": ["example.com"]}
    })
    base = HttpSandbox.strict()
    assert result.http.allowed_hosts == ["example.com"]
    # Other fields remain from strict preset
    assert result.http.block_private_ips == base.block_private_ips
    assert result.http.timeout == base.timeout


def test_sandbox_from_profile_filesystem_off():
    """Filesystem off preset equals FileSandbox.off()."""
    result = sandbox_from_profile({"filesystem": {"preset": "off"}})
    assert result.filesystem == FileSandbox.off()
    assert result.http == HttpSandbox.default()


def test_sandbox_from_profile_unknown_preset_raises():
    """Unknown preset name raises ValueError."""
    with pytest.raises(ValueError, match="banana"):
        sandbox_from_profile({"http": {"preset": "banana"}})


def test_sandbox_from_profile_unknown_field_raises():
    """Unknown override field raises ValueError."""
    with pytest.raises(ValueError, match="nonexistent_field"):
        sandbox_from_profile({"http": {"nonexistent_field": True}})


def test_sandbox_from_profile_domain_no_preset_defaults_to_default():
    """Domain config without preset key uses default preset."""
    result = sandbox_from_profile({"filesystem": {}})
    assert result.filesystem == FileSandbox.default()


# ---------------------------------------------------------------------------
# Task 5.2: AgentProfileRegistry
# ---------------------------------------------------------------------------

def test_registry_loads_builtin_researcher():
    """Registry contains the researcher built-in profile after loading."""
    registry = AgentProfileRegistry()
    registry.load_all()
    assert "researcher" in registry.names()


def test_registry_get_returns_profile():
    """get() returns an AgentProfile with the correct name."""
    registry = AgentProfileRegistry()
    registry.load_all()
    profile = registry.get("researcher")
    assert isinstance(profile, AgentProfile)
    assert profile.name == "researcher"


def test_registry_get_unknown_raises_key_error():
    """get() raises KeyError for an unknown profile name."""
    registry = AgentProfileRegistry()
    registry.load_all()
    with pytest.raises(KeyError):
        registry.get("nonexistent_profile_xyz")


def test_registry_names_sorted():
    """names() returns a sorted list."""
    registry = AgentProfileRegistry()
    registry.load_all()
    names = registry.names()
    assert names == sorted(names)


def test_registry_all_sorted_by_name():
    """all() returns profiles sorted alphabetically by name."""
    registry = AgentProfileRegistry()
    registry.load_all()
    profiles = registry.all()
    assert [p.name for p in profiles] == sorted(p.name for p in profiles)


# ---------------------------------------------------------------------------
# Task 5.3: researcher.md profile
# ---------------------------------------------------------------------------

def test_researcher_profile_has_correct_tools():
    """researcher.md lists exactly ['http_get', 'read_file'] as tools."""
    registry = AgentProfileRegistry()
    registry.load_all()
    profile = registry.get("researcher")
    assert profile.tools == ["http_get", "read_file"]


def test_researcher_profile_sandbox_not_fully_off():
    """researcher sandbox does not use FileSandbox.off() — filesystem is sandboxed."""
    registry = AgentProfileRegistry()
    registry.load_all()
    profile = registry.get("researcher")
    sandbox = sandbox_from_profile(profile.sandbox_config)
    assert sandbox.filesystem != FileSandbox.off()


def test_researcher_profile_has_system_prompt():
    """researcher profile has a non-empty system prompt."""
    registry = AgentProfileRegistry()
    registry.load_all()
    profile = registry.get("researcher")
    assert len(profile.system_prompt) > 0


def test_researcher_profile_has_model():
    """researcher profile specifies a model."""
    registry = AgentProfileRegistry()
    registry.load_all()
    profile = registry.get("researcher")
    assert profile.model  # non-empty string


# ---------------------------------------------------------------------------
# format_subagents_section
# ---------------------------------------------------------------------------

def _make_registry(*profiles: AgentProfile) -> AgentProfileRegistry:
    """Build a registry pre-loaded with the given profiles (no disk I/O)."""
    registry = AgentProfileRegistry()
    registry._profiles = {p.name: p for p in profiles}
    registry._loaded = True
    return registry


def _make_profile(name: str, description: str = "desc") -> AgentProfile:
    return AgentProfile(
        name=name,
        description=description,
        model="gpt-4o-mini",
        tools=[],
        system_prompt="",
        sandbox_config={},
    )


def test_format_subagents_section_heading():
    """Section always starts with '## Available Sub-agents'."""
    registry = _make_registry(_make_profile("alpha"))
    result = format_subagents_section(registry)
    assert result.startswith("## Available Sub-agents")


def test_format_subagents_section_contains_name_and_description():
    """Each profile appears as '- **name**: description'."""
    registry = _make_registry(_make_profile("alpha", "does alpha things"))
    result = format_subagents_section(registry)
    assert "- **alpha**: does alpha things" in result


def test_format_subagents_section_alphabetical_order():
    """Profiles are listed in alphabetical order by name."""
    registry = _make_registry(_make_profile("zap"), _make_profile("alpha"))
    result = format_subagents_section(registry)
    assert result.index("alpha") < result.index("zap")


def test_format_subagents_section_empty_registry():
    """Empty registry produces heading and an empty-note line."""
    registry = _make_registry()
    result = format_subagents_section(registry)
    assert "## Available Sub-agents" in result
    assert "No sub-agents available" in result
    assert "- **" not in result


# ---------------------------------------------------------------------------
# build_system_prompt
# ---------------------------------------------------------------------------

def test_build_system_prompt_appends_section():
    """build_system_prompt appends the sub-agents section after the base prompt."""
    registry = _make_registry(_make_profile("researcher", "searches the web"))
    result = build_system_prompt("You are a helpful assistant.", registry)
    assert result.startswith("You are a helpful assistant.")
    assert "## Available Sub-agents" in result
    assert "- **researcher**: searches the web" in result


def test_build_system_prompt_empty_base():
    """Empty base prompt returns only the sub-agents section."""
    registry = _make_registry(_make_profile("researcher"))
    result = build_system_prompt("", registry)
    assert "## Available Sub-agents" in result
    assert not result.startswith("\n\n")
