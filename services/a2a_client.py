"""Minimal A2A JSON-RPC client for the hackathon's synchronous demo."""

import os
import uuid
from urllib.parse import urlparse

import requests


class A2AClientError(RuntimeError):
    """Raised when a matched agent cannot complete the A2A request."""


def send_message(agent, prompt):
    """Verify an agent's public card, send a message, and return its answer."""
    agent_url = agent.get("agent_url", "")
    metadata_url = agent.get("metadata_url", "")
    _validate_agent_urls(agent_url, metadata_url)
    timeout = _read_timeout()

    # Read the public Agent Card before calling the agent. It tells AgenTinder
    # which A2A version, transport, and security requirements the agent uses.
    try:
        card_response = requests.get(
            metadata_url,
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
        card_response.raise_for_status()
        agent_card = card_response.json()
    except (requests.RequestException, ValueError) as error:
        raise A2AClientError("Unable to read the matched agent's Agent Card.") from error

    _validate_agent_card(agent_card, agent_url)

    # A2A 0.3 JSON-RPC uses message/send. messageId identifies this individual
    # message, while the remote agent creates the task and context identifiers.
    request_id = str(uuid.uuid4())
    request_body = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"kind": "text", "text": prompt}],
            }
        },
    }

    try:
        response = requests.post(
            agent_url,
            json=request_body,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as error:
        raise A2AClientError("The matched agent did not return a valid response.") from error

    if not isinstance(payload, dict):
        raise A2AClientError("The matched agent returned an invalid A2A response.")
    if payload.get("jsonrpc") != "2.0" or payload.get("id") != request_id:
        raise A2AClientError("The matched agent returned an invalid A2A response.")

    if payload.get("error"):
        error_payload = payload["error"]
        message = (
            error_payload.get("message", "The matched agent reported an error.")
            if isinstance(error_payload, dict)
            else "The matched agent reported an error."
        )
        raise A2AClientError(message)

    result = payload.get("result")
    if not isinstance(result, dict):
        raise A2AClientError("The matched agent returned no A2A result.")

    answer = _extract_answer(result)
    return {
        "task_id": result.get("id"),
        "context_id": result.get("contextId"),
        "answer": answer,
        "protocol_version": agent_card["protocolVersion"],
    }


def _validate_agent_urls(agent_url, metadata_url):
    """Allow only HTTPS URLs advertised by the selected ANS record."""
    agent_parts = urlparse(agent_url)
    metadata_parts = urlparse(metadata_url)

    if agent_parts.scheme != "https" or not agent_parts.hostname:
        raise A2AClientError("The selected agent has an invalid A2A URL.")
    if metadata_parts.scheme != "https" or not metadata_parts.hostname:
        raise A2AClientError("The selected agent has an invalid Agent Card URL.")
    if agent_parts.hostname != metadata_parts.hostname:
        raise A2AClientError("The A2A endpoint and Agent Card hosts do not match.")


def _validate_agent_card(agent_card, agent_url):
    """Limit the MVP to the one A2A shape we tested successfully."""
    if not isinstance(agent_card, dict):
        raise A2AClientError("The matched agent returned an invalid Agent Card.")
    if agent_card.get("preferredTransport") != "JSONRPC":
        raise A2AClientError("The matched agent does not support JSON-RPC.")
    if agent_card.get("protocolVersion") != "0.3.0":
        raise A2AClientError("The matched agent uses an unsupported A2A version.")
    if agent_card.get("security"):
        raise A2AClientError("The matched agent requires unsupported authentication.")
    if agent_card.get("url", "").rstrip("/") != agent_url.rstrip("/"):
        raise A2AClientError("The Agent Card does not match the ANS endpoint.")


def _extract_answer(result):
    """Extract text from either a direct Message or a completed Task."""
    if result.get("kind") == "message":
        parts = result.get("parts", [])
    elif result.get("kind") == "task":
        status = result.get("status", {})
        if status.get("state") != "completed":
            state = status.get("state", "unknown")
            raise A2AClientError(f"The matched agent returned task state '{state}'.")
        parts = status.get("message", {}).get("parts", [])
    else:
        raise A2AClientError("The matched agent returned an unknown A2A result type.")

    text_parts = [
        part.get("text", "").strip()
        for part in parts
        if part.get("kind") == "text" and part.get("text", "").strip()
    ]
    if not text_parts:
        raise A2AClientError("The matched agent completed without a text answer.")

    return "\n\n".join(text_parts)


def _read_timeout():
    """Read a bounded timeout so a remote agent cannot hang Flask forever."""
    raw_timeout = os.getenv("A2A_TIMEOUT_SECONDS", "20")
    try:
        return max(1.0, float(raw_timeout))
    except ValueError as error:
        raise A2AClientError("A2A_TIMEOUT_SECONDS must be a number.") from error
