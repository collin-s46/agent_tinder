from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from services.ans_client import (
    ANSClientError,
    ANSConfigurationError,
    search_agents,
)
from services.capability import UnsupportedCapabilityError, detect_capability


load_dotenv()
app = Flask(__name__)


@app.get("/")
def index():
    """Render the AgenTinder homepage."""
    return render_template("index.html")


@app.post("/api/search")
def search():
    """Detect the requested capability and return matching ANS agents."""
    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt", "")

    if not isinstance(prompt, str) or not prompt.strip():
        return _error_response("missing_prompt", "Please enter a request.", 400)

    prompt = prompt.strip()

    try:
        capability = detect_capability(prompt)
    except UnsupportedCapabilityError as error:
        return _error_response("unsupported_capability", str(error), 422)

    try:
        candidates = search_agents(capability.search_query)
    except ANSConfigurationError as error:
        return _error_response("ans_not_configured", str(error), 503)
    except ANSClientError as error:
        return _error_response("ans_unavailable", str(error), 502)

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
    return jsonify({"error": {"code": code, "message": message}}), status_code


if __name__ == "__main__":
    app.run(debug=True)
