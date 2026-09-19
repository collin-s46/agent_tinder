"""Explainable compatibility scoring for the single MVP scenario."""


def score_candidate(prompt, capability_name, candidate):
    """Score an ANS candidate using three simple, visible checks."""
    prompt_text = prompt.casefold()
    profile_text = " ".join(
        (
            candidate.get("name", ""),
            candidate.get("description", ""),
            candidate.get("ans_name", ""),
        )
    ).casefold()

    # The user asked specifically about HaloHeat, so matching that business is
    # the most important part of compatibility for this demo.
    requested_target = "haloheat" if "haloheat" in prompt_text else ""
    target_points = 60 if requested_target and requested_target in profile_text else 0

    # Combine every skill field into searchable text. This keeps the score
    # compatible with the function names and tags returned by ANS.
    skill_text_parts = []
    for skill in candidate.get("skills", []):
        skill_text_parts.extend(
            [skill.get("id", ""), skill.get("name", ""), *skill.get("tags", [])]
        )
    skill_text = " ".join(skill_text_parts).casefold()
    capability_points = 20 if capability_name in skill_text else 0

    # The remaining points confirm that AgenTinder can actually communicate
    # with the candidate using the protocol required by the MVP.
    supports_a2a_http = (
        candidate.get("protocol") == "A2A"
        and "HTTP" in candidate.get("transports", [])
    )
    protocol_points = 20 if supports_a2a_http else 0

    return {
        "score": target_points + capability_points + protocol_points,
        "breakdown": {
            "target_match": target_points,
            "capability_match": capability_points,
            "protocol_match": protocol_points,
        },
    }
