"""
Action Plan Generator using GPT-4.

Generates detailed, actionable optimization plans based on recommendations.
"""
import logging
from typing import List
from datetime import datetime

from app.models.recommendation import Recommendation, ActionPlan
from app.clients.gpt4_client import GPT4Client

logger = logging.getLogger(__name__)


class PlanGenerator:
    """
    Service for generating AI-powered action plans.
    
    Uses GPT-4 to transform technical recommendations into
    business-friendly, step-by-step action plans.
    """
    
    SYSTEM_PROMPT = """Tu es un expert en optimisation des licences SaaS et en transformation digitale.
Ta mission est de transformer des recommandations techniques en plans d'action concrets, 
détaillés et faciles à exécuter pour des managers non-techniques.

Principes:
- Sois précis et actionnable
- Explique les risques et bénéfices
- Propose des étapes claires et ordonnées
- Inclus des critères de validation
- Reste professionnel et concis"""
    
    def __init__(self, gpt4_client: GPT4Client):
        """
        Initialize plan generator.
        
        Args:
            gpt4_client: GPT-4 client for AI generation
        """
        self.gpt4_client = gpt4_client
    
    async def generate_plan(
        self,
        recommendations: List[Recommendation],
        context: dict = None
    ) -> ActionPlan:
        """
        Generate comprehensive action plan from recommendations.
        
        Args:
            recommendations: List of recommendations to plan
            context: Optional context (org info, constraints)
            
        Returns:
            ActionPlan with detailed steps
        """
        logger.info(f"Generating action plan for {len(recommendations)} recommendations")
        
        # Build prompt
        prompt = self._build_prompt(recommendations, context)
        
        # Call GPT-4
        response = await self.gpt4_client.complete(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.5  # Lower for more focused output
        )
        
        # Parse response into ActionPlan
        plan = self._parse_response(response, recommendations)
        
        logger.info(f"Generated plan with {len(plan.steps)} steps")
        
        return plan
    
    def _build_prompt(
        self,
        recommendations: List[Recommendation],
        context: dict = None
    ) -> str:
        """Build structured prompt from recommendations."""
        
        # Group by priority
        critical = [r for r in recommendations if r.priority.value == "CRITICAL"]
        high = [r for r in recommendations if r.priority.value == "HIGH"]
        medium = [r for r in recommendations if r.priority.value == "MEDIUM"]
        
        prompt_parts = [
            "# Mission: Créer un plan d'action d'optimisation des licences Salesforce\n",
            f"## Contexte",
            f"- Nombre total de recommandations: {len(recommendations)}",
            f"- Économies totales potentielles: {sum(r.monthly_savings for r in recommendations):.2f}$/mois",
            f"- Économies annuelles: {sum(r.annual_savings for r in recommendations):.2f}$\n"
        ]
        
        if context:
            prompt_parts.append(f"- Organisation: {context.get('org_name', 'N/A')}")
            prompt_parts.append(f"- Nombre d'utilisateurs: {context.get('total_users', 'N/A')}\n")
        
        # Critical recommendations
        if critical:
            prompt_parts.append("\n## Recommandations CRITIQUES:")
            for i, rec in enumerate(critical[:5], 1):  # Max 5
                prompt_parts.append(
                    f"{i}. {rec.title} - Utilisateur: {rec.username} "
                    f"(Économie: {rec.monthly_savings}$/mois)"
                )
        
        # High priority
        if high:
            prompt_parts.append("\n## Recommandations HAUTE priorité:")
            for i, rec in enumerate(high[:5], 1):
                prompt_parts.append(
                    f"{i}. {rec.title} - Utilisateur: {rec.username} "
                    f"(Économie: {rec.monthly_savings}$/mois)"
                )
        
        # Medium priority
        if medium:
            prompt_parts.append("\n## Recommandations MOYENNE priorité:")
            for i, rec in enumerate(medium[:3], 1):
                prompt_parts.append(
                    f"{i}. {rec.title} - Utilisateur: {rec.username} "
                    f"(Économie: {rec.monthly_savings}$/mois)"
                )
        
        prompt_parts.append("\n## Instructions:")
        prompt_parts.append("""
Génère un plan d'action structuré avec:
1. Un titre percutant
2. Un executive summary (3-4 phrases)
3. Des étapes concrètes et priorisées avec:
   - Description claire
   - Durée estimée
   - Ressources nécessaires
   - Critères de validation
4. Des quick wins (actions immédiates)
5. Des risques identifiés et mitigation
6. Un calendrier réaliste sur 30-90 jours

Format: JSON avec les champs suivants:
{
  "title": "...",
  "executive_summary": "...",
  "steps": [
    {
      "title": "...",
      "description": "...",
      "duration_days": X,
      "resources": ["...", "..."],
      "success_criteria": ["...", "..."]
    }
  ],
  "quick_wins": ["...", "..."],
  "risks": [
    {
      "risk": "...",
      "mitigation": "..."
    }
  ],
  "timeline": "..."
}
""")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(
        self,
        response: str,
        recommendations: List[Recommendation]
    ) -> ActionPlan:
        """Parse GPT-4 response into ActionPlan object."""
        import json
        from decimal import Decimal
        
        try:
            # Try to extract JSON from response
            # GPT-4 might wrap it in ```json ... ```
            if "```json" in response:
                json_start = response.index("```json") + 7
                json_end = response.rindex("```")
                response = response[json_start:json_end].strip()
            
            data = json.loads(response)
            
            total_savings = sum(r.monthly_savings for r in recommendations)
            annual_savings = sum(r.annual_savings for r in recommendations)
            
            return ActionPlan(
                title=data.get("title", "Plan d'optimisation des licences"),
                executive_summary=data.get("executive_summary", ""),
                steps=data.get("steps", []),
                quick_wins=data.get("quick_wins", []),
                risks=data.get("risks", []),
                timeline=data.get("timeline", "30-90 jours"),
                total_estimated_savings=Decimal(str(total_savings)),
                annual_estimated_savings=Decimal(str(annual_savings)),
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to parse GPT-4 response: {e}")
            
            # Fallback to simple plan
            return self._create_fallback_plan(recommendations)
    
    def _create_fallback_plan(
        self,
        recommendations: List[Recommendation]
    ) -> ActionPlan:
        """Create fallback plan if GPT-4 parsing fails."""
        from decimal import Decimal
        
        steps = [
            {
                "title": "Phase 1: Audit et validation",
                "description": "Valider les recommandations avec les managers",
                "duration_days": 5,
                "resources": ["IT Manager", "Finance"],
                "success_criteria": ["Approbation des recommendations"]
            },
            {
                "title": "Phase 2: Implémentation",
                "description": "Appliquer les changements de licences",
                "duration_days": 10,
                "resources": ["Admin Salesforce"],
                "success_criteria": ["Licences modifiées", "Utilisateurs notifiés"]
            },
            {
                "title": "Phase 3: Suivi",
                "description": "Monitorer l'impact et ajuster",
                "duration_days": 15,
                "resources": ["IT Manager"],
                "success_criteria": ["Économies réalisées", "Aucun incident"]
            }
        ]
        
        total_savings = sum(r.monthly_savings for r in recommendations)
        annual_savings = sum(r.annual_savings for r in recommendations)
        
        return ActionPlan(
            title="Plan d'optimisation des licences Salesforce",
            executive_summary=f"Plan d'action pour optimiser {len(recommendations)} licences avec une économie potentielle de {total_savings:.2f}$/mois.",
            steps=steps,
            quick_wins=["Désactiver les utilisateurs inactifs", "Downgrade des licences sous-utilisées"],
            risks=[
                {
                    "risk": "Perturbation de l'accès utilisateur",
                    "mitigation": "Communication préalable et validation manager"
                }
            ],
            timeline="30 jours",
            total_estimated_savings=Decimal(str(total_savings)),
            annual_estimated_savings=Decimal(str(annual_savings)),
            generated_at=datetime.utcnow()
        )


# Default instance
plan_generator = PlanGenerator(gpt4_client=None)  # Will be injected
