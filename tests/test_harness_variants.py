import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.harness_variants import (
    HarnessVariantInputError,
    compare_harness_variants,
    write_harness_variants_report,
)


def fixed_questions():
    return pd.DataFrame(
        [
            {
                "question_id": "q1",
                "requires_numbers": True,
                "requires_tools": True,
                "requires_state_enforcement": False,
                "requires_evidence": False,
                "requires_quality_gate": False,
                "requires_replay": False,
                "requires_human_review": False,
            },
            {
                "question_id": "q2",
                "requires_numbers": True,
                "requires_tools": True,
                "requires_state_enforcement": True,
                "requires_evidence": True,
                "requires_quality_gate": True,
                "requires_replay": False,
                "requires_human_review": False,
            },
            {
                "question_id": "q3",
                "requires_numbers": True,
                "requires_tools": True,
                "requires_state_enforcement": True,
                "requires_evidence": True,
                "requires_quality_gate": True,
                "requires_replay": True,
                "requires_human_review": True,
            },
        ]
    )


class HarnessVariantTests(unittest.TestCase):
    def test_compare_harness_variants_scores_capabilities(self):
        result = compare_harness_variants(fixed_questions())

        score_by_variant = dict(zip(result.summary["variant"], result.summary["score"]))
        self.assertEqual(0, score_by_variant["A"])
        self.assertLess(score_by_variant["D"], 1)
        self.assertEqual(1, score_by_variant["E"])
        self.assertEqual(15, len(result.questions))

    def test_variant_d_has_quality_gate_but_not_replay_or_review(self):
        result = compare_harness_variants(fixed_questions())
        d_summary = result.summary[result.summary["variant"] == "D"].iloc[0]

        self.assertEqual(3, d_summary["quality_gate_count"])
        self.assertEqual(2, d_summary["replayable_count"])
        self.assertEqual(2, d_summary["human_review_count"])
        self.assertEqual("limited", d_summary["status"])

    def test_invalid_question_schema_raises_clear_error(self):
        with self.assertRaisesRegex(HarnessVariantInputError, "missing required columns"):
            compare_harness_variants(pd.DataFrame({"question_id": ["q1"]}))

    def test_write_harness_variants_report(self):
        result = compare_harness_variants(fixed_questions())

        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_harness_variants_report(
                result,
                Path(tmpdir) / "harness_variants.md",
            )

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Harness Variant Comparison A-E", text)
            self.assertIn("Financial strategy A-E and harness A-E", text)


if __name__ == "__main__":
    unittest.main()
