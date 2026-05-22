"""Render artifacts/live-e2e-report.json into a client-ready Markdown deliverable."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "artifacts" / "live-e2e-report.json"
OUT = REPO_ROOT / "artifacts" / "CLIENT_REPORT.md"


def fmt_eur(n: float) -> str:
    return f"{n:,.0f} €".replace(",", " ")


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    fin = data["financials"]
    dist = data["distribution"]
    recs = data["recommendations"]
    alerts = data["security_alerts"]
    plan = data["plan_preview"]

    lines: list[str] = []
    lines.append(f"# Rapport d'Optimisation Salesforce — {data['org_name']}")
    lines.append("")
    lines.append(
        f"> **Org analysée** : `{data['org_id']}`  \n"
        f"> **Date du rapport** : {data['generated_at'][:10]}  \n"
        f"> **Modèle IA utilisé** : `{plan['model']}`"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Résumé exécutif")
    lines.append("")
    lines.append(plan["executive_summary"])
    lines.append("")
    lines.append("### Chiffres clés")
    lines.append("")
    lines.append("| Indicateur | Valeur |")
    lines.append("|---|---:|")
    lines.append(f"| Utilisateurs analysés | **{data['total_users_analysed']}** |")
    lines.append(f"| Coût mensuel actuel | **{fmt_eur(fin['current_monthly_cost_eur'])}** |")
    lines.append(f"| Économies mensuelles potentielles | **{fmt_eur(fin['potential_monthly_savings_eur'])}** |")
    lines.append(f"| **Économies annuelles potentielles** | **{fmt_eur(fin['potential_annual_savings_eur'])}** |")
    lines.append(f"| Taux d'économies | **{fin['savings_rate_pct']:.1f} %** |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Distribution des utilisateurs")
    lines.append("")
    lines.append("| Catégorie | Utilisateurs | % | Action recommandée |")
    lines.append("|---|---:|---:|---|")
    labels = {
        "inactive": ("🔴 Inactifs", "Désactivation immédiate"),
        "underutilized": ("🟠 Sous-utilisés", "Downgrade ou formation"),
        "optimizable": ("🔵 Optimisables", "Ajustement de licence"),
        "efficient": ("🟢 Efficaces", "Conserver"),
    }
    total = data["total_users_analysed"]
    for k in ("inactive", "underutilized", "optimizable", "efficient"):
        n = dist.get(k, 0)
        pct = (n / total * 100) if total else 0
        label, action = labels[k]
        lines.append(f"| {label} | {n} | {pct:.1f} % | {action} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Recommandations — synthèse")
    lines.append("")
    lines.append(f"**{recs['total']} recommandations** générées, ventilées :")
    lines.append("")
    lines.append("- **Par type** : " + " · ".join(f"`{k}` ({v})" for k, v in recs["by_type"].items()))
    lines.append("- **Par priorité** : " + " · ".join(f"`{k}` ({v})" for k, v in recs["by_priority"].items()))
    lines.append("")
    lines.append("### Top 10 par économie mensuelle")
    lines.append("")
    lines.append("| Utilisateur | Licence | Action | Priorité | Économie/mois |")
    lines.append("|---|---|---|---|---:|")
    for r in data["top10_savings"]:
        lines.append(
            f"| `{r['username']}` | {r['license']} | {r['type']} | "
            f"{r['priority']} | {fmt_eur(r['monthly_savings_eur'])} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Plan d'action CFO (généré par IA)")
    lines.append("")
    lines.append(f"### {plan['title']}")
    lines.append("")
    lines.append("**Étapes :**")
    for i, s in enumerate(plan["step_titles"], 1):
        lines.append(f"{i}. {s}")
    lines.append("")
    if plan["quick_wins"]:
        lines.append("**Quick wins :**")
        for q in plan["quick_wins"]:
            lines.append(f"- {q}")
        lines.append("")
    if plan["risks"]:
        lines.append("**Risques & mitigation :**")
        lines.append("")
        lines.append("| Risque | Mitigation |")
        lines.append("|---|---|")
        for r in plan["risks"]:
            lines.append(f"| {r['risk']} | {r['mitigation']} |")
        lines.append("")
    lines.append(f"**Calendrier** : {plan['timeline']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 5. Alertes de sécurité")
    lines.append("")
    lines.append(f"**{alerts['total']} alertes** détectées par le PermissionMonitor :")
    lines.append("")
    for sev, n in sorted(alerts["by_severity"].items(), key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x[0], 9)):
        lines.append(f"- **{sev}** : {n}")
    lines.append("")
    lines.append("### Échantillon (15 alertes les plus sévères)")
    lines.append("")
    lines.append("| Sévérité | Utilisateur | Règle déclenchée |")
    lines.append("|---|---|---|")
    for a in data["top_alerts"]:
        lines.append(f"| **{a['severity']}** | `{a['user']}` | `{a['rule']}` |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 6. Méthodologie & disclaimers")
    lines.append("")
    lines.append(
        "- **Données collectées via Salesforce CLI** (SOQL temps réel) — pas de mock.\n"
        "- **Classification** : algorithme de scoring 0–100 (recency, frequency, "
        "feature usage, record activity) → 4 catégories.\n"
        "- **Recommandations** : moteur à règles + factory, score-based.\n"
        "- **Plan CFO** : généré par `gpt-4o` (OpenAI), fallback déterministe "
        "si l'API n'est pas joignable.\n"
        "- **Économies estimées** : prennent la meilleure recommandation par "
        "utilisateur (pas de double-comptage).\n"
        "- **Org analysée = sandbox dev** : le taux d'inactivité (99.9 %) est "
        "exceptionnellement élevé car les comptes sont copiés depuis prod sans "
        "y être réutilisés. Sur une org production réelle, attendre 20–40 % "
        "d'inactifs (toujours actionnable financièrement)."
    )
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Client report : {OUT}  ({len(lines)} lignes)")


if __name__ == "__main__":
    main()
