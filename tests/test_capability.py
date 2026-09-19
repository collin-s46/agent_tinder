import unittest

from services.capability import UnsupportedCapabilityError, detect_capability
from services.primary_agents import get_primary_agent


class CapabilityDetectionTests(unittest.TestCase):
    def setUp(self):
        self.spark = get_primary_agent("spark")
        self.sage = get_primary_agent("sage")

    def test_spark_detects_each_supported_event_topic(self):
        cases = (
            (
                "I need catering for a graduation party.",
                "catering",
                "event catering",
            ),
            ("Find a DJ for my birthday party.", "entertainment", "event planning"),
            ("Help me find a wedding venue.", "venue", "wedding venue"),
            ("We need an event photographer.", "photography", "photography"),
        )

        for prompt, expected_name, expected_query in cases:
            with self.subTest(prompt=prompt):
                capability = detect_capability(self.spark, prompt)
                self.assertEqual(capability.name, expected_name)
                self.assertEqual(capability.search_query, expected_query)

    def test_sage_detects_each_supported_wellness_topic(self):
        cases = (
            ("What massage services and prices are available?", "spa", "spa"),
            ("How much does a sauna session cost?", "sauna", "sauna"),
            ("Find a beginner fitness program.", "fitness", "fitness"),
        )

        for prompt, expected_name, expected_query in cases:
            with self.subTest(prompt=prompt):
                capability = detect_capability(self.sage, prompt)
                self.assertEqual(capability.name, expected_name)
                self.assertEqual(capability.search_query, expected_query)

    def test_selected_agent_limits_the_available_topics(self):
        with self.assertRaisesRegex(
            UnsupportedCapabilityError,
            "Sage handles questions about",
        ):
            detect_capability(self.sage, "I need catering for a graduation party.")

    def test_specific_rule_wins_before_a_broad_rule(self):
        capability = detect_capability(
            self.spark,
            "I need catering for a birthday party.",
        )

        self.assertEqual(capability.name, "catering")


if __name__ == "__main__":
    unittest.main()
