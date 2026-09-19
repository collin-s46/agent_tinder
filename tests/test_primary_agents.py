import unittest

from services.primary_agents import (
    PRIMARY_AGENTS,
    get_primary_agent,
    list_primary_agents,
)


class PrimaryAgentConfigurationTests(unittest.TestCase):
    def test_iteration_one_contains_only_the_two_verified_agents(self):
        self.assertEqual(list(PRIMARY_AGENTS), ["spark", "sage"])

    def test_every_agent_has_complete_identity_and_topic_rules(self):
        for agent_id, agent in PRIMARY_AGENTS.items():
            with self.subTest(agent_id=agent_id):
                self.assertEqual(agent["id"], agent_id)
                self.assertTrue(agent["name"])
                self.assertTrue(agent["role"])
                self.assertTrue(agent["description"])
                self.assertTrue(agent["icon"])
                self.assertTrue(agent["theme"])
                self.assertGreaterEqual(len(agent["example_prompts"]), 2)
                self.assertGreaterEqual(len(agent["topic_rules"]), 1)

                for rule in agent["topic_rules"]:
                    self.assertTrue(rule["id"])
                    self.assertTrue(rule["label"])
                    self.assertTrue(rule["keywords"])
                    self.assertTrue(rule["search_query"])

    def test_get_primary_agent_normalizes_the_id(self):
        self.assertEqual(get_primary_agent(" SPARK ")["name"], "Spark")

    def test_get_primary_agent_rejects_an_unknown_or_non_text_id(self):
        self.assertIsNone(get_primary_agent("atlas"))
        self.assertIsNone(get_primary_agent(None))

    def test_list_primary_agents_preserves_display_order(self):
        names = [agent["name"] for agent in list_primary_agents()]
        self.assertEqual(names, ["Spark", "Sage"])


if __name__ == "__main__":
    unittest.main()
