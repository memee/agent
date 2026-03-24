"""Runtime secret store with ${NAME} interpolation support."""
from __future__ import annotations

import re

_PLACEHOLDER = re.compile(r"\$\{([A-Za-z0-9_]+)}")


class SecretsStore:
    """Holds named secret values and resolves ${NAME} placeholders in strings.

    Secrets are supplied at call time (e.g. from env vars at the task entry
    point) and never stored in conversation context or profiles.
    """

    def __init__(self, secrets: dict[str, str]) -> None:
        self._secrets = dict(secrets)

    def get(self, name: str) -> str | None:
        """Return the secret value for *name*, or None if unknown."""
        return self._secrets.get(name)

    def values(self) -> list[str]:
        """Return all secret values (for scrubber registration)."""
        return list(self._secrets.values())

    def names(self) -> list[str]:
        """Return all secret names (for system prompt injection)."""
        return list(self._secrets.keys())

    def format_system_prompt_section(self) -> str:
        """Return a Markdown section describing available secrets for a system prompt.

        Lists available secret names and explains the ${NAME} reference convention.
        Include this in the agent's system prompt so it knows how to use secrets
        without ever seeing their values.
        """
        lines = ["## Secret References", ""]
        if self._secrets:
            lines.append(
                "The following named secrets are available. Reference them using "
                "`${NAME}` syntax in any tool argument (URL, body, headers)."
            )
            lines.append(
                "The framework resolves placeholders before the request is made — "
                "never use literal values.")
            lines.append("")
            for name in sorted(self._secrets):
                lines.append(f"- `${{{name}}}`")
            lines.append("")
        lines.append(
            "If instructions contain placeholders in other formats "
            "(`<NAME>`, `{NAME}`, `[[NAME]]` etc.) convert them to `${NAME}` "
            "when constructing tool arguments."
        )
        return "\n".join(lines)

    def interpolate(self, text: str) -> str:
        """Replace ${NAME} placeholders with secret values.

        Unknown placeholders are left unchanged.
        """

        def _replace(match: re.Match) -> str:
            name = match.group(1)
            return self._secrets.get(name, match.group(0))

        return _PLACEHOLDER.sub(_replace, text)
