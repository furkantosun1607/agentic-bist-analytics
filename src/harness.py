"""Stateful analysis harness with enforced tool order."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from src.mcp_server import ToolResponse, call_tool


HARNESS_STATES = (
    "select_universe",
    "load_validate",
    "run_analyses",
    "add_context",
    "build_evidence",
    "compare_variants",
    "backtest",
    "risk_gate",
    "explain",
    "human_review",
    "save_decision",
)
PERMITTED_TOOLS_BY_STATE: dict[str, tuple[str, ...]] = {
    "select_universe": (),
    "load_validate": ("market_history", "data_quality"),
    "run_analyses": (
        "indicators_events",
        "sector_ranking",
        "weekday_test",
        "point_in_time_fundamentals",
    ),
    "add_context": ("context",),
    "build_evidence": ("evidence_bundle", "data_quality"),
    "compare_variants": ("data_quality",),
    "backtest": ("backtest",),
    "risk_gate": ("backtest", "data_quality"),
    "explain": (),
    "human_review": (),
    "save_decision": (),
}
EDUCATIONAL_OUTPUT_LABELS = (
    "WATCH",
    "INVESTIGATE",
    "POTENTIAL_CATCH_UP_CANDIDATE",
    "REJECT_SIGNAL",
    "ANALYSIS_UNSAFE",
)


@dataclass(frozen=True)
class HarnessEvent:
    state: str
    event_type: str
    message: str
    tool_name: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class HarnessStepResult:
    status: str
    state: str
    message: str
    response: ToolResponse | None = None
    errors: tuple[str, ...] = ()


@dataclass
class AnalysisHarness:
    """Small state machine that enforces the research workflow."""

    state: str = HARNESS_STATES[0]
    output_label: str | None = None
    review_status: str | None = None
    saved: bool = False
    events: list[HarnessEvent] = field(default_factory=list)

    def current_state(self) -> str:
        return self.state

    def permitted_tools(self) -> tuple[str, ...]:
        return PERMITTED_TOOLS_BY_STATE[self.state]

    def call_tool(self, tool_name: str, args: dict[str, object] | None = None) -> HarnessStepResult:
        if tool_name not in self.permitted_tools():
            message = f"tool {tool_name} is not permitted in state {self.state}"
            self._record("tool_blocked", message, tool_name=tool_name, status="error")
            return HarnessStepResult(
                status="error",
                state=self.state,
                message=message,
                errors=(message,),
            )

        response = call_tool(tool_name, args or {})
        status = "ok" if response.status != "error" else "error"
        message = f"tool {tool_name} returned {response.status}"
        self._record("tool_called", message, tool_name=tool_name, status=response.status)
        return HarnessStepResult(
            status=status,
            state=self.state,
            message=message,
            response=response,
            errors=response.errors,
        )

    def advance(self, expected_state: str | None = None) -> HarnessStepResult:
        if expected_state is not None and expected_state != self.state:
            message = f"cannot complete {expected_state}; current state is {self.state}"
            self._record("advance_blocked", message, status="error")
            return HarnessStepResult(
                status="error",
                state=self.state,
                message=message,
                errors=(message,),
            )

        if self.state == HARNESS_STATES[-1]:
            message = "already at terminal state"
            self._record("advance_blocked", message, status="warning")
            return HarnessStepResult(
                status="warning",
                state=self.state,
                message=message,
                errors=(message,),
            )

        previous = self.state
        self.state = HARNESS_STATES[HARNESS_STATES.index(self.state) + 1]
        message = f"advanced from {previous} to {self.state}"
        self._record("advanced", message, status="ok")
        return HarnessStepResult(status="ok", state=self.state, message=message)

    def set_output_label(self, label: str) -> HarnessStepResult:
        normalized = label.upper()
        if self.state != "explain":
            message = f"output label can only be set in explain state, not {self.state}"
            self._record("label_blocked", message, status="error")
            return HarnessStepResult(
                status="error",
                state=self.state,
                message=message,
                errors=(message,),
            )
        if normalized not in EDUCATIONAL_OUTPUT_LABELS:
            message = f"unsupported output label: {label}"
            self._record("label_blocked", message, status="error")
            return HarnessStepResult(
                status="error",
                state=self.state,
                message=message,
                errors=(message,),
            )

        self.output_label = normalized
        message = f"output label set to {normalized}"
        self._record("label_set", message, status="ok")
        return HarnessStepResult(status="ok", state=self.state, message=message)

    def record_human_review(self, review_status: str) -> HarnessStepResult:
        normalized = review_status.lower()
        if self.state != "human_review":
            message = f"human review can only be recorded in human_review state, not {self.state}"
            self._record("review_blocked", message, status="error")
            return HarnessStepResult(
                status="error",
                state=self.state,
                message=message,
                errors=(message,),
            )
        if normalized not in ("accept", "modify", "reject"):
            message = f"review_status must be accept, modify, or reject: {review_status}"
            self._record("review_blocked", message, status="error")
            return HarnessStepResult(
                status="error",
                state=self.state,
                message=message,
                errors=(message,),
            )

        self.review_status = normalized
        message = f"human review recorded as {normalized}"
        self._record("review_recorded", message, status="ok")
        return HarnessStepResult(status="ok", state=self.state, message=message)

    def save_decision(self) -> HarnessStepResult:
        if self.state != "save_decision":
            message = f"decision can only be saved in save_decision state, not {self.state}"
            self._record("save_blocked", message, status="error")
            return HarnessStepResult(
                status="error",
                state=self.state,
                message=message,
                errors=(message,),
            )
        if self.output_label is None:
            message = "decision cannot be saved before an output label is set"
            self._record("save_blocked", message, status="error")
            return HarnessStepResult(
                status="error",
                state=self.state,
                message=message,
                errors=(message,),
            )
        if self.review_status is None:
            message = "decision cannot be saved before human review"
            self._record("save_blocked", message, status="error")
            return HarnessStepResult(
                status="error",
                state=self.state,
                message=message,
                errors=(message,),
            )

        self.saved = True
        message = "decision saved"
        self._record("decision_saved", message, status="ok")
        return HarnessStepResult(status="ok", state=self.state, message=message)

    def snapshot(self) -> dict[str, object]:
        return {
            "state": self.state,
            "output_label": self.output_label,
            "review_status": self.review_status,
            "saved": self.saved,
            "permitted_tools": self.permitted_tools(),
            "events": [asdict(event) for event in self.events],
        }

    def _record(
        self,
        event_type: str,
        message: str,
        tool_name: str | None = None,
        status: str | None = None,
    ) -> None:
        self.events.append(
            HarnessEvent(
                state=self.state,
                event_type=event_type,
                message=message,
                tool_name=tool_name,
                status=status,
            )
        )


def create_harness() -> AnalysisHarness:
    """Create a fresh analysis harness at the first state."""

    return AnalysisHarness()
