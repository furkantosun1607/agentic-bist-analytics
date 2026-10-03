"""Optional live LLM agent harness integration.

The LLM is allowed to explain and organize deterministic tool outputs.
It is not allowed to calculate prices, returns or financial ratios.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from src.decision_log import (
    DecisionRecord,
    ReplayResult,
    create_decision_record,
    load_decision_records,
    replay_decision_record,
    write_decision_records,
)
from src.decision_log_reports import build_decision_evidence_records
from src.evidence import (
    QualityGateResult,
    build_evidence_bundle,
    evaluate_quality_gate,
    quality_gate_to_dict,
)
from src.harness import AnalysisHarness, EDUCATIONAL_OUTPUT_LABELS
from src.settings import PROJECT_ROOT, Settings, load_settings


DEFAULT_CREATED_AT = "2026-10-03T12:00:00+03:00"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "llm_agent_harness.md"
DEFAULT_JSON_PATH = PROJECT_ROOT / "reports" / "llm_agent_harness.json"
ALLOWED_EVIDENCE_LINKS = (
    "reports/research_run_status.md",
    "reports/backtest.md",
    "reports/strategy_variants.md",
    "reports/harness_variants.md",
    "reports/pdf_requirement_coverage.md",
)


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    api_key: str | None
    api_base: str
    timeout_seconds: int


@dataclass(frozen=True)
class AgentExplanation:
    label: str
    summary: str
    methodology: str
    evidence_links: tuple[str, ...]
    quality_gate_interpretation: str
    limitations: tuple[str, ...]
    risk_notes: tuple[str, ...]
    next_steps: tuple[str, ...]
    not_investment_advice: bool


@dataclass(frozen=True)
class LLMHarnessRunResult:
    status: str
    provider: str
    model: str
    explanation: AgentExplanation
    quality_gate: QualityGateResult
    decision_record: DecisionRecord
    replay: ReplayResult
    report_path: Path
    json_path: Path
    warnings: tuple[str, ...]


class LLMClient(Protocol):
    provider: str
    model: str

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        """Return parsed JSON from a constrained LLM response."""


class OfflineLLMClient:
    """Deterministic fallback client for no-key classroom demos."""

    provider = "offline"
    model = "deterministic-fallback"

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        return {
            "label": "INVESTIGATE",
            "summary": (
                "The project is ready to demonstrate a controlled educational BIST "
                "analytics workflow. Deterministic Python reports provide the measured "
                "scenario, backtest, strategy-variant and harness evidence; the LLM "
                "explains that evidence without recalculating financial metrics."
            ),
            "methodology": (
                "The harness reads committed report evidence, applies the quality gate, "
                "asks the LLM for a constrained explanation, records human review, and "
                "writes a replayable decision log."
            ),
            "evidence_links": list(ALLOWED_EVIDENCE_LINKS),
            "quality_gate_interpretation": (
                "ANALYSIS_SAFE means the committed project evidence passed the current "
                "evidence completeness and leakage-oriented checks for this educational "
                "artifact."
            ),
            "limitations": [
                "The fallback client is deterministic and does not benchmark live prose quality.",
                "Strategy variants D and E are unavailable until executable macro/news signals exist.",
                "RSS news is context metadata, not a standalone trading signal.",
            ],
            "risk_notes": [
                "No broker action is generated.",
                "Numerical claims must remain tied to deterministic report artifacts.",
            ],
            "next_steps": [
                "Open reports/pdf_requirement_coverage.md for PDF alignment.",
                "Open ui/dashboard.html for a classroom status overview.",
                "Run the live Gemini provider when a fresh LLM explanation is required.",
            ],
            "not_investment_advice": True,
        }


class OpenAICompatibleChatClient:
    """Small stdlib client for OpenAI-compatible chat-completions endpoints."""

    provider = "openai_compatible"

    def __init__(self, config: LLMConfig):
        self.config = config
        self.model = config.model

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        if not self.config.api_key:
            raise RuntimeError("LLM_API_KEY or OPENAI_API_KEY is required for live LLM calls")

        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            self.config.api_base,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"live LLM HTTP error {exc.code}: {detail}") from exc
        except Exception as exc:
            raise RuntimeError(f"live LLM request failed: {exc}") from exc

        try:
            content = payload["choices"][0]["message"]["content"]
        except Exception as exc:
            raise RuntimeError("live LLM response missing choices[0].message.content") from exc
        return parse_json_response(str(content))


class GoogleGenAIClient:
    """Google Gen AI SDK client for Gemini models."""

    provider = "google"

    def __init__(self, config: LLMConfig):
        self.config = config
        self.model = config.model

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        if not self.config.api_key:
            raise RuntimeError("GEMINI_API_KEY, GOOGLE_API_KEY or LLM_API_KEY is required")

        try:
            from google import genai
        except Exception as exc:
            raise RuntimeError(
                "google-genai is required for Google Gemini calls; run pip install -r requirements.txt"
            ) from exc

        client = genai.Client(api_key=self.config.api_key)
        prompt = (
            f"{system_prompt}\n\n"
            "Return valid JSON only. Do not wrap it in markdown fences.\n\n"
            f"{user_prompt}"
        )
        try:
            response = client.models.generate_content(
                model=self.config.model,
                contents=prompt,
            )
        except Exception as exc:
            raise RuntimeError(f"Google Gemini request failed: {exc}") from exc

        text = getattr(response, "text", None)
        if text is None:
            raise RuntimeError("Google Gemini response missing text")
        return parse_json_response(str(text))


def load_llm_config_from_env(provider: str = "auto") -> LLMConfig:
    """Load LLM config from environment variables without requiring secrets."""

    env_provider = provider if provider != "auto" else os.getenv("LLM_PROVIDER", "auto")
    resolved_provider = env_provider.lower()
    if resolved_provider == "auto":
        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
            resolved_provider = "google"
        elif os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"):
            resolved_provider = "openai"
        else:
            resolved_provider = "offline"

    if resolved_provider in {"google", "gemini"}:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
        model = os.getenv("GEMINI_MODEL") or os.getenv("LLM_MODEL") or "gemini-3.8-flash"
        api_base = os.getenv("LLM_API_BASE") or "google-genai-sdk"
    else:
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
        api_base = os.getenv("LLM_API_BASE") or "https://api.openai.com/v1/chat/completions"

    return LLMConfig(
        provider=resolved_provider,
        model=model,
        api_key=api_key,
        api_base=api_base,
        timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "45")),
    )


def make_llm_client(config: LLMConfig) -> LLMClient:
    """Create the configured client."""

    if config.provider in {"offline", "mock", "deterministic"}:
        return OfflineLLMClient()
    if config.provider in {"openai", "openai_compatible"}:
        return OpenAICompatibleChatClient(config)
    if config.provider in {"google", "gemini"}:
        return GoogleGenAIClient(config)
    raise ValueError(f"unsupported LLM_PROVIDER: {config.provider}")


def run_llm_agent_harness_from_settings(
    settings: Settings | None = None,
    provider: str = "auto",
    review_status: str = "accept",
) -> LLMHarnessRunResult:
    active_settings = settings or load_settings()
    config = load_llm_config_from_env(provider)
    client = make_llm_client(config)
    return run_llm_agent_harness(
        reports_dir=active_settings.paths.reports_dir,
        decision_log_dir=active_settings.outputs.decision_log_dir,
        client=client,
        review_status=review_status,
    )


def run_llm_agent_harness(
    reports_dir: str | Path,
    decision_log_dir: str | Path,
    client: LLMClient,
    review_status: str = "accept",
    report_path: str | Path = DEFAULT_REPORT_PATH,
    json_path: str | Path = DEFAULT_JSON_PATH,
) -> LLMHarnessRunResult:
    """Run the stateful harness and let the LLM explain committed evidence."""

    reports_path = Path(reports_dir)
    warnings: list[str] = []
    evidence_records = build_decision_evidence_records(reports_path)
    evidence_bundle = build_evidence_bundle(
        evidence_records,
        feature_columns=[
            "scenario_report_count",
            "backtest_trade_count",
            "strategy_variant_measured_count",
            "harness_question_count",
        ],
        source_columns=["source", "source_url", "known_at"],
    )
    quality_gate = evaluate_quality_gate(evidence_bundle)
    harness = _advance_to_explain(quality_gate)

    try:
        raw = client.complete_json(
            _system_prompt(),
            _user_prompt(evidence_bundle.evidence, quality_gate),
        )
        explanation = validate_agent_explanation(raw)
    except Exception as exc:
        warnings.append(str(exc))
        explanation = validate_agent_explanation(OfflineLLMClient().complete_json("", ""))

    harness.set_output_label(explanation.label)
    harness.advance("explain")
    harness.record_human_review(review_status)
    harness.advance("human_review")
    harness.save_decision()

    record = create_decision_record(
        decision_id="p41-llm-agent-harness",
        harness=harness,
        inputs={
            "analysis_question": "Can the live LLM agent harness explain deterministic BIST project evidence?",
            "decision_scope": "educational_project_artifact",
            "llm_provider": client.provider,
            "llm_model": client.model,
            "not_investment_advice": True,
        },
        tool_outputs={
            "llm_explanation": asdict(explanation),
            "quality_gate": quality_gate_to_dict(quality_gate),
        },
        quality_gate=quality_gate,
        reviewer="project-owner",
        review_notes="LLM explanation reviewed as educational harness output only.",
        created_at=DEFAULT_CREATED_AT,
    )
    llm_log_dir = Path(decision_log_dir) / "llm_agent"
    log_path = write_decision_records([record], llm_log_dir)
    loaded = load_decision_records(log_path)
    replay = replay_decision_record(loaded[0])

    status = "live_llm_replay_ok" if client.provider != "offline" else "offline_llm_replay_ok"
    if replay.status != "ok":
        status = "llm_replay_error"
    result = LLMHarnessRunResult(
        status=status,
        provider=client.provider,
        model=client.model,
        explanation=explanation,
        quality_gate=quality_gate,
        decision_record=record,
        replay=replay,
        report_path=Path(report_path),
        json_path=Path(json_path),
        warnings=tuple(warnings),
    )
    write_llm_harness_outputs(result, log_path)
    return result


def parse_json_response(content: str) -> dict[str, object]:
    """Parse direct or fenced JSON from an LLM response."""

    text = content.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        if match:
            text = match.group(1)
    return json.loads(text)


def validate_agent_explanation(raw: dict[str, object]) -> AgentExplanation:
    """Validate the LLM explanation contract and block unsafe labels."""

    label = str(raw.get("label", "")).upper()
    if label not in EDUCATIONAL_OUTPUT_LABELS:
        raise ValueError(f"LLM returned unsupported educational label: {label}")

    summary = str(raw.get("summary", "")).strip()
    if not summary:
        raise ValueError("LLM explanation summary is empty")
    not_advice = bool(raw.get("not_investment_advice"))
    if not not_advice:
        raise ValueError("LLM explanation must mark not_investment_advice=true")

    evidence_links = _string_tuple(raw.get("evidence_links"))
    invalid_links = [link for link in evidence_links if link not in ALLOWED_EVIDENCE_LINKS]
    if not evidence_links:
        raise ValueError("LLM explanation evidence_links is empty")
    if invalid_links:
        raise ValueError(f"LLM explanation contains unsupported evidence links: {', '.join(invalid_links)}")

    return AgentExplanation(
        label=label,
        summary=summary,
        methodology=_required_text(raw, "methodology"),
        evidence_links=evidence_links,
        quality_gate_interpretation=_required_text(raw, "quality_gate_interpretation"),
        limitations=_string_tuple(raw.get("limitations")),
        risk_notes=_string_tuple(raw.get("risk_notes")),
        next_steps=_string_tuple(raw.get("next_steps")),
        not_investment_advice=not_advice,
    )


def write_llm_harness_outputs(result: LLMHarnessRunResult, log_path: Path) -> None:
    """Write JSON and markdown artifacts for the LLM harness run."""

    result.json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": result.status,
        "provider": result.provider,
        "model": result.model,
        "quality_gate": quality_gate_to_dict(result.quality_gate),
        "explanation": asdict(result.explanation),
        "decision_id": result.decision_record.decision_id,
        "replay_status": result.replay.status,
        "warnings": list(result.warnings),
    }
    result.json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    result.report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# LLM Agent Harness Run",
        "",
        f"Status: `{result.status}`.",
        f"Provider: `{result.provider}`.",
        f"Model: `{result.model}`.",
        f"Decision log: `{_display_path(log_path)}`.",
        f"Replay status: `{result.replay.status}`.",
        f"Quality gate: `{result.quality_gate.gate_status}`.",
        "",
        "## Agent Explanation",
        "",
        f"Label: `{result.explanation.label}`.",
        "",
        result.explanation.summary,
        "",
        "## Methodology",
        "",
        result.explanation.methodology,
        "",
        "## Quality Gate Interpretation",
        "",
        result.explanation.quality_gate_interpretation,
        "",
        "## Evidence Links",
        "",
    ]
    lines.extend(f"- `{link}`" for link in result.explanation.evidence_links)
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in result.explanation.limitations)
    lines.extend(["", "## Risk Notes", ""])
    lines.extend(f"- {item}" for item in result.explanation.risk_notes)
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in result.explanation.next_steps)
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(
        [
            "",
            "Educational-use notice: this harness does not provide investment advice, "
            "does not place orders, and does not allow the LLM to calculate financial metrics.",
            "",
        ]
    )
    result.report_path.write_text("\n".join(lines), encoding="utf-8")


def _advance_to_explain(quality_gate: QualityGateResult) -> AnalysisHarness:
    harness = AnalysisHarness()
    while harness.current_state() != "risk_gate":
        harness.advance()
    harness.apply_quality_gate(quality_gate)
    harness.advance("risk_gate")
    return harness


def _system_prompt() -> str:
    return (
        "You are the explanation layer inside an educational BIST analytics harness. "
        "Python tools already calculated every number. Do not invent, calculate or "
        "recommend trades. Return only JSON with keys: label, summary, methodology, "
        "evidence_links, quality_gate_interpretation, limitations, risk_notes, "
        "next_steps, not_investment_advice. Evidence links must be existing project "
        "report paths from the user payload, not invented aliases. The label must be "
        f"one of {', '.join(EDUCATIONAL_OUTPUT_LABELS)}."
    )


def _user_prompt(evidence: tuple[dict[str, object], ...], quality_gate: QualityGateResult) -> str:
    payload = {
        "committed_evidence": list(evidence),
        "quality_gate": quality_gate_to_dict(quality_gate),
        "required_policy": {
            "no_investment_advice": True,
            "no_new_numbers": True,
            "must_reference_evidence": True,
            "evidence_links_must_be_repo_paths": True,
        },
        "required_json_schema": {
            "label": "one educational label",
            "summary": "plain-language project conclusion",
            "methodology": "how the harness used deterministic reports, quality gate, LLM explanation, human review and replay",
            "evidence_links": list(ALLOWED_EVIDENCE_LINKS),
            "quality_gate_interpretation": "explain gate_status without adding new facts",
            "limitations": "list of explicit project limitations",
            "risk_notes": "list of educational risk notes",
            "next_steps": "list of classroom/demo follow-up actions",
            "not_investment_advice": True,
        },
    }
    return json.dumps(payload, ensure_ascii=True, sort_keys=True)


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value if str(item).strip())
    raise ValueError("expected a string or list of strings")


def _required_text(raw: dict[str, object], key: str) -> str:
    value = str(raw.get(key, "")).strip()
    if not value:
        raise ValueError(f"LLM explanation {key} is empty")
    return value


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
