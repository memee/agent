from __future__ import annotations

import contextvars
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    pass

logger = logging.getLogger("agent")

# ─── Data ────────────────────────────────────────────────────────────────────


@dataclass
class HITLRequest:
    """Carries the parameters of a single human-in-the-loop prompt."""

    type: Literal["confirm", "text", "select"]
    question: str
    choices: list[str] | None = None


# ─── Protocol ────────────────────────────────────────────────────────────────


class HITLHandler(Protocol):
    """Any object with this method is a valid HITL backend."""

    def ask(self, request: HITLRequest) -> str: ...


# ─── Context variable ─────────────────────────────────────────────────────────

_hitl_handler_var: contextvars.ContextVar[HITLHandler | None] = contextvars.ContextVar(
    "_hitl_handler_var", default=None
)


def get_hitl_handler() -> HITLHandler:
    """Return the active HITL handler, falling back to TerminalHITLHandler."""
    handler = _hitl_handler_var.get()
    if handler is None:
        return TerminalHITLHandler()
    return handler


# ─── Default terminal handler ─────────────────────────────────────────────────


class TerminalHITLHandler:
    """Default HITL handler that renders prompts in the terminal using questionary."""

    def ask(self, request: HITLRequest) -> str:
        import questionary

        logger.info(
            "hitl_request",
            extra={"type": request.type, "question": request.question},
        )

        if request.type == "confirm":
            result = questionary.confirm(request.question).ask()
            answer = "yes" if result else "no"
        elif request.type == "text":
            answer = questionary.text(request.question).ask()
        elif request.type == "select":
            answer = questionary.select(request.question, choices=request.choices).ask()
        else:
            raise ValueError(f"Unknown HITL request type: {request.type!r}")

        logger.info(
            "hitl_response",
            extra={"type": request.type, "question": request.question},
        )
        return answer
