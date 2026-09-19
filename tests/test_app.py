import unittest
from unittest.mock import patch

from app import app
from services.ans_client import ANSClientError, ANSConfigurationError


class SearchRouteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_homepage_renders(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("AgenTinder", response.get_data(as_text=True))

    def test_search_requires_a_prompt(self):
        response = self.client.post("/api/search", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"]["code"], "missing_prompt")

    def test_search_rejects_an_unsupported_prompt(self):
        response = self.client.post(
            "/api/search", json={"prompt": "Help me write a history essay."}
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json["error"]["code"], "unsupported_capability"
        )

    @patch("app.search_agents")
    def test_search_returns_normalized_candidates(self, mock_search_agents):
        mock_search_agents.return_value = [
            {
                "agent_id": "agent-123",
                "name": "HaloHeat Sauna Studios Customer Support Agent",
            }
        ]

        response = self.client.post(
            "/api/search",
            json={
                "prompt": (
                    "What services does HaloHeat offer, and how much is a "
                    "drop-in sauna session?"
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["capability"], "customer-support")
        self.assertEqual(response.json["search_query"], "HaloHeat Sauna")
        self.assertEqual(response.json["candidates"][0]["agent_id"], "agent-123")
        mock_search_agents.assert_called_once_with("HaloHeat Sauna")

    @patch("app.search_agents")
    def test_search_reports_missing_configuration(self, mock_search_agents):
        mock_search_agents.side_effect = ANSConfigurationError("Missing credentials.")

        response = self.client.post(
            "/api/search",
            json={"prompt": "What services does HaloHeat offer?"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["error"]["code"], "ans_not_configured")

    @patch("app.search_agents")
    def test_search_reports_ans_failures(self, mock_search_agents):
        mock_search_agents.side_effect = ANSClientError("ANS is unavailable.")

        response = self.client.post(
            "/api/search",
            json={"prompt": "What services does HaloHeat offer?"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json["error"]["code"], "ans_unavailable")


if __name__ == "__main__":
    unittest.main()
