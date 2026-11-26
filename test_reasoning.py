
import unittest

from modules.reasoning_engine import (
    detect_conflicts,
    assess_reliability,
    answer_question
)


class TestReasoningEngine(unittest.TestCase):

    def setUp(self):
        self.facts = [
            {
                "entity": "Rahul",
                "attribute": "Joining Date",
                "value": "10 June 2022",
                "source": "employee.pdf",
                "location": "Page 2",
                "modality": "PDF",
                "extraction_quality": "HIGH",
                "raw_text": "Rahul joined on 10 June 2022."
            },
            {
                "entity": "Rahul",
                "attribute": "Joining Date",
                "value": "15 June 2022",
                "source": "id_card.jpg",
                "location": "Image",
                "modality": "IMAGE",
                "extraction_quality": "MEDIUM",
                "raw_text": "Rahul joined on 15 June 2022."
            },
            {
                "entity": "Rahul",
                "attribute": "Joining Date",
                "value": "10 June 2022",
                "source": "employee.xlsx",
                "location": "Sheet1, Row 3",
                "modality": "EXCEL",
                "extraction_quality": "HIGH",
                "raw_text": "Rahul joined on 10 June 2022."
            }
        ]

    def test_conflict_detection(self):
        conflicts = detect_conflicts(self.facts)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["status"], "CONFLICTING")

    def test_no_conflict(self):
        facts = [self.facts[0], self.facts[2]]
        conflicts = detect_conflicts(facts)
        self.assertEqual(conflicts, [])

    def test_empty_facts(self):
        self.assertEqual(detect_conflicts([]), [])
        self.assertEqual(assess_reliability([]), [])

    def test_reliability_assessment(self):
        reliability = assess_reliability(self.facts)
        self.assertEqual(len(reliability), 3)
        self.assertIn("indicators", reliability[0])

    def test_conflicting_answer(self):
        conflicts = detect_conflicts(self.facts)
        reliability = assess_reliability(self.facts)

        result = answer_question(
            "What is Rahul's joining date?",
            self.facts,
            conflicts,
            reliability
        )

        self.assertEqual(result["status"], "CONFLICTING")
        self.assertTrue(result["contradicting_evidence"])

    def test_insufficient_evidence(self):
        result = answer_question(
            "What is Rahul's salary?",
            self.facts,
            [],
            []
        )

        self.assertEqual(
            result["status"],
            "INSUFFICIENT_EVIDENCE"
        )

    def test_supported_answer(self):
        facts = [self.facts[0], self.facts[2]]
        conflicts = detect_conflicts(facts)
        reliability = assess_reliability(facts)

        result = answer_question(
            "What is Rahul's joining date?",
            facts,
            conflicts,
            reliability
        )

        self.assertEqual(result["status"], "SUPPORTED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
