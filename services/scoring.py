"""Generic, explainable compatibility scoring for ANS candidates."""

import re


# Agents below this score have only weak technical or text evidence that they
# can help. Hiding them is clearer than presenting unrelated agents as matches.
MINIMUM_COMPATIBILITY_SCORE = 50

# These common words do not tell us whether an agent matches a request. Keeping
# the list local and explicit makes the scoring easy to explain and change.
_STOP_WORDS = {
    "a",
    "about",
    "agent",
    "an",
    "and",
    "are",
    "available",
    "customer",
    "do",
    "does",
    "for",
    "find",
    "first",
    "help",
    "how",
    "i",
    "in",
    "is",
    "me",
    "my",
    "of",
    "offer",
    "options",
    "or",
    "please",
    "questions",
    "service",
    "services",
    "support",
    "tell",
    "the",
    "time",
    "to",
    "we",
    "what",
    "with",
    "you",
}


def score_candidate(prompt, capability, candidate):
    """Score one ANS candidate using five deterministic checks."""
    profile_tokens = _candidate_profile_tokens(candidate)

    # 40 points: the requested topic appears somewhere meaningful in Agent B's
    # name, description, skill names, or tags.
    capability_tokens = _meaningful_tokens(
        " ".join((capability.name, capability.label, capability.search_query))
    )
    capability_points = 40 if capability_tokens & profile_tokens else 0

    # 25 points: words from the user's actual request also appear in Agent B's
    # profile. One shared word earns 15; two or more earn the full 25.
    prompt_overlap = _meaningful_tokens(prompt) & profile_tokens
    if len(prompt_overlap) >= 2:
        prompt_points = 25
    elif len(prompt_overlap) == 1:
        prompt_points = 15
    else:
        prompt_points = 0

    # 20 points: AgenTinder can communicate using its supported protocol and
    # transport. ANS search already filters for these, but scoring the evidence
    # makes the compatibility number explainable.
    supports_a2a_http = (
        candidate.get("protocol") == "A2A"
        and "HTTP" in candidate.get("transports", [])
    )
    protocol_points = 20 if supports_a2a_http else 0

    # 10 points: prefer records ANS currently marks as active.
    status = candidate.get("status", "")
    active_points = (
        10 if isinstance(status, str) and status.casefold() == "active" else 0
    )

    # 5 points: reward registry evidence without using its value as a hidden or
    # complicated ranking formula. Some records have a trust score; others have
    # stable ANS identity metadata.
    scores = candidate.get("scores", {})
    has_registry_metadata = scores.get("trust") is not None or bool(
        candidate.get("agent_id") and candidate.get("ans_name")
    )
    registry_points = 5 if has_registry_metadata else 0

    return {
        "score": (
            capability_points
            + prompt_points
            + protocol_points
            + active_points
            + registry_points
        ),
        "breakdown": {
            "capability_relevance": capability_points,
            "prompt_alignment": prompt_points,
            "protocol_compatibility": protocol_points,
            "active_status": active_points,
            "registry_metadata": registry_points,
        },
    }


def _candidate_profile_tokens(candidate):
    """Collect searchable words from the candidate's public ANS profile."""
    text_parts = [
        candidate.get("name", ""),
        candidate.get("description", ""),
    ]

    for skill in candidate.get("skills", []):
        text_parts.extend(
            [
                skill.get("id", ""),
                skill.get("name", ""),
                *skill.get("tags", []),
            ]
        )

    return _meaningful_tokens(" ".join(text_parts))


def _meaningful_tokens(text):
    """Return lowercase words after removing punctuation and filler words."""
    tokens = re.findall(r"[a-z0-9]+", text.casefold())
    return {token for token in tokens if len(token) > 1 and token not in _STOP_WORDS}
