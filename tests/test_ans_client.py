import os
import unittest
from unittest.mock import Mock, patch

from services.ans_client import (
    ANSClientError,
    ANSConfigurationError,
    get_agent,
    search_agents,
)


class ANSClientTests(unittest.TestCase):
    """Check ANS request construction and response normalization in isolation."""

    @patch("services.ans_client.requests.get")
    def test_search_builds_request_and_normalizes_agents(self, mock_get):
        # This fake response has the important fields from the real response the
        # user received during the manual HaloHeat ANS test.
        response = Mock()
        response.json.return_value = {
            "items": [
                {
                    "agentId": "agent-123",
                    "ansName": "ans://v1.0.0.haloheat.example",
                    "agentDisplayName": "HaloHeat Support Agent",
                    "agentDescription": "Answers product and service questions.",
                    "lifecycle": {"status": "ACTIVE"},
                    "scores": {"trustScore": 37, "relevance": 9.5},
                    "endpoints": [
                        {
                            "agentUrl": "https://haloheat.example/a2a",
                            "metaDataUrl": (
                                "https://haloheat.example/.well-known/"
                                "agent-card.json"
                            ),
                            "protocol": "A2A",
                            "transports": ["HTTP"],
                            "functions": [
                                {
                                    "id": "answer-questions",
                                    "name": "Answer Questions",
                                    "tags": ["customer-support"],
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        mock_get.return_value = response

        # patch.dict keeps this test independent from the developer's real .env
        # file and points the request at a fake base URL.
        environment = {
            "ANS_BASE_URL": "https://api.godaddy.test",
            "ANS_TIMEOUT_SECONDS": "7",
        }
        with patch.dict(os.environ, environment, clear=True):
            candidates = search_agents("HaloHeat Sauna")

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["agent_id"], "agent-123")
        self.assertEqual(candidates[0]["status"], "ACTIVE")
        self.assertEqual(candidates[0]["skills"][0]["id"], "answer-questions")
        mock_get.assert_called_once()

        # Inspect the mocked request to prove the client used the correct URL,
        # filters, public headers, and timeout.
        request = mock_get.call_args
        self.assertEqual(
            request.args[0],
            "https://api.godaddy.test/v1/ans/registered-agents",
        )
        self.assertEqual(request.kwargs["params"]["query"], "HaloHeat Sauna")
        self.assertEqual(request.kwargs["params"]["protocols"], "A2A")
        self.assertEqual(request.kwargs["params"]["transports"], "HTTP")
        self.assertNotIn("Authorization", request.kwargs["headers"])
        self.assertEqual(request.kwargs["timeout"], 7.0)

    def test_search_rejects_an_invalid_timeout(self):
        # Invalid local configuration should fail before any network request.
        with patch.dict(
            os.environ,
            {"ANS_TIMEOUT_SECONDS": "not-a-number"},
            clear=True,
        ):
            with self.assertRaises(ANSConfigurationError):
                search_agents("HaloHeat Sauna")

    @patch("services.ans_client.requests.get")
    def test_search_rejects_a_non_object_response(self, mock_get):
        response = Mock()
        response.json.return_value = ["unexpected"]
        mock_get.return_value = response

        with self.assertRaisesRegex(ANSClientError, "unexpected response"):
            search_agents("sauna")

    @patch("services.ans_client.requests.get")
    def test_get_agent_resolves_an_id_through_ans(self, mock_get):
        response = Mock()
        response.json.return_value = {
            "agentId": "agent-123",
            "ansName": "ans://v1.0.0.haloheat.example",
            "agentDisplayName": "HaloHeat Support Agent",
            "agentDescription": "Answers customer questions.",
            "lifecycle": {"status": "ACTIVE"},
            "endpoints": [
                {
                    "agentUrl": "https://haloheat.example/a2a",
                    "metaDataUrl": (
                        "https://haloheat.example/.well-known/agent-card.json"
                    ),
                    "protocol": "A2A",
                    "transports": ["HTTP"],
                    "functions": [],
                }
            ],
        }
        mock_get.return_value = response

        with patch.dict(
            os.environ,
            {"ANS_BASE_URL": "https://api.godaddy.test"},
            clear=True,
        ):
            agent = get_agent("agent-123")

        self.assertEqual(agent["agent_id"], "agent-123")
        self.assertEqual(agent["agent_url"], "https://haloheat.example/a2a")
        self.assertEqual(
            mock_get.call_args.args[0],
            "https://api.godaddy.test/v1/ans/registered-agents/agent-123",
        )


if __name__ == "__main__":
    unittest.main()
