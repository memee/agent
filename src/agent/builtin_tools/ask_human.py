from agent.hitl import HITLRequest, get_hitl_handler
from agent.tool import tool


@tool("ask_human", group="builtin")
def ask_human(
    question: str,
    type: str = "text",
    choices: str = "",
) -> str:
    """Pause the agent and ask the human for input.

    Use this when a decision or piece of information is required from the user
    before the agent can continue.

    type: One of "confirm" (yes/no), "text" (free input), or "select" (pick from list).
    choices: Comma-separated list of options, required when type is "select".
    Returns the human's answer as a string ("yes"/"no" for confirm).
    """
    if type == "select":
        if not choices:
            raise ValueError("choices must be provided when type='select'")
        choice_list = [c.strip() for c in choices.split(",") if c.strip()]
    else:
        choice_list = None

    request = HITLRequest(type=type, question=question, choices=choice_list)  # type: ignore[arg-type]
    return get_hitl_handler().ask(request)
