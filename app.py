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
from services.scoring import score_candidate


# Read values from a local .env file into environment variables. This happens
# before any request is handled so the ANS client can find its credentials.
load_dotenv()

# Flask uses this application object to register routes and run the web server.
app = Flask(__name__)


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
    payload = request.get_json(silent=True) or {}
    primary_agent_id = payload.get("primary_agent_id", "")
    prompt = payload.get("prompt", "")

    # Reject empty or non-text prompts before doing any external API work.
    if not isinstance(prompt, str) or not prompt.strip():
        return _error_response("missing_prompt", "Please enter a request.", 400)

    prompt = prompt.strip()

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

    # Give each ANS result a small, explainable compatibility score before the
    # browser renders it as a card.
    scored_candidates = []
    for candidate in candidates:
        scored_candidate = candidate.copy()
        scored_candidate["compatibility"] = score_candidate(
            prompt,
            capability.name,
            candidate,
        )
        scored_candidates.append(scored_candidate)

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
    """Resolve a selected ANS agent and send it the user's request over A2A."""
    payload = request.get_json(silent=True) or {}
    agent_id = payload.get("agent_id", "")
    prompt = payload.get("prompt", "")

    if not isinstance(agent_id, str) or not agent_id.strip():
        return _error_response("missing_agent", "Please select an agent.", 400)
    if not isinstance(prompt, str) or not prompt.strip():
        return _error_response("missing_prompt", "Please enter a request.", 400)

    # Resolve the ID through ANS instead of accepting an agent URL from the
    # browser. This keeps ANS as the source of truth for the remote endpoint.
    try:
        agent = get_agent(agent_id.strip())
    except ANSAgentNotFoundError as error:
        return _error_response("agent_not_found", str(error), 404)
    except ANSClientError as error:
        return _error_response("ans_unavailable", str(error), 502)

    try:
        result = send_message(agent, prompt.strip())
    except A2AClientError as error:
        return _error_response("a2a_failed", str(error), 502)

    return jsonify(
        {
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
