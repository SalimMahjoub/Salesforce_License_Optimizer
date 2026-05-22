"""PDF report generator (WeasyPrint + Jinja2).

Consumes an ``AnalysisResult`` + an ``ActionPlan`` and produces a CFO-friendly
PDF. Returns the rendered bytes so the caller decides whether to stream,
persist or attach.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from decimal import Decimal

from app.models.recommendation import ActionPlan
from app.models.user import UserCategory
from app.services.analysis_service import AnalysisResult
from app.utils.time import utcnow

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class PDFService:
    """Renders the CFO PDF report from an analysis result."""

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render(
        self,
        result: AnalysisResult,
        plan: ActionPlan,
        organization_name: str = "Organization",
    ) -> bytes:
        """Render the report and return the PDF bytes."""
        # WeasyPrint imports are expensive — load lazily so the rest of the
        # service is importable in environments without the native libs.
        try:
            from weasyprint import HTML  # type: ignore
        except OSError as exc:  # pragma: no cover — missing libcairo etc.
            raise RuntimeError(
                "WeasyPrint native dependencies are missing on this host. "
                "Install libcairo / libpango / libgdk-pixbuf (see backend/Dockerfile)."
            ) from exc

        context = self._build_context(result, plan, organization_name)
        template = self.env.get_template("full_report.html")
        html = template.render(**context)
        return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()

    def render_to_file(
        self,
        result: AnalysisResult,
        plan: ActionPlan,
        output_path: Path,
        organization_name: str = "Organization",
    ) -> Path:
        pdf_bytes = self.render(result, plan, organization_name)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(pdf_bytes)
        logger.info("PDF report written: %s (%d bytes)", output_path, len(pdf_bytes))
        return output_path

    # ------------------------------------------------------------------ context
    def _build_context(
        self,
        result: AnalysisResult,
        plan: ActionPlan,
        organization_name: str,
    ) -> dict:
        recs = [r for recs in result.recommendations_by_user.values() for r in recs]
        recs.sort(key=lambda r: (r.priority.value, -float(r.monthly_savings)))

        monthly = sum((r.monthly_savings for r in recs), Decimal("0"))
        annual = monthly * 12

        categories = {c.name: 0 for c in UserCategory}
        for u in result.classified:
            categories[u.category.name] += 1

        return {
            "title": "Rapport d'Optimisation Salesforce",
            "organization_name": organization_name,
            "generated_date": utcnow().strftime("%d/%m/%Y"),
            "executive_summary": (
                f"Analyse de {len(result.classified)} utilisateurs. "
                f"{len(recs)} recommandations identifiées pour un potentiel "
                f"d'économies de {monthly:.0f}€/mois ({annual:.0f}€/an)."
            ),
            "total_users": len(result.classified),
            "inactive_users": categories.get("INACTIVE", 0),
            "monthly_savings": float(monthly),
            "annual_savings": float(annual),
            "recommendations": [_rec_dict(r) for r in recs],
            "categories": categories,
            "action_plan": _plan_dict(plan),
        }


def _rec_dict(rec) -> dict:
    return {
        "priority": rec.priority.value,
        "type": rec.type.value,
        "username": rec.username,
        "license_type": rec.license_type,
        "title": rec.title,
        "description": rec.description,
        "rationale": list(rec.rationale),
        "monthly_savings": float(rec.monthly_savings),
        "annual_savings": float(rec.annual_savings),
        "implementation_complexity": rec.implementation_complexity,
        "implementation_time_days": rec.implementation_time_days,
        "risk_level": rec.risk_level,
    }


def _plan_dict(plan: ActionPlan) -> dict:
    return {
        "title": plan.title,
        "executive_summary": plan.executive_summary,
        "steps": [
            {
                "title": s.title,
                "description": s.description,
                "duration_days": s.duration_days,
                "resources": list(s.resources),
                "success_criteria": list(s.success_criteria),
            }
            for s in plan.steps
        ],
        "quick_wins": list(plan.quick_wins),
        "risks": [{"risk": r.risk, "mitigation": r.mitigation} for r in plan.risks],
        "timeline": plan.timeline,
    }


pdf_service = PDFService()
