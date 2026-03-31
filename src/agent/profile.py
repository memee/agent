from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Callable

import yaml

from agent.sandbox import FileSandbox, HttpSandbox, SandboxConfig

# Mapping of domain name → (sandbox class, default factory)
_DOMAIN_SANDBOX_CLASSES: dict[str, type] = {
    "http": HttpSandbox,
    "filesystem": FileSandbox,
}

_VALID_PRESETS = {"default", "strict", "off"}


@dataclass
class AgentProfile:
    name: str
    description: str
    model: str
    tools: list[str]
    system_prompt: str
    sandbox_config: dict


def _parse_profile_file(path: Any, content: str) -> AgentProfile:
    """Parse a profile Markdown file with YAML frontmatter."""
    if not content.startswith("---"):
        raise ValueError(f"Profile file {path} must start with '---' YAML frontmatter")

    # Split off the frontmatter block
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Profile file {path} has malformed frontmatter (missing closing '---')")

    frontmatter_text = parts[1]
    body = parts[2]

    try:
        fm = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Profile file {path} has invalid YAML frontmatter: {exc}") from exc

    required_fields = ["name", "description", "model", "tools"]
    for field in required_fields:
        if field not in fm:
            raise ValueError(f"Profile file {path} is missing required frontmatter field: '{field}'")

    return AgentProfile(
        name=fm["name"],
        description=fm["description"],
        model=fm["model"],
        tools=fm["tools"],
        system_prompt=body.strip(),
        sandbox_config=fm.get("sandbox") or {},
    )


def sandbox_from_profile(config: dict) -> SandboxConfig:
    """Build a SandboxConfig from a profile frontmatter sandbox mapping.

    Each key in config is a domain name ('http', 'filesystem').
    Each domain value may have a 'preset' key (default/strict/off) plus
    field-level overrides applied on top via dataclasses.replace().
    """
    domain_instances: dict[str, Any] = {}

    for domain_name, domain_cls in _DOMAIN_SANDBOX_CLASSES.items():
        if domain_name not in config:
            # Use default preset for absent domains
            domain_instances[domain_name] = domain_cls.default()
            continue

        domain_config = dict(config[domain_name]) if config[domain_name] else {}
        preset_name = domain_config.pop("preset", "default")

        if preset_name not in _VALID_PRESETS:
            raise ValueError(
                f"Unknown sandbox preset '{preset_name}' for domain '{domain_name}'. "
                f"Valid presets: {sorted(_VALID_PRESETS)}"
            )

        # FileSandbox.strict() requires a base_dir argument; handle specially
        if preset_name == "strict" and domain_cls is FileSandbox:
            from pathlib import Path
            base_dir = domain_config.pop("base_dir", None)
            base_dir_path = Path(base_dir) if base_dir else Path("./workspace")
            base = domain_cls.strict(base_dir_path)
            if base_dir is not None:
                # base_dir was already applied via strict(), don't re-apply
                domain_config.pop("base_dir", None)
        else:
            base = getattr(domain_cls, preset_name)()

        # Validate and apply field overrides
        if domain_config:
            valid_fields = {f.name for f in dataclasses.fields(base)}
            for field_name in domain_config:
                if field_name not in valid_fields:
                    raise ValueError(
                        f"Unknown field '{field_name}' for sandbox domain '{domain_name}'. "
                        f"Valid fields: {sorted(valid_fields)}"
                    )
            base = dataclasses.replace(base, **domain_config)

        domain_instances[domain_name] = base

    return SandboxConfig(
        filesystem=domain_instances["filesystem"],
        http=domain_instances["http"],
    )


class AgentProfileRegistry:
    """Registry that loads and exposes AgentProfile objects from subagents/*.md files."""

    def __init__(self) -> None:
        self._discovered_profiles: dict[str, AgentProfile] = {}
        self._registered_profiles: dict[str, AgentProfile] = {}
        self._listeners: list[Callable[[], None]] = []
        self._loaded = False

    def load_all(self) -> None:
        """Load all *.md profiles from the agent.subagents package."""
        pkg = files("agent.subagents")
        discovered_profiles: dict[str, AgentProfile] = {}
        for resource in pkg.iterdir():
            if resource.name.endswith(".md"):
                content = resource.read_text(encoding="utf-8")
                profile = _parse_profile_file(resource.name, content)
                self._check_duplicate_name(profile.name, discovered_profiles, source="autodiscovery")
                self._check_duplicate_name(
                    profile.name,
                    self._registered_profiles,
                    source="autodiscovery",
                )
                discovered_profiles[profile.name] = profile
        self._discovered_profiles = discovered_profiles
        self._loaded = True
        self._notify_changed()

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load_all()

    def _check_duplicate_name(
        self,
        name: str,
        profiles: dict[str, AgentProfile],
        *,
        source: str,
    ) -> None:
        if name in profiles:
            raise ValueError(f"Duplicate profile name '{name}' encountered during {source}")

    def _notify_changed(self) -> None:
        for listener in list(self._listeners):
            listener()

    def add_change_listener(self, listener: Callable[[], None]) -> None:
        """Register a callback invoked whenever the registry contents change."""
        self._listeners.append(listener)

    def register(self, profile: AgentProfile) -> None:
        """Register a profile programmatically."""
        self._ensure_loaded()
        self._check_duplicate_name(profile.name, self._discovered_profiles, source="registration")
        self._check_duplicate_name(profile.name, self._registered_profiles, source="registration")
        self._registered_profiles[profile.name] = profile
        self._notify_changed()

    def _merged_profiles(self) -> dict[str, AgentProfile]:
        self._ensure_loaded()
        return {**self._discovered_profiles, **self._registered_profiles}

    def all(self) -> list[AgentProfile]:
        """Return all loaded profiles sorted alphabetically by name."""
        return sorted(self._merged_profiles().values(), key=lambda p: p.name)

    def get(self, name: str) -> AgentProfile:
        """Return a profile by name. Raises KeyError if not found."""
        profiles = self._merged_profiles()
        if name not in profiles:
            raise KeyError(name)
        return profiles[name]

    def names(self) -> list[str]:
        """Return sorted list of profile names."""
        return sorted(self._merged_profiles().keys())


# Module-level singleton
profile_registry = AgentProfileRegistry()


def format_subagents_section(registry: AgentProfileRegistry) -> str:
    """Return a Markdown section listing available sub-agents from the registry.

    Profiles are listed alphabetically as '- **name**: description'.
    If the registry is empty, a note is included instead of a list.
    """
    profiles = registry.all()
    lines = ["## Available Sub-agents", ""]
    if profiles:
        for p in profiles:
            lines.append(f"- **{p.name}**: {p.description}")
    else:
        lines.append("_No sub-agents available._")
    return "\n".join(lines)


def build_system_prompt(base_prompt: str, registry: AgentProfileRegistry) -> str:
    """Append the sub-agents section to a base system prompt string.

    Returns '<base_prompt>\\n\\n<format_subagents_section(registry)>'.
    """
    section = format_subagents_section(registry)
    if base_prompt:
        return f"{base_prompt}\n\n{section}"
    return section
