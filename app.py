from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from services.ans_client import (
    ANSClientError,
    ANSConfigurationError,
    search_agents,
)
from services.capability import UnsupportedCapabilityError, detect_capability


# Read values from a local .env file into environment variables. This happens
# before any request is handled so the ANS client can find its credentials.
load_dotenv()

# Flask uses this application object to register routes and run the web server.
app = Flask(__name__)


@app.get("/")
def index():
    """Render the AgenTinder homepage."""
    return render_template("index.html")


@app.post("/api/search")
def search():
    """Detect the requested capability and return matching ANS agents."""
    # The future JavaScript button will send JSON shaped like:
    # {"prompt": "What services does HaloHeat offer?"}
    # silent=True lets us return our own friendly error if the body is not JSON.
    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt", "")

    # Reject empty or non-text prompts before doing any external API work.
    if not isinstance(prompt, str) or not prompt.strip():
        return _error_response("missing_prompt", "Please enter a request.", 400)

    prompt = prompt.strip()

    # Convert the natural-language request into the one capability and search
    # query supported by this MVP. This is intentionally deterministic—there is
    # no LLM call or complex orchestration here.
    try:
        capability = detect_capability(prompt)
    except UnsupportedCapabilityError as error:
        return _error_response("unsupported_capability", str(error), 422)

    # Search GoDaddy ANS only after the prompt has been validated and classified.
    # Configuration failures and external service failures get different status
    # codes so the frontend can explain what went wrong later.
    try:
        candidates = search_agents(capability.search_query)
    except ANSConfigurationError as error:
        return _error_response("ans_not_configured", str(error), 503)
    except ANSClientError as error:
        return _error_response("ans_unavailable", str(error), 502)

    # jsonify creates a JSON response and sets the correct Content-Type header.
    # Candidate records are already cleaned up by services/ans_client.py.
    return jsonify(
        {
            "prompt": prompt,
            "capability": capability.name,
            "search_query": capability.search_query,
            "candidates": candidates,
        }
    )


def _error_response(code, message, status_code):
    """Return API errors in one predictable JSON format."""
    # Keeping every error in the same shape makes the future JavaScript simpler:
    # it can always read response.error.code and response.error.message.
    return jsonify({"error": {"code": code, "message": message}}), status_code


if __name__ == "__main__":
    app.run(debug=True)
