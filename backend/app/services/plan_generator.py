"""CFO-facing action plan generator (GPT-4 backed).

Adds Redis caching and a per-tenant daily budget guard on top of the raw
GPT-4 client. Falls back to a deterministic plan when:
- OPENAI_API_KEY is unset,
- the GPT call fails, or
- the daily token budget is exhausted.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

import hashlib

from app.clients.gpt4_client import GPT4Client, gpt4_client
from app.config import get_settings
from app.models.recommendation import (
    ActionPlan,
    PlanRisk,
    PlanStep,
    Priority,
    Recommendation,
)
from app.services.cache import get_cache
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Tu es un expert en optimisation des licences SaaS et en transformation digitale.
Ta mission : transformer une liste de recommandations techniques en plan d'action
exécutable pour un CFO non technique.

Principes :
- Sois précis et actionnable
- Quantifie les bénéfices et les risques
- Priorise par impact financier
- Reste professionnel et concis
- Réponds uniquement avec du JSON valide (pas de markdown wrappers)"""


class PlanGenerator:
    """Orchestrates GPT-4 calls + safety nets to produce an ActionPlan."""

    # Conservative daily token cap per process instance.
    # In production this should be per-tenant in Redis; kept simple for now.
    DEFAULT_DAILY_TOKEN_BUDGET = 200_000

    def __init__(
        self,
        gpt4: Optional[GPT4Client] = None,
        daily_token_budget: int = DEFAULT_DAILY_TOKEN_BUDGET,
    ):
        self.gpt4 = gpt4 or gpt4_client
        self.daily_token_budget = daily_token_budget
        self._budget_window_start = utcnow()
        self._tokens_spent_today = 0

    async def generate(
        self,
        recommendations: List[Recommendation],
        org_name: str = "Organization",
        total_users: int = 0,
    ) -> ActionPlan:
        """Return an ActionPlan, always — never raises to the caller."""
        settings = get_settings()
        total_savings = _sum(r.monthly_savings for r in recommendations)
        annual_savings = _sum(r.annual_savings for r in recommendations)

        # --- guard rails -------------------------------------------------
        if not settings.openai_api_key or settings.openai_api_key.startswith("sk-test"):
            logger.info("OpenAI key missing/test → returning fallback plan")
            return _fallback_plan(recommendations, total_savings, annual_savings)

        if not self._within_budget():
            logger.warning(
                "Daily GPT-4 budget reached (%d tokens) — using fallback",
                self.daily_token_budget,
            )
            return _fallback_plan(recommendations, total_savings, annual_savings)

        # --- distributed cache check -------------------------------------
        prompt = _build_prompt(recommendations, org_name, total_users)
        cache = get_cache()
        cache_key = "plan:" + hashlib.sha256(prompt.encode()).hexdigest()
        cached = await cache.get(cache_key)
        if cached is not None:
            plan = _parse_plan(cached)
            if plan is not None:
                logger.info("Plan cache HIT (%s)", cache_key[:20])
                plan.total_estimated_savings = total_savings
                plan.annual_estimated_savings = annual_savings
                plan.model_version = f"{settings.openai_model}+cache"
                return plan

        # --- call GPT-4 --------------------------------------------------
        try:
            raw = await self.gpt4.complete(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.4,
                use_cache=False,  # we manage the cache one level up
            )
        except Exception as exc:  # noqa: BLE001 — any failure → fallback
            logger.warning("GPT-4 call failed: %s — using fallback", exc)
            return _fallback_plan(recommendations, total_savings, annual_savings)

        # Track tokens consumed by GPT4Client (best-effort).
        self._tokens_spent_today = self.gpt4.total_tokens_used

        plan = _parse_plan(raw)
        if plan is None:
            logger.warning("Could not parse GPT-4 JSON — using fallback")
            return _fallback_plan(recommendations, total_savings, annual_savings)

        # Store the raw GPT JSON in cache for 24h (CFO plans are stable)
        await cache.set(cache_key, raw, ttl_seconds=86_400)

        plan.total_estimated_savings = total_savings
        plan.annual_estimated_savings = annual_savings
        plan.model_version = settings.openai_model
        return plan

    # ------------------------------------------------------------------ budget
    def _within_budget(self) -> bool:
        if utcnow() - self._budget_window_start > timedelta(hours=24):
            # Roll the window
            self._budget_window_start = utcnow()
            self._tokens_spent_today = 0
        return self._tokens_spent_today < self.daily_token_budget


# ---------------------------------------------------------------------- helpers


def _sum(values) -> Decimal:
    total = Decimal("0")
    for v in values:
        total += v
    return total


