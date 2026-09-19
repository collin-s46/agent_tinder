import unittest
from unittest.mock import patch

from app import app
from services.a2a_client import A2AClientError
from services.ans_client import (
    ANSAgentNotFoundError,
    ANSClientError,
    ANSConfigurationError,
)


class SearchRouteTests(unittest.TestCase):
    """Check the Flask routes without contacting the real ANS service."""

    def setUp(self):
        # Flask's test client calls routes in memory, so no server is required.
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_homepage_renders(self):
        response = self.client.get("/")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("AgenTinder", page)
        self.assertIn("Spark", page)
        self.assertIn("Event Planner", page)
        self.assertIn("Sage", page)
        self.assertIn("Wellness Concierge", page)
        self.assertIn('data-agent-id="sage"', page)

    def test_search_requires_a_prompt(self):
        response = self.client.post("/api/search", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"]["code"], "missing_prompt")

    def test_search_rejects_an_unsupported_prompt(self):
        response = self.client.post(
            "/api/search",
            json={
                "primary_agent_id": "sage",
                "prompt": "Help me write a history essay.",
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json["error"]["code"], "unsupported_capability"
        )

    @patch("app.search_agents")
    def test_search_returns_normalized_candidates(self, mock_search_agents):
        # Replace the real network call with a predictable result. Route tests
        # should test our Flask logic, not depend on the internet being online.
        mock_search_agents.return_value = [
            {
                "agent_id": "agent-123",
                "name": "HaloHeat Sauna Studios Customer Support Agent",
            }
        ]

        response = self.client.post(
            "/api/search",
            json={
                "primary_agent_id": "sage",
                "prompt": (
                    "What services does HaloHeat offer, and how much is a "
                    "drop-in sauna session?"
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["primary_agent"]["id"], "sage")
        self.assertEqual(response.json["primary_agent"]["name"], "Sage")
        self.assertEqual(response.json["capability"], "sauna")
        self.assertEqual(response.json["capability_label"], "Sauna")
        self.assertEqual(response.json["search_query"], "sauna")
        self.assertEqual(response.json["candidates"][0]["agent_id"], "agent-123")
        self.assertEqual(response.json["candidates"][0]["compatibility"]["score"], 60)

        # This also verifies that capability detection produced the correct ANS
        # search phrase.
        mock_search_agents.assert_called_once_with("sauna")

    @patch("app.search_agents")
    def test_spark_uses_its_event_topic_to_search_ans(self, mock_search_agents):
        mock_search_agents.return_value = []

        response = self.client.post(
            "/api/search",
            json={
                "primary_agent_id": "spark",
                "prompt": "What catering options are available for a graduation party?",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["primary_agent"]["name"], "Spark")
        self.assertEqual(response.json["capability"], "catering")
        self.assertEqual(response.json["search_query"], "catering")
        mock_search_agents.assert_called_once_with("catering")

    @patch("app.search_agents")
    def test_search_reports_invalid_configuration(self, mock_search_agents):
        mock_search_agents.side_effect = ANSConfigurationError("Invalid timeout.")

        response = self.client.post(
            "/api/search",
            json={
                "primary_agent_id": "sage",
                "prompt": "What services does HaloHeat offer?",
            },
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["error"]["code"], "ans_configuration")

    @patch("app.search_agents")
    def test_search_reports_ans_failures(self, mock_search_agents):
        mock_search_agents.side_effect = ANSClientError("ANS is unavailable.")

        response = self.client.post(
            "/api/search",
            json={
                "primary_agent_id": "sage",
                "prompt": "What services does HaloHeat offer?",
            },
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json["error"]["code"], "ans_unavailable")

    def test_search_requires_a_valid_primary_agent(self):
        response = self.client.post(
            "/api/search",
            json={"prompt": "What services does HaloHeat offer?"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json["error"]["code"], "invalid_primary_agent"
        )

    def test_search_rejects_an_unknown_primary_agent(self):
        response = self.client.post(
            "/api/search",
            json={
                "primary_agent_id": "atlas",
                "prompt": "What services does HaloHeat offer?",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json["error"]["code"], "invalid_primary_agent"
        )

    def test_match_requires_an_agent_id(self):
        response = self.client.post(
            "/api/match",
            json={"prompt": "What services does HaloHeat offer?"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"]["code"], "missing_agent")

    @patch("app.send_message")
    @patch("app.get_agent")
    def test_match_returns_a2a_answer(self, mock_get_agent, mock_send_message):
        mock_get_agent.return_value = {
            "agent_id": "agent-123",
            "name": "HaloHeat Support Agent",
        }
        mock_send_message.return_value = {
            "task_id": "task-123",
            "context_id": "context-123",
            "answer": "Drop-in sessions are $49.",
            "protocol_version": "0.3.0",
        }

        response = self.client.post(
            "/api/match",
            json={
                "agent_id": "agent-123",
                "prompt": "What services does HaloHeat offer?",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["agent_name"], "HaloHeat Support Agent")
        self.assertEqual(response.json["answer"], "Drop-in sessions are $49.")
        mock_get_agent.assert_called_once_with("agent-123")

    @patch("app.get_agent")
    def test_match_reports_a_missing_agent(self, mock_get_agent):
        mock_get_agent.side_effect = ANSAgentNotFoundError("Agent not found.")

        response = self.client.post(
            "/api/match",
            json={
                "agent_id": "missing-agent",
                "prompt": "What services does HaloHeat offer?",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"]["code"], "agent_not_found")

    @patch("app.send_message")
    @patch("app.get_agent")
    def test_match_reports_a2a_failures(self, mock_get_agent, mock_send_message):
        mock_get_agent.return_value = {
            "agent_id": "agent-123",
            "name": "HaloHeat Support Agent",
        }
        mock_send_message.side_effect = A2AClientError("Agent unavailable.")

        response = self.client.post(
            "/api/match",
            json={
                "agent_id": "agent-123",
                "prompt": "What services does HaloHeat offer?",
            },
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json["error"]["code"], "a2a_failed")


if __name__ == "__main__":
    unittest.main()
