"""
PDF Report Generator Service.

Generates professional 30-40 page PDF reports with charts and styling.
"""
import logging
from typing import List
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from decimal import Decimal

from app.models.recommendation import Recommendation, ActionPlan
from app.models.user import ClassifiedUser, UserCategory

logger = logging.getLogger(__name__)


class PDFService:
    """
    Service for generating PDF reports using WeasyPrint and Jinja2.
    
    Features:
    - Professional multi-page layouts
    - Data-driven charts and tables
    - Executive summaries
    - Detailed recommendations
    - Action plans
    """
    
    def __init__(self):
        """Initialize PDF service."""
        templates_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))
    
    async def generate_full_report(
        self,
        organization_name: str,
        classified_users: List[ClassifiedUser],
        recommendations: dict,  # user_id -> List[Recommendation]
        action_plan: ActionPlan,
        output_path: str
    ) -> Path:
        """
        Generate comprehensive 30-40 page PDF report.
        
        Args:
            organization_name: Organization name
            classified_users: List of classified users
            recommendations: Dictionary of recommendations by user
            action_plan: Generated action plan
            output_path: Output file path
            
        Returns:
            Path to generated PDF
        """
        logger.info(f"Generating PDF report for {organization_name}")
        
        # Aggregate data
        all_recommendations = []
        for user_recs in recommendations.values():
            all_recommendations.extend(user_recs)
        
        # Sort by priority and savings
        all_recommendations.sort(
            key=lambda r: (r.priority.value, -float(r.monthly_savings)),
            reverse=True
        )
        
        # Calculate statistics
        total_users = len(classified_users)
        monthly_savings = sum(r.monthly_savings for r in all_recommendations)
        annual_savings = sum(r.annual_savings for r in all_recommendations)
        
        # Category distribution
        categories = {
            "INACTIVE": sum(1 for u in classified_users if u.category == UserCategory.INACTIVE),
            "UNDERUTILIZED": sum(1 for u in classified_users if u.category == UserCategory.UNDERUTILIZED),
            "OPTIMIZABLE": sum(1 for u in classified_users if u.category == UserCategory.OPTIMIZABLE),
            "EFFICIENT": sum(1 for u in classified_users if u.category == UserCategory.EFFICIENT),
        }
        
        inactive_users = categories["INACTIVE"]
        
        # Prepare context
        context = {
            "title": "Rapport d'Optimisation Salesforce",
            "organization_name": organization_name,
            "generated_date": datetime.utcnow().strftime("%d/%m/%Y"),
            "executive_summary": self._generate_executive_summary(
                total_users,
                monthly_savings,
                len(all_recommendations)
            ),
            "total_users": total_users,
            "inactive_users": inactive_users,
            "monthly_savings": float(monthly_savings),
            "annual_savings": float(annual_savings),
            "recommendations": [self._recommendation_to_dict(r) for r in all_recommendations],
            "categories": categories,
            "action_plan": self._action_plan_to_dict(action_plan),
        }
        
        # Render template
        template = self.env.get_template("full_report.html")
        html_content = template.render(**context)
        
        # Generate PDF
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        HTML(string=html_content).write_pdf(output_file)
        
        logger.info(f"PDF report generated: {output_file}")
        
        return output_file
    
    def _generate_executive_summary(
        self,
        total_users: int,
        monthly_savings: Decimal,
        recommendations_count: int
    ) -> str:
        """Generate executive summary text."""
        return (
            f"Ce rapport présente une analyse complète de {total_users} utilisateurs Salesforce. "
            f"Nous avons identifié {recommendations_count} opportunités d'optimisation "
            f"représentant une économie potentielle de ${monthly_savings:,.2f} par mois, "
            f"soit ${monthly_savings * 12:,.2f} annuellement. "
            f"Les recommandations sont classées par priorité et incluent des actions "
            f"immédiates ainsi qu'un plan détaillé pour maximiser le ROI."
        )
    
    def _recommendation_to_dict(self, rec: Recommendation) -> dict:
        """Convert Recommendation to dict for template."""
        return {
            "priority": rec.priority.value,
            "type": rec.type.value,
            "username": rec.username,
            "license_type": rec.license_type,
            "title": rec.title,
            "description": rec.description,
            "rationale": rec.rationale,
            "monthly_savings": float(rec.monthly_savings),
            "annual_savings": float(rec.annual_savings),
            "implementation_complexity": rec.implementation_complexity,
            "implementation_time_days": rec.implementation_time_days,
            "risk_level": rec.risk_level,
        }
    
    def _action_plan_to_dict(self, plan: ActionPlan) -> dict:
        """Convert ActionPlan to dict for template."""
        return {
            "title": plan.title,
            "executive_summary": plan.executive_summary,
            "steps": plan.steps,
            "quick_wins": plan.quick_wins,
            "risks": plan.risks,
            "timeline": plan.timeline,
        }


# Default instance
pdf_service = PDFService()

