import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.llm_agent import (
    AgentExplanation,
    ALLOWED_EVIDENCE_LINKS,
    GoogleGenAIClient,
    LLMConfig,
    OfflineLLMClient,
    load_llm_config_from_env,
    make_llm_client,
    parse_json_response,
    run_llm_agent_harness,
    validate_agent_explanation,
)


class BadLLMClient:
    provider = "bad_test_client"
    model = "bad-model"

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        return {
            "label": "BUY",
            "summary": "unsupported label",
            "methodology": "bad",
            "evidence_links": [],
            "quality_gate_interpretation": "bad",
            "limitations": [],
            "risk_notes": [],
            "next_steps": [],
            "not_investment_advice": True,
        }


class PromptCaptureClient:
    provider = "capture"
    model = "capture-model"

    def __init__(self):
        self.system_prompt = ""
        self.user_prompt = ""

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return OfflineLLMClient().complete_json(system_prompt, user_prompt)


class LLMAgentTests(unittest.TestCase):
    def test_parse_json_response_accepts_fenced_json(self):
        parsed = parse_json_response('```json\n{"label": "WATCH"}\n```')

        self.assertEqual({"label": "WATCH"}, parsed)

    def test_validate_agent_explanation_rejects_unsafe_contract(self):
        with self.assertRaisesRegex(ValueError, "unsupported educational label"):
            validate_agent_explanation(
                {
                    "label": "BUY",
                    "summary": "bad",
                    "not_investment_advice": True,
                }
            )
        with self.assertRaisesRegex(ValueError, "not_investment_advice"):
            validate_agent_explanation(
                {
                    "label": "WATCH",
                    "summary": "bad",
                    "methodology": "bad",
                    "evidence_links": list(ALLOWED_EVIDENCE_LINKS),
                    "quality_gate_interpretation": "bad",
                    "limitations": [],
                    "risk_notes": [],
                    "next_steps": [],
                    "not_investment_advice": False,
                }
            )
        with self.assertRaisesRegex(ValueError, "unsupported evidence links"):
            validate_agent_explanation(
                {
                    "label": "WATCH",
                    "summary": "bad",
                    "methodology": "bad",
                    "evidence_links": ["research_reports"],
                    "quality_gate_interpretation": "bad",
                    "limitations": [],
                    "risk_notes": [],
                    "next_steps": [],
                    "not_investment_advice": True,
                }
            )

    def test_offline_llm_harness_writes_replayable_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = run_llm_agent_harness(
                reports_dir=tmp / "reports",
                decision_log_dir=tmp / "decision_logs",
                client=OfflineLLMClient(),
                report_path=tmp / "llm.md",
                json_path=tmp / "llm.json",
            )

            self.assertEqual("offline_llm_replay_ok", result.status)
            self.assertEqual("ok", result.replay.status)
            self.assertEqual("INVESTIGATE", result.explanation.label)
            self.assertIn("reports/pdf_requirement_coverage.md", result.explanation.evidence_links)
            self.assertTrue(result.explanation.methodology)
            self.assertTrue(result.explanation.quality_gate_interpretation)
            self.assertTrue(result.explanation.next_steps)
            self.assertTrue((tmp / "decision_logs" / "llm_agent" / "decisions.jsonl").exists())
            payload = json.loads((tmp / "llm.json").read_text(encoding="utf-8"))
            self.assertEqual("offline", payload["provider"])
            self.assertIn("methodology", payload["explanation"])
            self.assertIn("quality_gate_interpretation", payload["explanation"])
            self.assertIn("next_steps", payload["explanation"])

    def test_bad_llm_output_falls_back_to_safe_offline_explanation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = run_llm_agent_harness(
                reports_dir=tmp / "reports",
                decision_log_dir=tmp / "decision_logs",
                client=BadLLMClient(),
                report_path=tmp / "llm.md",
                json_path=tmp / "llm.json",
            )

            self.assertEqual("live_llm_replay_ok", result.status)
            self.assertEqual("INVESTIGATE", result.explanation.label)
            self.assertGreaterEqual(len(result.warnings), 1)

    def test_prompt_blocks_llm_calculation_and_requires_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            client = PromptCaptureClient()
            result = run_llm_agent_harness(
                reports_dir=tmp / "reports",
                decision_log_dir=tmp / "decision_logs",
                client=client,
                report_path=tmp / "llm.md",
                json_path=tmp / "llm.json",
            )

            self.assertIsInstance(result.explanation, AgentExplanation)
            self.assertIn("Do not invent, calculate", client.system_prompt)
            self.assertIn("Return only JSON", client.system_prompt)
            self.assertIn("methodology", client.system_prompt)
            self.assertIn("quality_gate_interpretation", client.system_prompt)
            self.assertIn("no_new_numbers", client.user_prompt)
            self.assertIn("evidence_links_must_be_repo_paths", client.user_prompt)
            self.assertIn("reports/pdf_requirement_coverage.md", client.user_prompt)

    def test_auto_provider_uses_google_when_gemini_key_exists(self):
        clean_env = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "LLM_PROVIDER",
                "LLM_API_KEY",
                "OPENAI_API_KEY",
                "GEMINI_API_KEY",
                "GOOGLE_API_KEY",
                "LLM_MODEL",
                "GEMINI_MODEL",
            }
        }

        with patch.dict(os.environ, clean_env, clear=True):
            os.environ["GEMINI_API_KEY"] = "unit-test-key"
            config = load_llm_config_from_env("auto")
            client = make_llm_client(config)

        self.assertEqual("google", config.provider)
        self.assertEqual("gemini-3.8-flash", config.model)
        self.assertIsInstance(client, GoogleGenAIClient)

    def test_google_provider_accepts_explicit_model_override(self):
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "unit-test-key", "GEMINI_MODEL": "gemini-test-model"},
            clear=True,
        ):
            config = load_llm_config_from_env("google")

        self.assertEqual(
            LLMConfig(
                provider="google",
                model="gemini-test-model",
                api_key="unit-test-key",
                api_base="google-genai-sdk",
                timeout_seconds=45,
            ),
            config,
        )


if __name__ == "__main__":
    unittest.main()
