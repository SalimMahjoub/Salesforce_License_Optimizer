"""Live E2E pipeline runner against real Salesforce data.

Reads artifacts/sf-{users,logins}-raw.json (pulled via sf CLI), runs the full
pipeline (classification + recommendations + plan + permission monitor), and
writes a presentation-ready JSON + Markdown report to artifacts/.

Usage:
    python scripts/run_live_e2e.py

Pre-reqs:
    cd <repo>/backend
    pip install -r requirements.txt
    # then go back to repo root and run this script
"""
from __future__ import annotations

import asyncio
import io
import json
import os
import sys
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Force UTF-8 stdout on Windows (default cp1252 chokes on €, →, etc.)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Make `app` importable when running from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

# Load .env at repo root if present (gives us the real OPENAI_API_KEY).
# Done manually to avoid a python-dotenv dep just for this script.
_env_file = REPO_ROOT / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Skip the broken comment line in the supplied .env
        if " " in key:
            continue
        os.environ.setdefault(key, value)

# Required env for app.config to load (defaults only if .env didn't set them)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://t:t@l:5432/t")
os.environ.setdefault("SF_CLIENT_ID", "n/a")
os.environ.setdefault("SF_CLIENT_SECRET", "n/a")
os.environ.setdefault("SF_REDIRECT_URI", "http://localhost:8000/cb")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fallback-only")
os.environ.setdefault("SECRET_KEY", "x" * 40)
os.environ.setdefault("ENCRYPTION_KEY", "zmWmS7p6gK1H7N0pXhVz9JmnJ8m4mY3o5p2WJZ6e1nQ=")
os.environ.setdefault("DATA_PROVIDER", "demo")  # bypass salesforce eager import
os.environ.setdefault("OPENAI_MODEL", os.environ.get("LLM_MODEL", "gpt-4o"))

from app.factories.recommendation_factory import RecommendationFactory  # noqa: E402
from app.services.analysis_service import AnalysisService  # noqa: E402
from app.services.classification_service import ClassificationService  # noqa: E402
from app.services.data_providers.sf_cli import SfCliDataProvider  # noqa: E402
from app.services.permission_monitor import PermissionMonitor  # noqa: E402
from app.services.plan_generator import PlanGenerator  # noqa: E402

ORG_ID = "airliquidehhc-emea-devselim"
ORG_NAME = "Air Liquide HHC EMEA — DevSelim Sandbox"
ARTIFACTS = REPO_ROOT / "artifacts"


def _serialize_decimal(o):
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(o)


async def main():
    print(f"=== LIVE E2E against {ORG_ID} ===\n")

    provider = SfCliDataProvider(
        users_path=ARTIFACTS / "sf-users-raw.json",
        logins_path=ARTIFACTS / "sf-logins-raw.json",
    )
    service = AnalysisService(data_provider=provider)
    result = await service.get_or_run(ORG_ID, days=90, force_refresh=True)

    print(f"[1/5] Snapshot")
    print(f"      Users analysed      : {len(result.classified)}")
    print(f"      Login activity (90j): "
          f"{sum(1 for m in result.snapshot.metrics if m.login_count_90d > 0)} users")

    cat_counts = Counter(c.category.value for c in result.classified)
    print(f"\n[2/5] Classification")
    for cat, n in cat_counts.most_common():
        pct = n / len(result.classified) * 100
        print(f"      {cat:>14} : {n:>4}  ({pct:5.1f} %)")

    recs = [r for rs in result.recommendations_by_user.values() for r in rs]
    # Realistic savings: use the analysis service rollup (max savings per user)
    total_monthly = float(result.total_monthly_savings())
    total_annual = total_monthly * 12
    total_cost = float(result.total_monthly_cost())
    savings_rate = (total_monthly / total_cost * 100) if total_cost else 0
    rec_by_type = Counter(r.type.value for r in recs)
    rec_by_priority = Counter(r.priority.value for r in recs)

    print(f"\n[3/5] Recommendations")
    print(f"      Total recommendations  : {len(recs)}")
    print(f"      Current monthly cost   : {total_cost:>12,.0f} €")
    print(f"      Potential monthly save : {total_monthly:>12,.0f} €")
    print(f"      Potential annual save  : {total_annual:>12,.0f} €")
    print(f"      Savings rate           : {savings_rate:>12.1f} %")
    print(f"      By type     : {dict(rec_by_type)}")
    print(f"      By priority : {dict(rec_by_priority)}")

    print(f"\n[4/5] CFO action plan (GPT-4 if key configured, else deterministic fallback)")
    plan = await PlanGenerator().generate(
        recommendations=recs, org_name=ORG_NAME, total_users=len(result.classified),
    )
    print(f"      Title    : {plan.title}")
    print(f"      Model    : {plan.model_version}")
    print(f"      Steps    : {len(plan.steps)}")
    print(f"      Q-wins   : {len(plan.quick_wins)}")
    print(f"      Risks    : {len(plan.risks)}")
    print(f"      Timeline : {plan.timeline}")

    alerts = PermissionMonitor().scan(result)
    sev = Counter(a.severity for a in alerts)
    print(f"\n[5/5] Security alerts")
    print(f"      Total    : {len(alerts)}")
    for s, n in sev.most_common():
        print(f"      {s:>10}: {n}")

    # --- Persist artifacts -------------------------------------------------
    ARTIFACTS.mkdir(exist_ok=True)
    summary = {
        "org_id": ORG_ID,
        "org_name": ORG_NAME,
        "generated_at": datetime.utcnow().isoformat(),
        "total_users_analysed": len(result.classified),
        "distribution": dict(cat_counts),
        "financials": {
            "current_monthly_cost_eur": total_cost,
            "potential_monthly_savings_eur": total_monthly,
            "potential_annual_savings_eur": total_annual,
            "savings_rate_pct": round(savings_rate, 2),
        },
        "recommendations": {
            "total": len(recs),
            "by_type": dict(rec_by_type),
            "by_priority": dict(rec_by_priority),
        },
        "security_alerts": {
            "total": len(alerts),
            "by_severity": dict(sev),
        },
        "plan_preview": {
            "title": plan.title,
            "model": plan.model_version,
            "executive_summary": plan.executive_summary,
            "step_titles": [s.title for s in plan.steps],
            "quick_wins": list(plan.quick_wins),
            "risks": [{"risk": r.risk, "mitigation": r.mitigation} for r in plan.risks],
            "timeline": plan.timeline,
        },
        "top10_savings": [
            {
                "username": r.username,
                "license": r.license_type,
                "type": r.type.value,
                "priority": r.priority.value,
                "monthly_savings_eur": float(r.monthly_savings),
                "title": r.title,
            }
            for r in sorted(recs, key=lambda x: -float(x.monthly_savings))[:10]
        ],
        "top_alerts": [
            {
                "user": a.username,
                "severity": a.severity,
                "rule": a.permission,
                "description": a.description,
            }
            for a in sorted(alerts, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x.severity, 9))[:15]
        ],
    }

    out_json = ARTIFACTS / "live-e2e-report.json"
    out_json.write_text(
        json.dumps(summary, indent=2, default=_serialize_decimal, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n✅ JSON report : {out_json}")
    return summary


if __name__ == "__main__":
    asyncio.run(main())
