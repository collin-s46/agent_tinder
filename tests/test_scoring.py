import unittest

from services.capability import Capability
from services.scoring import MINIMUM_COMPATIBILITY_SCORE, score_candidate


class CompatibilityScoringTests(unittest.TestCase):
    """Verify that the five generic scoring rules remain predictable."""

    def setUp(self):
        self.prompt = (
            "What services does HaloHeat offer, and how much is a sauna session?"
        )
        self.capability = Capability(
            name="sauna",
            label="Sauna",
            search_query="sauna",
        )
        self.base_candidate = {
            "agent_id": "agent-123",
            "ans_name": "ans://v1.0.0.support.example",
            "description": "Answers questions about products and services.",
            "status": "ACTIVE",
            "protocol": "A2A",
            "transports": ["HTTP"],
            "scores": {"trust": 37},
            "skills": [
                {
                    "id": "answer-questions",
                    "name": "Answer Questions",
                    "tags": ["customer-support", "product-info"],
                }
            ],
        }

    def test_relevant_active_candidate_receives_full_score(self):
        candidate = {
            **self.base_candidate,
            "name": "HaloHeat Sauna Studios Customer Support Agent",
        }

        result = score_candidate(self.prompt, self.capability, candidate)

        self.assertEqual(result["score"], 100)
        self.assertEqual(result["breakdown"]["capability_relevance"], 40)
        self.assertEqual(result["breakdown"]["prompt_alignment"], 25)
        self.assertEqual(result["breakdown"]["protocol_compatibility"], 20)
        self.assertEqual(result["breakdown"]["active_status"], 10)
        self.assertEqual(result["breakdown"]["registry_metadata"], 5)

    def test_unrelated_agent_falls_below_the_display_threshold(self):
        candidate = {
            **self.base_candidate,
            "name": "Another Business Support Agent",
        }

        result = score_candidate(self.prompt, self.capability, candidate)

        self.assertEqual(result["score"], 35)
        self.assertLess(result["score"], MINIMUM_COMPATIBILITY_SCORE)
        self.assertEqual(result["breakdown"]["capability_relevance"], 0)
        self.assertEqual(result["breakdown"]["prompt_alignment"], 0)

    def test_one_shared_prompt_word_receives_partial_alignment_points(self):
        candidate = {
            **self.base_candidate,
            "name": "Neighborhood Sauna Support Agent",
        }

        result = score_candidate(self.prompt, self.capability, candidate)

        self.assertEqual(result["breakdown"]["prompt_alignment"], 15)
        self.assertEqual(result["score"], 90)

    def test_missing_protocol_status_and_registry_metadata_earn_no_points(self):
        candidate = {
            "name": "Golden Spa",
            "description": "Massage and spa treatments.",
            "skills": [],
            "protocol": "REST",
            "transports": [],
            "status": "INACTIVE",
            "scores": {"trust": None},
        }
        capability = Capability(
            name="spa",
            label="Spa and massage",
            search_query="spa",
        )

        result = score_candidate("Find a spa massage.", capability, candidate)

        self.assertEqual(result["score"], 65)
        self.assertEqual(result["breakdown"]["protocol_compatibility"], 0)
        self.assertEqual(result["breakdown"]["active_status"], 0)
        self.assertEqual(result["breakdown"]["registry_metadata"], 0)


if __name__ == "__main__":
    unittest.main()
