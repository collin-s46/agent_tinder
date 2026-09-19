"""Small, deterministic capability detection for the hackathon demo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    """The capability and ANS query derived from a user request."""

    # name is shown to the frontend; search_query is sent to GoDaddy ANS.
    name: str
    search_query: str


class UnsupportedCapabilityError(ValueError):
    """Raised when a prompt is outside the single supported MVP scenario."""


def detect_capability(prompt):
    """Recognize the HaloHeat customer-support scenario."""
    # casefold() is a stronger lowercase operation, so "HaloHeat" and
    # "HALOHEAT" are treated the same way.
    normalized_prompt = prompt.casefold()

    # The prompt must mention the demo business and also ask for something the
    # customer-support agent can answer. Keeping these lists short makes the
    # behavior easy to explain during the hackathon demo.
    target_terms = ("haloheat", "sauna")
    support_terms = (
        "service",
        "offer",
        "price",
        "pricing",
        "cost",
        "session",
        "membership",
        "support",
        "order",
    )

    mentions_target = any(term in normalized_prompt for term in target_terms)
    requests_support = any(term in normalized_prompt for term in support_terms)

    if mentions_target and requests_support:
        # We send a short, focused query instead of the full sentence because
        # the manual ANS test showed this reliably finds the HaloHeat agent.
        return Capability(name="customer-support", search_query="HaloHeat Sauna")

    # The MVP supports one polished scenario. An explicit error is clearer than
    # pretending an unsupported request can be handled.
    raise UnsupportedCapabilityError(
        "This MVP currently supports questions about HaloHeat services and pricing."
    )
