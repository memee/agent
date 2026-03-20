from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

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
        self._profiles: dict[str, AgentProfile] = {}
        self._loaded = False

    def load_all(self) -> None:
        """Load all *.md profiles from the agent.subagents package."""
        pkg = files("agent.subagents")
        self._profiles = {}
        for resource in pkg.iterdir():
            if resource.name.endswith(".md"):
                content = resource.read_text(encoding="utf-8")
                profile = _parse_profile_file(resource.name, content)
                self._profiles[profile.name] = profile
        self._loaded = True

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load_all()

    def all(self) -> list[AgentProfile]:
        """Return all loaded profiles sorted alphabetically by name."""
        self._ensure_loaded()
        return sorted(self._profiles.values(), key=lambda p: p.name)

    def get(self, name: str) -> AgentProfile:
        """Return a profile by name. Raises KeyError if not found."""
        self._ensure_loaded()
        if name not in self._profiles:
            raise KeyError(name)
        return self._profiles[name]

    def names(self) -> list[str]:
        """Return sorted list of profile names."""
        self._ensure_loaded()
        return sorted(self._profiles.keys())


# Module-level singleton
profile_registry = AgentProfileRegistry()
