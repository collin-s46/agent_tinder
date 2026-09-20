"""Deterministic quality checks for responses returned by external agents."""

import re


_LIMITATION_PATTERNS = (
    r"\b(?:i am|i'm|we are|we're)(?: currently| temporarily)? unable to\b",
    r"\b(?:i|we) (?:cannot|can't) (?:access|find|provide|retrieve)\b",
    r"\b(?:i|we) (?:do not|don't) have access\b",
    r"\bnot available at (?:this|the) (?:moment|time)\b",
)

_HANDOFF_PATTERNS = (
    r"\bcontact (?:us|them|the business)\b",
    r"\bcontact [^.]{0,80}\bdirectly\b",
    r"\breach out (?:to|directly)\b",
    r"\bcall (?:us|them|the business)\b",
    r"\bvisit (?:our|their|the) (?:website|site)\b",
)

_LIMITED_MESSAGE = (
    "This agent returned a fallback instead of the requested details. "
    "Try the next discovered agent or revise the request."
)


def assess_answer_quality(answer):
    """Label obvious refusal/contact fallbacks without judging factual truth."""
    if not isinstance(answer, str) or not answer.strip():
        return {"status": "limited", "message": _LIMITED_MESSAGE}

    normalized = " ".join(answer.casefold().split())
    has_limitation = _matches_any(_LIMITATION_PATTERNS, normalized)
    redirects_elsewhere = _matches_any(_HANDOFF_PATTERNS, normalized)

    # A limitation plus an external handoff is the common low-information
    # response from public business agents. Very short refusals are also marked
    # limited even when they omit explicit contact instructions.
    if (has_limitation and redirects_elsewhere) or (
        has_limitation and len(normalized) < 180
    ):
        return {"status": "limited", "message": _LIMITED_MESSAGE}

    return {"status": "useful", "message": ""}


def _matches_any(patterns, text):
    return any(re.search(pattern, text) for pattern in patterns)
