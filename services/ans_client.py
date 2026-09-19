"""Client for discovering A2A agents through GoDaddy ANS."""

import os
from urllib.parse import quote

import requests


class ANSClientError(RuntimeError):
    """Raised when ANS cannot complete a search."""


class ANSConfigurationError(ANSClientError):
    """Raised when local ANS configuration is invalid."""


class ANSAgentNotFoundError(ANSClientError):
    """Raised when a selected agent no longer exists in ANS."""


def search_agents(query, page_size=5):
    """Search ANS and return normalized A2A-over-HTTP candidates."""
    # ANS discovery is a public, read-only registry endpoint, so this request
    # does not send the user's PAT or any other credential. These settings have
    # safe defaults but can be changed in .env for testing.
    base_url = os.getenv("ANS_BASE_URL", "https://api.godaddy.com").rstrip("/")
    timeout = _read_timeout()

    # Ask ANS for a small result set containing only agents that advertise the
    # protocol and network transport required by this MVP.
    params = {
        "query": query,
        "pageSize": max(1, min(int(page_size), 100)),
        "profile": "default",
        "protocols": "A2A",
        "transports": "HTTP",
    }

    # Ask GoDaddy to return JSON. No Authorization header is needed for this
    # public discovery operation.
    headers = {
        "Accept": "application/json",
    }

    try:
        # The timeout prevents a slow external service from hanging Flask
        # forever. raise_for_status() turns 4xx/5xx responses into exceptions.
        response = requests.get(
            f"{base_url}/v1/ans/registered-agents",
            params=params,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        status = getattr(getattr(error, "response", None), "status_code", None)
        detail = f" (HTTP {status})" if status else ""
        raise ANSClientError(f"ANS search failed{detail}.") from error

    try:
        # A successful HTTP status does not guarantee that the body is valid
        # JSON, so parsing gets its own friendly error.
        payload = response.json()
    except ValueError as error:
        raise ANSClientError("ANS returned an invalid JSON response.") from error

    items = payload.get("items", [])
    if not isinstance(items, list):
        raise ANSClientError("ANS returned an unexpected response format.")

    # ANS returns more information than the UI needs. Normalize every record and
    # drop entries that do not actually contain a usable A2A-over-HTTP endpoint.
    candidates = []
    for item in items:
        candidate = _normalize_agent(item)
        if candidate is not None:
            candidates.append(candidate)

    return candidates


def get_agent(agent_id):
    """Retrieve one selected agent from ANS and normalize its metadata."""
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise ANSAgentNotFoundError("The selected agent ID is missing.")

    base_url = os.getenv("ANS_BASE_URL", "https://api.godaddy.com").rstrip("/")
    timeout = _read_timeout()

    # quote() keeps the ID inside one URL path segment. The browser supplies only
    # an ID; it never gets to choose the remote URL that Flask will contact.
    safe_agent_id = quote(agent_id.strip(), safe="")
    url = f"{base_url}/v1/ans/registered-agents/{safe_agent_id}"

    try:
        response = requests.get(
            url,
            params={"profile": "default"},
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        status = getattr(getattr(error, "response", None), "status_code", None)
        if status == 404:
            raise ANSAgentNotFoundError(
                "The selected agent is no longer available in ANS."
            ) from error
        detail = f" (HTTP {status})" if status else ""
        raise ANSClientError(f"ANS agent lookup failed{detail}.") from error

    try:
        payload = response.json()
    except ValueError as error:
        raise ANSClientError("ANS returned invalid agent metadata.") from error

    candidate = _normalize_agent(payload)
    if candidate is None:
        raise ANSClientError(
            "The selected ANS agent has no usable A2A-over-HTTP endpoint."
        )

    return candidate


def _read_timeout():
    """Read a safe HTTP timeout from the environment."""
    raw_timeout = os.getenv("ANS_TIMEOUT_SECONDS", "10")
    try:
        # Never allow zero or a negative timeout, even if .env contains one.
        return max(1.0, float(raw_timeout))
    except ValueError as error:
        raise ANSConfigurationError(
            "ANS_TIMEOUT_SECONDS must be a number."
        ) from error


def _normalize_agent(item):
    """Convert a registry record into the small shape used by the UI."""
    # An ANS agent can advertise several endpoints. The MVP needs only one that
    # speaks A2A over HTTP.
    endpoint = _find_a2a_http_endpoint(item.get("endpoints", []))
    if endpoint is None:
        return None

    functions = endpoint.get("functions", [])
    skills = []

    # ANS calls these records "functions"; the AgenTinder UI presents them as
    # skills because that is easier for users to understand.
    for function in functions:
        skills.append(
            {
                "id": function.get("id", ""),
                "name": function.get("name", ""),
                "tags": function.get("tags", []),
            }
        )

    lifecycle = item.get("lifecycle", {})
    scores = item.get("scores", {})

    # .get(..., default) keeps a partially filled registry record from crashing
    # the whole search response.
    return {
        "agent_id": item.get("agentId", ""),
        "ans_name": item.get("ansName", ""),
        "name": item.get("agentDisplayName", "Unnamed agent"),
        "description": item.get("agentDescription", ""),
        "status": lifecycle.get("status", "UNKNOWN"),
        "discovered_via_ans": True,
        "agent_url": endpoint.get("agentUrl", ""),
        "metadata_url": endpoint.get("metaDataUrl", ""),
        "protocol": endpoint.get("protocol", ""),
        "transports": endpoint.get("transports", []),
        "skills": skills,
        "scores": {
            "trust": scores.get("trustScore"),
            "relevance": scores.get("relevance"),
        },
    }


def _find_a2a_http_endpoint(endpoints):
    """Choose the first endpoint that matches the MVP transport requirements."""
    # We intentionally support one protocol/transport combination for the MVP.
    for endpoint in endpoints:
        transports = endpoint.get("transports", [])
        if endpoint.get("protocol") == "A2A" and "HTTP" in transports:
            return endpoint
    return None
