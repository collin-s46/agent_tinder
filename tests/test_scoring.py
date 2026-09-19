import unittest

from services.scoring import score_candidate


class CompatibilityScoringTests(unittest.TestCase):
    """Verify that the three scoring rules remain simple and predictable."""

    def setUp(self):
        self.prompt = "What services does HaloHeat offer?"
        self.capability = "customer-support"
        self.base_candidate = {
            "description": "Answers questions about products and services.",
            "protocol": "A2A",
            "transports": ["HTTP"],
            "skills": [
                {
                    "id": "answer-questions",
                    "name": "Answer Questions",
                    "tags": ["customer-support"],
                }
            ],
        }

    def test_exact_candidate_receives_full_score(self):
        candidate = {
            **self.base_candidate,
            "name": "HaloHeat Sauna Studios Customer Support Agent",
            "ans_name": "ans://v1.0.0.support.haloheat.example",
        }

        result = score_candidate(self.prompt, self.capability, candidate)

        self.assertEqual(result["score"], 100)
        self.assertEqual(result["breakdown"]["target_match"], 60)
        self.assertEqual(result["breakdown"]["capability_match"], 20)
        self.assertEqual(result["breakdown"]["protocol_match"], 20)

    def test_unrelated_support_agent_does_not_receive_target_points(self):
        candidate = {
            **self.base_candidate,
            "name": "Another Business Support Agent",
            "ans_name": "ans://v1.0.0.support.other.example",
        }

        result = score_candidate(self.prompt, self.capability, candidate)

        self.assertEqual(result["score"], 40)
        self.assertEqual(result["breakdown"]["target_match"], 0)


if __name__ == "__main__":
    unittest.main()
