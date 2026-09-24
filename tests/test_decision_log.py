import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.decision_log import (
    DecisionLogError,
    append_decision_record,
    create_decision_record,
    load_decision_records,
    replay_decision_record,
    write_decision_log_report,
)
from src.evidence import build_evidence_bundle, evaluate_quality_gate
from src.harness import AnalysisHarness


def reviewed_harness() -> AnalysisHarness:
    harness = AnalysisHarness(state="save_decision")
    harness.output_label = "INVESTIGATE"
    harness.review_status = "accept"
    harness.gate_status = "ANALYSIS_SAFE"
    harness.saved = True
    return harness


def quality_gate():
    records = pd.DataFrame(
        [
            {
                "signal_id": "sig-1",
                "source": "unit_test",
                "known_at": "2024-01-01T18:10:00+03:00",
                "score": 0.42,
            }
        ]
    )
    bundle = build_evidence_bundle(records, feature_columns=["score"])
    return evaluate_quality_gate(bundle)


class DecisionLogTests(unittest.TestCase):
    def test_create_decision_record_requires_reviewed_saved_harness(self):
        with self.assertRaisesRegex(DecisionLogError, "must be saved"):
            create_decision_record(
                decision_id="decision-1",
                harness=AnalysisHarness(state="save_decision", output_label="WATCH", review_status="accept"),
                inputs={"question": "synthetic"},
                tool_outputs={"evidence": {"ok": True}},
                quality_gate=quality_gate(),
                reviewer="tester",
            )

    def test_create_decision_record_captures_replay_fields(self):
        record = create_decision_record(
            decision_id="decision-1",
            harness=reviewed_harness(),
            inputs={"question": "synthetic"},
            tool_outputs={"evidence": {"ok": True}},
            quality_gate=quality_gate(),
            reviewer="tester",
            review_notes="approved for unit test",
            created_at="2024-01-10T12:00:00+00:00",
        )

        self.assertEqual("decision-1", record.decision_id)
        self.assertEqual("INVESTIGATE", record.output_label)
        self.assertEqual("accept", record.review_status)
        self.assertEqual(record.evidence_hash, record.quality_gate["evidence_hash"])
        self.assertEqual(64, len(record.record_hash))

    def test_append_load_and_replay_decision_record(self):
        record = create_decision_record(
            decision_id="decision-1",
            harness=reviewed_harness(),
            inputs={"question": "synthetic"},
            tool_outputs={"evidence": {"ok": True}},
            quality_gate=quality_gate(),
            reviewer="tester",
            created_at="2024-01-10T12:00:00+00:00",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = append_decision_record(record, Path(tmpdir))
            loaded = load_decision_records(log_path)
            replay = replay_decision_record(loaded[0])

            self.assertEqual(1, len(loaded))
            self.assertEqual("ok", replay.status)
            self.assertEqual((), replay.messages)

    def test_replay_detects_tampered_record(self):
        record = create_decision_record(
            decision_id="decision-1",
            harness=reviewed_harness(),
            inputs={"question": "synthetic"},
            tool_outputs={"evidence": {"ok": True}},
            quality_gate=quality_gate(),
            reviewer="tester",
            created_at="2024-01-10T12:00:00+00:00",
        )
        tampered = record.__class__(
            **{
                **record.__dict__,
                "output_label": "WATCH",
            }
        )

        replay = replay_decision_record(tampered)

        self.assertEqual("error", replay.status)
        self.assertIn("record_hash mismatch", replay.messages)

    def test_write_decision_log_report(self):
        record = create_decision_record(
            decision_id="decision-1",
            harness=reviewed_harness(),
            inputs={"question": "synthetic"},
            tool_outputs={"evidence": {"ok": True}},
            quality_gate=quality_gate(),
            reviewer="tester",
            created_at="2024-01-10T12:00:00+00:00",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_decision_log_report([record], Path(tmpdir) / "decision_log.md")

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Human Review And Replayable Decision Log", text)
            self.assertIn("decision-1", text)


if __name__ == "__main__":
    unittest.main()
