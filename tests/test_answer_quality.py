import unittest

from services.answer_quality import assess_answer_quality


class AnswerQualityTests(unittest.TestCase):
    def test_detailed_answer_is_useful(self):
        result = assess_answer_quality(
            "Drop-in sauna sessions are $49 and last 45 minutes. "
            "Weekday appointments run from 9 AM to 7 PM."
        )

        self.assertEqual(result["status"], "useful")
        self.assertEqual(result["message"], "")

    def test_refusal_with_contact_redirect_is_limited(self):
        result = assess_answer_quality(
            "I'm currently unable to retrieve our specific catering service "
            "offerings through our system. Please contact us directly for "
            "menu options and pricing."
        )

        self.assertEqual(result["status"], "limited")
        self.assertIn("fallback", result["message"])

    def test_short_refusal_is_limited_without_a_redirect(self):
        result = assess_answer_quality(
            "I cannot provide those details right now. Please try again later."
        )

        self.assertEqual(result["status"], "limited")

    def test_useful_answer_can_still_include_booking_contact(self):
        result = assess_answer_quality(
            "The massage is $90 for 60 minutes and includes aromatherapy. "
            "Contact us to book your preferred time."
        )

        self.assertEqual(result["status"], "useful")


if __name__ == "__main__":
    unittest.main()
