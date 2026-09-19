from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from services.ans_client import (
    ANSAgentNotFoundError,
    ANSClientError,
    ANSConfigurationError,
    get_agent,
    search_agents,
)
from services.a2a_client import A2AClientError, send_message
from services.capability import UnsupportedCapabilityError, detect_capability
from services.primary_agents import get_primary_agent, list_primary_agents
from services.scoring import MINIMUM_COMPATIBILITY_SCORE, score_candidate


# Read values from a local .env file into environment variables. This happens
# before any request is handled so the ANS client can find its credentials.
load_dotenv()

# Flask uses this application object to register routes and run the web server.
app = Flask(__name__)

MAX_PROMPT_LENGTH = 2_000
MAX_AGENT_ID_LENGTH = 256


@app.after_request
def add_security_headers(response):
    """Apply small, dependency-free browser protections to every response."""
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "connect-src 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "img-src 'self' data:; "
        "script-src 'self'; "
        "style-src 'self'"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/")
def index():
    """Render the AgenTinder homepage."""
    # Sage is the temporary default because its HaloHeat example remains
    # compatible with the current single-scenario backend. Agent-specific
    # routing will be added in the next iteration step.
    return render_template(
        "index.html",
        primary_agents=list_primary_agents(),
        default_primary_agent=get_primary_agent("sage"),
    )


@app.post("/api/search")
def search():
    """Detect the requested capability and return matching ANS agents."""
    # JavaScript sends only the local Agent A ID and the user's prompt. The
    # server retrieves every other Agent A field from its trusted configuration.
    # Example: {"primary_agent_id": "sage", "prompt": "Find a sauna."}
    # silent=True lets us return our own friendly error if the body is not JSON.
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error_response(
            "invalid_request",
            "Please send the request as a JSON object.",
            400,
        )
    primary_agent_id = payload.get("primary_agent_id", "")
    prompt = payload.get("prompt", "")

    # Reject empty or non-text prompts before doing any external API work.
    if not isinstance(prompt, str) or not prompt.strip():
        return _error_response("missing_prompt", "Please enter a request.", 400)

    prompt = prompt.strip()
    if len(prompt) > MAX_PROMPT_LENGTH:
        return _error_response(
            "prompt_too_long",
            f"Please keep the request under {MAX_PROMPT_LENGTH:,} characters.",
            400,
        )

    # Never accept an Agent A name, role, or rules from the browser. Resolve its
    # short ID against our local configuration so only Spark and Sage are valid.
    primary_agent = get_primary_agent(primary_agent_id)
    if primary_agent is None:
        return _error_response(
            "invalid_primary_agent",
            "Please select a valid primary agent.",
            400,
        )

    # Let the selected Agent A classify the request using its small local topic
    # rules. This is intentionally deterministic—there is no LLM call or
    # complex orchestration in the MVP.
    try:
        capability = detect_capability(primary_agent, prompt)
    except UnsupportedCapabilityError as error:
        return _error_response("unsupported_capability", str(error), 422)

    # Search GoDaddy ANS only after the prompt has been validated and classified.
    # Configuration failures and external service failures get different status
    # codes so the frontend can explain what went wrong later.
    try:
        candidates = search_agents(capability.search_query)
    except ANSConfigurationError as error:
        return _error_response("ans_configuration", str(error), 503)
    except ANSClientError as error:
        return _error_response("ans_unavailable", str(error), 502)

    # Score every real ANS result, then hide candidates with too little evidence
    # that they match the request. No agents are invented or hard-coded here.
    scored_candidates = []
    for candidate in candidates:
        scored_candidate = candidate.copy()
        scored_candidate["compatibility"] = score_candidate(
            prompt,
            capability,
            candidate,
        )
        if (
            scored_candidate["compatibility"]["score"]
            >= MINIMUM_COMPATIBILITY_SCORE
        ):
            scored_candidates.append(scored_candidate)

    # Highest compatibility appears first in the API. The Tinder-style demo
    # deck may still place one lower match before it so Pass remains visible.
    scored_candidates.sort(
        key=lambda candidate: candidate["compatibility"]["score"],
        reverse=True,
    )

    # jsonify creates a JSON response and sets the correct Content-Type header.
    # Candidate records are already cleaned up by services/ans_client.py.
    return jsonify(
        {
            "prompt": prompt,
            "primary_agent": {
                "id": primary_agent["id"],
                "name": primary_agent["name"],
                "role": primary_agent["role"],
            },
            "capability": capability.name,
            "capability_label": capability.label,
            "search_query": capability.search_query,
            "candidates": scored_candidates,
        }
    )


@app.post("/api/match")
def connect_match():
    """Let a validated Agent A delegate the request to Agent B over A2A."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error_response(
            "invalid_request",
            "Please send the request as a JSON object.",
            400,
        )
    primary_agent_id = payload.get("primary_agent_id", "")
    agent_id = payload.get("agent_id", "")
    prompt = payload.get("prompt", "")

    if not isinstance(agent_id, str) or not agent_id.strip():
        return _error_response("missing_agent", "Please select an agent.", 400)
    if not isinstance(prompt, str) or not prompt.strip():
        return _error_response("missing_prompt", "Please enter a request.", 400)

    prompt = prompt.strip()
    agent_id = agent_id.strip()
    if len(prompt) > MAX_PROMPT_LENGTH:
        return _error_response(
            "prompt_too_long",
            f"Please keep the request under {MAX_PROMPT_LENGTH:,} characters.",
            400,
        )
    if len(agent_id) > MAX_AGENT_ID_LENGTH:
        return _error_response(
            "invalid_agent",
            "The selected agent ID is invalid.",
            400,
        )

    # Validate Agent A again at the moment of delegation. A successful search
    # does not make later browser data trusted, and /api/match can be called on
    # its own without going through the interface first.
    primary_agent = get_primary_agent(primary_agent_id)
    if primary_agent is None:
        return _error_response(
            "invalid_primary_agent",
            "Please select a valid primary agent.",
            400,
        )

    # Re-run the small deterministic classifier so Agent A cannot be asked to
    # delegate a request outside its configured role between Search and Match.
    try:
        capability = detect_capability(primary_agent, prompt)
    except UnsupportedCapabilityError as error:
        return _error_response("unsupported_capability", str(error), 422)

    # Resolve the ID through ANS instead of accepting an agent URL from the
    # browser. This keeps ANS as the source of truth for the remote endpoint.
    try:
        agent = get_agent(agent_id)
    except ANSAgentNotFoundError as error:
        return _error_response("agent_not_found", str(error), 404)
    except ANSClientError as error:
        return _error_response("ans_unavailable", str(error), 502)

    try:
        # This outbound request is Agent A's delegation. The original wording
        # is preserved so Agent B receives exactly what the user asked.
        result = send_message(agent, prompt)
    except A2AClientError as error:
        return _error_response("a2a_failed", str(error), 502)

    return jsonify(
        {
            "primary_agent": {
                "id": primary_agent["id"],
                "name": primary_agent["name"],
                "role": primary_agent["role"],
            },
            "capability": capability.name,
            "capability_label": capability.label,
            "agent_id": agent["agent_id"],
            "agent_name": agent["name"],
            **result,
        }
    )


def _error_response(code, message, status_code):
    """Return API errors in one predictable JSON format."""
    # Keeping every error in the same shape makes the future JavaScript simpler:
    # it can always read response.error.code and response.error.message.
    return jsonify({"error": {"code": code, "message": message}}), status_code


if __name__ == "__main__":
    app.run(debug=True)