def _build_prompt(
    recommendations: List[Recommendation],
    org_name: str,
    total_users: int,
) -> str:
    critical = [r for r in recommendations if r.priority == Priority.CRITICAL][:5]
    high = [r for r in recommendations if r.priority == Priority.HIGH][:5]
    medium = [r for r in recommendations if r.priority == Priority.MEDIUM][:3]

    def _line(rec: Recommendation) -> str:
        return f"- {rec.title} — {rec.username} (économie {rec.monthly_savings}€/mois)"

    sections = [
        "# Mission : plan d'action d'optimisation des licences Salesforce",
        f"## Contexte",
        f"- Organisation : {org_name}",
        f"- Utilisateurs analysés : {total_users}",
        f"- Recommandations totales : {len(recommendations)}",
        f"- Économies potentielles : {sum(r.monthly_savings for r in recommendations):.2f}€/mois",
    ]
    if critical:
        sections.append("\n## Recommandations CRITIQUES")
        sections.extend(_line(r) for r in critical)
    if high:
        sections.append("\n## Recommandations HAUTE priorité")
        sections.extend(_line(r) for r in high)
    if medium:
        sections.append("\n## Recommandations MOYENNE priorité")
        sections.extend(_line(r) for r in medium)

    sections.append(
        "\n## Format attendu (JSON STRICT, sans markdown wrapper)\n"
        '{"title":"string","executive_summary":"string",'
        '"steps":[{"title":"string","description":"string","duration_days":int,'
        '"resources":["string"],"success_criteria":["string"]}],'
        '"quick_wins":["string"],'
        '"risks":[{"risk":"string","mitigation":"string"}],'
        '"timeline":"string"}'
    )
    return "\n".join(sections)


def _parse_plan(raw: str) -> Optional[ActionPlan]:
    """Best-effort JSON parsing tolerant of ```json fences."""
    text = raw.strip()
    if text.startswith("```"):
        # Strip ``` fences
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None

    try:
        return ActionPlan(
            title=data.get("title") or "Plan d'optimisation des licences Salesforce",
            executive_summary=data.get("executive_summary", ""),
            steps=[PlanStep(**s) for s in data.get("steps", [])],
            quick_wins=list(data.get("quick_wins", [])),
            risks=[PlanRisk(**r) for r in data.get("risks", [])],
            timeline=data.get("timeline", "30-90 jours"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("ActionPlan validation failed: %s", exc)
        return None


def _fallback_plan(
    recommendations: List[Recommendation],
    total_savings: Decimal,
    annual_savings: Decimal,
) -> ActionPlan:
    """Deterministic plan returned when GPT-4 is unavailable."""
    critical_count = sum(1 for r in recommendations if r.priority == Priority.CRITICAL)
    return ActionPlan(
        title="Plan d'optimisation des licences Salesforce",
        executive_summary=(
            f"Analyse de {len(recommendations)} recommandations sur les licences "
            f"Salesforce. Économies mensuelles potentielles : {total_savings:.0f}€ "
            f"({annual_savings:.0f}€/an). {critical_count} actions critiques à "
            f"traiter en priorité."
        ),
        steps=[
            PlanStep(
                title="Phase 1 — Validation des recommandations critiques",
                description=(
                    "Revoir avec les managers métier les utilisateurs zombies "
                    "et inactifs pour confirmation de désactivation."
                ),
                duration_days=5,
                resources=["IT Manager", "Finance", "Managers métier"],
                success_criteria=[
                    "Liste des utilisateurs à désactiver validée",
                    "Plan de communication aux utilisateurs prêt",
                ],
            ),
            PlanStep(
                title="Phase 2 — Désactivation et downgrade",
                description=(
                    "Appliquer les actions critiques + downgrade des licences "
                    "sous-utilisées vers Platform ou Free."
                ),
                duration_days=10,
                resources=["Administrateur Salesforce"],
                success_criteria=[
                    "Tous les utilisateurs critiques traités",
                    "Coûts mensuels réduits conformément aux estimations",
                ],
            ),
            PlanStep(
                title="Phase 3 — Suivi et mesure du ROI",
                description=(
                    "Vérifier après 30 jours qu'aucun ticket utilisateur n'est "
                    "lié au changement et confirmer les économies réalisées."
                ),
                duration_days=30,
                resources=["IT Manager", "Finance"],
                success_criteria=[
                    "Économies réalisées ≥ 80 % de l'estimation",
                    "< 5 % de demandes de réactivation",
                ],
            ),
        ],
        quick_wins=[
            "Désactiver immédiatement les utilisateurs jamais connectés",
            "Downgrade des licences Sales Cloud vers Platform pour les profils admin uniquement",
            "Auditer mensuellement les licences Einstein non utilisées",
        ],
        risks=[
            PlanRisk(
                risk="Réactivation tardive d'utilisateurs désactivés à tort",
                mitigation="Conserver les profils + permissions 90 jours avant suppression définitive",
            ),
            PlanRisk(
                risk="Résistance des équipes commerciales au downgrade",
                mitigation="Communication amont + démonstration que les features critiques restent accessibles",
            ),
        ],
        timeline="45 jours (Phase 1 → Phase 3)",
        total_estimated_savings=total_savings,
        annual_estimated_savings=annual_savings,
        model_version="fallback",
    )


# Default singleton
plan_generator = PlanGenerator()
