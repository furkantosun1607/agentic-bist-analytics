import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.evidence import (
    build_evidence_bundle,
    evaluate_quality_gate,
    quality_gate_to_dict,
    write_evidence_report,
)
from src.harness import AnalysisHarness
from src.validation import (
    ANALYSIS_SAFE,
    ANALYSIS_UNSAFE,
    BLOCKING,
    QualityIssue,
    QualityReport,
)


def evidence_records():
    return pd.DataFrame(
        [
            {
                "signal_id": "sig-1",
                "source": "unit_test",
                "known_at": "2024-01-01T18:10:00+03:00",
                "score": 0.42,
                "rsi_14": 31.5,
            },
            {
                "signal_id": "sig-2",
                "source": "unit_test",
                "known_at": "2024-01-02T18:10:00+03:00",
                "score": -0.12,
                "rsi_14": 72.0,
            },
        ]
    )


class EvidenceTests(unittest.TestCase):
    def test_build_evidence_bundle_commits_observed_features_and_sources(self):
        bundle = build_evidence_bundle(
            evidence_records(),
            feature_columns=["score", "rsi_14"],
        )
        duplicate = build_evidence_bundle(
            evidence_records(),
            feature_columns=["score", "rsi_14"],
        )

        self.assertEqual(2, len(bundle.evidence))
        self.assertEqual(bundle.evidence_hash, duplicate.evidence_hash)
        self.assertEqual(0.42, bundle.evidence[0]["observed_features"]["score"])
        self.assertEqual("unit_test", bundle.evidence[0]["sources"]["source"])

    def test_missing_source_is_warning_not_blocking(self):
        records = evidence_records().drop(columns=["source"])
        bundle = build_evidence_bundle(records, feature_columns=["score"])

        result = evaluate_quality_gate(bundle)

        self.assertEqual(ANALYSIS_SAFE, result.gate_status)
        self.assertIn("MISSING_SOURCE", {issue.code for issue in result.issues})

    def test_future_outcome_feature_blocks_quality_gate(self):
        records = evidence_records()
        records["future_return"] = [0.1, -0.2]
        bundle = build_evidence_bundle(records, feature_columns=["score", "future_return"])

        result = evaluate_quality_gate(bundle)

        self.assertEqual(ANALYSIS_UNSAFE, result.gate_status)
        self.assertIn("FUTURE_OUTCOME_FEATURE", {issue.code for issue in result.issues})

    def test_external_blocking_quality_report_blocks_gate(self):
        bundle = build_evidence_bundle(evidence_records(), feature_columns=["score"])
        report = QualityReport(
            (
                QualityIssue(
                    severity=BLOCKING,
                    code="FUTURE_INFORMATION_LEAKAGE",
                    message="test leakage",
                ),
            )
        )

        result = evaluate_quality_gate(bundle, quality_reports=(report,))

        self.assertEqual(ANALYSIS_UNSAFE, result.gate_status)
        self.assertIn("FUTURE_INFORMATION_LEAKAGE", {issue.code for issue in result.issues})

    def test_small_evidence_set_is_warning(self):
        bundle = build_evidence_bundle(evidence_records().head(1), feature_columns=["score"])

        result = evaluate_quality_gate(bundle, minimum_evidence_count=2)

        self.assertEqual(ANALYSIS_SAFE, result.gate_status)
        self.assertIn("SMALL_EVIDENCE_SET", {issue.code for issue in result.issues})

    def test_quality_gate_dict_and_report_writer(self):
        bundle = build_evidence_bundle(evidence_records(), feature_columns=["score"])
        result = evaluate_quality_gate(bundle)

        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_evidence_report(result, Path(tmpdir) / "evidence.md")

            payload = quality_gate_to_dict(result)
            text = output.read_text(encoding="utf-8")
            self.assertEqual(ANALYSIS_SAFE, payload["gate_status"])
            self.assertIn("# Evidence Bundle And Quality Gate", text)

    def test_harness_applies_quality_gate_only_in_risk_gate_state(self):
        bundle = build_evidence_bundle(evidence_records(), feature_columns=["score"])
        result = evaluate_quality_gate(bundle)
        harness = AnalysisHarness()

        blocked = harness.apply_quality_gate(result)
        while harness.current_state() != "risk_gate":
            harness.advance()
        accepted = harness.apply_quality_gate(result)

        self.assertEqual("error", blocked.status)
        self.assertEqual("ok", accepted.status)
        self.assertEqual(ANALYSIS_SAFE, harness.gate_status)

    def test_unsafe_quality_gate_sets_analysis_unsafe_label(self):
        records = evidence_records()
        records["future_return"] = [0.1, -0.2]
        bundle = build_evidence_bundle(records, feature_columns=["future_return"])
        result = evaluate_quality_gate(bundle)
        harness = AnalysisHarness(state="risk_gate")

        accepted = harness.apply_quality_gate(result)

        self.assertEqual("ok", accepted.status)
        self.assertEqual(ANALYSIS_UNSAFE, harness.gate_status)
        self.assertEqual("ANALYSIS_UNSAFE", harness.output_label)


if __name__ == "__main__":
    unittest.main()
