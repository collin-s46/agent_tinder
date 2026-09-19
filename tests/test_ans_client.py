import os
import unittest
from unittest.mock import Mock, patch

from services.ans_client import ANSConfigurationError, search_agents


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

        # patch.dict supplies safe fake credentials only for this test. No real
        # key or secret belongs in source code or test fixtures.
        environment = {
            "GODADDY_API_KEY": "test-key",
            "GODADDY_API_SECRET": "test-secret",
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
        # filters, authentication format, and timeout.
        request = mock_get.call_args
        self.assertEqual(
            request.args[0],
            "https://api.godaddy.test/v1/ans/registered-agents",
        )
        self.assertEqual(request.kwargs["params"]["query"], "HaloHeat Sauna")
        self.assertEqual(request.kwargs["params"]["protocols"], "A2A")
        self.assertEqual(request.kwargs["params"]["transports"], "HTTP")
        self.assertEqual(
            request.kwargs["headers"]["Authorization"],
            "sso-key test-key:test-secret",
        )
        self.assertEqual(request.kwargs["timeout"], 7.0)

    def test_search_requires_credentials(self):
        # With an empty environment, the client should fail before it attempts a
        # network request and should tell the developer what configuration lacks.
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ANSConfigurationError):
                search_agents("HaloHeat Sauna")


if __name__ == "__main__":
    unittest.main()
