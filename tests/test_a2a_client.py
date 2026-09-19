import os
import unittest
from unittest.mock import Mock, patch

from services.a2a_client import A2AClientError, send_message


class A2AClientTests(unittest.TestCase):
    """Check Agent Card validation, JSON-RPC construction, and task parsing."""

    def setUp(self):
        self.agent = {
            "agent_url": "https://haloheat.example/a2a",
            "metadata_url": (
                "https://haloheat.example/.well-known/agent-card.json"
            ),
        }
        self.agent_card = {
            "url": "https://haloheat.example/a2a",
            "preferredTransport": "JSONRPC",
            "protocolVersion": "0.3.0",
            "security": [],
        }

    @patch("services.a2a_client.requests.post")
    @patch("services.a2a_client.requests.get")
    def test_send_message_returns_completed_task_answer(self, mock_get, mock_post):
        card_response = Mock()
        card_response.json.return_value = self.agent_card
        mock_get.return_value = card_response

        message_response = Mock()
        message_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "rpc-123",
            "result": {
                "kind": "task",
                "id": "task-123",
                "contextId": "context-123",
                "status": {
                    "state": "completed",
                    "message": {
                        "kind": "message",
                        "parts": [
                            {
                                "kind": "text",
                                "text": "Drop-in sessions are $49.",
                            }
                        ],
                    },
                },
            },
        }
        mock_post.return_value = message_response

        with patch.dict(os.environ, {"A2A_TIMEOUT_SECONDS": "12"}, clear=True):
            result = send_message(
                self.agent,
                "What services does HaloHeat offer?",
            )

        self.assertEqual(result["task_id"], "task-123")
        self.assertEqual(result["answer"], "Drop-in sessions are $49.")
        self.assertEqual(result["protocol_version"], "0.3.0")

        request_body = mock_post.call_args.kwargs["json"]
        self.assertEqual(request_body["method"], "message/send")
        self.assertEqual(
            request_body["params"]["message"]["parts"][0]["text"],
            "What services does HaloHeat offer?",
        )
        self.assertEqual(mock_post.call_args.kwargs["timeout"], 12.0)

    @patch("services.a2a_client.requests.get")
    def test_send_message_rejects_unsupported_protocol_version(self, mock_get):
        card_response = Mock()
        card_response.json.return_value = {
            **self.agent_card,
            "protocolVersion": "1.0.0",
        }
        mock_get.return_value = card_response

        with self.assertRaisesRegex(A2AClientError, "unsupported A2A version"):
            send_message(self.agent, "Hello")

    def test_send_message_rejects_mismatched_hosts(self):
        agent = {
            **self.agent,
            "metadata_url": "https://unexpected.example/agent-card.json",
        }

        with self.assertRaisesRegex(A2AClientError, "hosts do not match"):
            send_message(agent, "Hello")


if __name__ == "__main__":
    unittest.main()
