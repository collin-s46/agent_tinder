"""Small, deterministic capability detection for the hackathon demo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    """The capability and ANS query derived from a user request."""

    name: str
    search_query: str


class UnsupportedCapabilityError(ValueError):
    """Raised when a prompt is outside the single supported MVP scenario."""


def detect_capability(prompt):
    """Recognize the HaloHeat customer-support scenario."""
    normalized_prompt = prompt.casefold()
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
        return Capability(name="customer-support", search_query="HaloHeat Sauna")

    raise UnsupportedCapabilityError(
        "This MVP currently supports questions about HaloHeat services and pricing."
    )
