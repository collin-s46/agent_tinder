"""Small, deterministic capability detection for the hackathon demo."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Capability:
    """The capability and ANS query derived from a user request."""

    # name is the stable rule ID, label is readable UI text, and search_query
    # is the verified phrase sent to GoDaddy ANS.
    name: str
    label: str
    search_query: str


class UnsupportedCapabilityError(ValueError):
    """Raised when a prompt is outside the selected Agent A's topics."""


def detect_capability(primary_agent, prompt):
    """Match a prompt to one topic rule owned by the selected Agent A."""
    # casefold() is a stronger lowercase operation, so "HaloHeat" and
    # "HALOHEAT" are treated the same way.
    normalized_prompt = prompt.casefold()

    # Rules are checked in configuration order. Specific topics such as
    # catering come before broad event-planning or wellness terms, making the
    # outcome predictable when a prompt contains more than one relevant word.
    for rule in primary_agent["topic_rules"]:
        for keyword in rule["keywords"]:
            if _contains_keyword(normalized_prompt, keyword):
                return Capability(
                    name=rule["id"],
                    label=rule["label"],
                    search_query=rule["search_query"],
                )

    # Build the error from the selected agent's own topics so the user gets a
    # useful correction instead of a generic unsupported-request message.
    topic_labels = [rule["label"] for rule in primary_agent["topic_rules"]]
    readable_topics = _join_readable(topic_labels)
    raise UnsupportedCapabilityError(
        f"{primary_agent['name']} handles questions about {readable_topics}."
    )


def _contains_keyword(normalized_prompt, keyword):
    """Match complete words or phrases instead of accidental substrings."""
    pattern = rf"(?<![a-z0-9]){re.escape(keyword.casefold())}(?![a-z0-9])"
    return re.search(pattern, normalized_prompt) is not None


def _join_readable(items):
    """Join labels as 'one, two, or three' for a friendly error message."""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])}, or {items[-1]}"
