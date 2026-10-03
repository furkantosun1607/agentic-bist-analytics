"""Static HTML dashboard for the BIST analytics project."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path

from src.reporting import REPORT_MANIFEST, ReportManifestEntry
from src.settings import PROJECT_ROOT, Settings, load_settings


DEFAULT_DASHBOARD_PATH = PROJECT_ROOT / "ui" / "dashboard.html"
DEFAULT_LLM_JSON_PATH = PROJECT_ROOT / "reports" / "llm_agent_harness.json"


@dataclass(frozen=True)
class DashboardBuildResult:
    status: str
    output_path: Path
    report_count: int
    missing_report_count: int
    llm_status: str


def build_dashboard_from_settings(
    settings: Settings | None = None,
    output_path: str | Path = DEFAULT_DASHBOARD_PATH,
) -> DashboardBuildResult:
    active_settings = settings or load_settings()
    return build_dashboard(
        output_path=output_path,
        reports_dir=active_settings.paths.reports_dir,
    )


def build_dashboard(
    output_path: str | Path = DEFAULT_DASHBOARD_PATH,
    reports_dir: str | Path = PROJECT_ROOT / "reports",
) -> DashboardBuildResult:
    """Build an informative static dashboard from current project artifacts."""

    reports_path = Path(reports_dir)
    path = Path(output_path)
    llm_payload = _load_json(reports_path / "llm_agent_harness.json")
    llm_status = str(llm_payload.get("status", "not_run")) if llm_payload else "not_run"
    initial_missing_reports = [
        entry for entry in REPORT_MANIFEST if not (PROJECT_ROOT / entry.path).exists()
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _render_dashboard(
            report_manifest=REPORT_MANIFEST,
            missing_reports=initial_missing_reports,
            llm_payload=llm_payload,
        ),
        encoding="utf-8",
    )
    missing_reports = [
        entry for entry in REPORT_MANIFEST if not (PROJECT_ROOT / entry.path).exists()
    ]
    if len(missing_reports) != len(initial_missing_reports):
        path.write_text(
            _render_dashboard(
                report_manifest=REPORT_MANIFEST,
                missing_reports=missing_reports,
                llm_payload=llm_payload,
            ),
            encoding="utf-8",
        )
    return DashboardBuildResult(
        status="ready" if not missing_reports else "warning",
        output_path=path,
        report_count=len(REPORT_MANIFEST),
        missing_report_count=len(missing_reports),
        llm_status=llm_status,
    )


def _render_dashboard(
    report_manifest: tuple[ReportManifestEntry, ...],
    missing_reports: list[ReportManifestEntry],
    llm_payload: dict[str, object],
) -> str:
    report_cards = "\n".join(_report_card(entry) for entry in report_manifest)
    missing_text = "All tracked reports are present." if not missing_reports else (
        f"{len(missing_reports)} tracked reports are missing."
    )
    llm_status = str(llm_payload.get("status", "not_run")) if llm_payload else "not_run"
    llm_provider = str(llm_payload.get("provider", "-")) if llm_payload else "-"
    llm_label = "-"
    llm_summary = "Run python -m scripts.run_llm_agent_harness before rebuilding the dashboard."
    if llm_payload:
        explanation = llm_payload.get("explanation", {})
        if isinstance(explanation, dict):
            llm_label = str(explanation.get("label", "-"))
            llm_summary = str(explanation.get("summary", llm_summary))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agentic BIST Analytics Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17202a;
      --muted: #5f6b76;
      --line: #d9e0e7;
      --panel: #ffffff;
      --page: #f4f7f9;
      --accent: #117a65;
      --accent-2: #8e44ad;
      --warn: #b9770e;
      --ok: #1e8449;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: var(--page);
      color: var(--ink);
      letter-spacing: 0;
    }}
    header {{
      padding: 28px clamp(18px, 4vw, 48px);
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{ margin: 0 0 8px; font-size: clamp(28px, 4vw, 44px); }}
    h2 {{ margin: 0 0 14px; font-size: 20px; }}
    p {{ line-height: 1.55; }}
    main {{ padding: 24px clamp(18px, 4vw, 48px) 48px; }}
    .subtitle {{ max-width: 900px; color: var(--muted); margin: 0; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-bottom: 24px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .metric {{ font-size: 30px; font-weight: 750; margin: 8px 0 2px; }}
    .label {{ color: var(--muted); font-size: 13px; }}
    .pill {{
      display: inline-block;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 12px;
      font-weight: 700;
      background: #eaf5f1;
      color: var(--accent);
    }}
    .pill.warn {{ background: #fbf1df; color: var(--warn); }}
    .section {{ margin-top: 24px; }}
    .reports {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }}
    .report h3 {{ margin: 0 0 8px; font-size: 16px; }}
    .report p {{ margin: 6px 0; color: var(--muted); font-size: 13px; }}
    code {{
      background: #edf2f5;
      border: 1px solid var(--line);
      border-radius: 5px;
      padding: 2px 5px;
      white-space: pre-wrap;
    }}
    .commands {{ display: grid; gap: 8px; }}
    .commands code {{ display: block; padding: 10px; }}
  </style>
</head>
<body>
  <header>
    <h1>Agentic BIST Analytics Dashboard</h1>
    <p class="subtitle">Educational research harness status, report inventory, LLM agent output and demo commands. No broker connection, no investment advice.</p>
  </header>
  <main>
    <section class="grid">
      <div class="card">
        <div class="label">Tracked reports</div>
        <div class="metric">{len(report_manifest)}</div>
        <span class="pill">{html.escape(missing_text)}</span>
      </div>
      <div class="card">
        <div class="label">LLM harness status</div>
        <div class="metric">{html.escape(llm_status)}</div>
        <span class="pill">{html.escape(llm_provider)}</span>
      </div>
      <div class="card">
        <div class="label">Agent label</div>
        <div class="metric">{html.escape(llm_label)}</div>
        <span class="pill warn">educational only</span>
      </div>
    </section>

    <section class="card section">
      <h2>LLM Agent Explanation</h2>
      <p>{html.escape(llm_summary)}</p>
    </section>

    <section class="section">
      <h2>Run Commands</h2>
      <div class="commands">
        <code>python -m scripts.run_llm_agent_harness --provider auto</code>
        <code>python -m scripts.build_dashboard</code>
        <code>python -m scripts.demo --offline</code>
        <code>python -m unittest discover -s tests</code>
      </div>
    </section>

    <section class="section">
      <h2>Report Inventory</h2>
      <div class="reports">
        {report_cards}
      </div>
    </section>
  </main>
</body>
</html>
"""


def _report_card(entry: ReportManifestEntry) -> str:
    exists = (PROJECT_ROOT / entry.path).exists()
    status_class = "" if exists else " warn"
    exists_label = entry.status if exists else "missing"
    return f"""<article class="card report">
  <h3>{html.escape(entry.report_name)}</h3>
  <span class="pill{status_class}">{html.escape(exists_label)}</span>
  <p><strong>Path:</strong> <code>{html.escape(entry.path)}</code></p>
  <p><strong>Sample:</strong> {html.escape(entry.sample_size)}</p>
  <p><strong>Limitation:</strong> {html.escape(entry.limitations)}</p>
</article>"""


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
