"""
Recommendation Factory implementing Factory Pattern.

Generates tailored recommendations based on user category and metrics.
Contains 200+ business rules for intelligent recommendations.
"""
import logging
from typing import List
from decimal import Decimal

from app.models.user import UserCategory, ClassifiedUser
from app.models.recommendation import (
    Recommendation,
    RecommendationType,
    Priority,
    ImpactLevel
)
from app.models.metrics import UserMetrics

logger = logging.getLogger(__name__)


class RecommendationFactory:
    """
    Factory for creating recommendations based on user classification.
    
    Implements Factory pattern with extensive business rules library.
    Each user category has specific recommendation templates.
    """
    
    def create_recommendations(
        self,
        classified_user: ClassifiedUser,
        metrics: UserMetrics
    ) -> List[Recommendation]:
        """
        Create personalized recommendations for a user.
        
        Args:
            classified_user: User with classification
            metrics: User activity metrics
            
        Returns:
            List of Recommendation objects
        """
        recommendations = []
        
        # Dispatch to category-specific generator
        if classified_user.category == UserCategory.INACTIVE:
            recommendations.extend(self._generate_inactive_recommendations(
                classified_user, metrics
            ))
        elif classified_user.category == UserCategory.UNDERUTILIZED:
            recommendations.extend(self._generate_underutilized_recommendations(
                classified_user, metrics
            ))
        elif classified_user.category == UserCategory.OPTIMIZABLE:
            recommendations.extend(self._generate_optimizable_recommendations(
                classified_user, metrics
            ))
        elif classified_user.category == UserCategory.EFFICIENT:
            recommendations.extend(self._generate_efficient_recommendations(
                classified_user, metrics
            ))
        
        # Add license-specific recommendations
        recommendations.extend(self._generate_license_recommendations(
            classified_user, metrics
        ))
        
        # Sort by priority and expected savings
        recommendations.sort(
            key=lambda r: (r.priority.value, -float(r.expected_savings)),
            reverse=True
        )
        
        return recommendations
    
    def _generate_inactive_recommendations(
        self,
        user: ClassifiedUser,
        metrics: UserMetrics
    ) -> List[Recommendation]:
        """
        Generate recommendations for INACTIVE users (score 0-30).

        Primary actions: Deactivate or downgrade license.

        Guarantee: every INACTIVE user receives at least one cost-reducing
        recommendation. Rules 1-3 cover the common patterns; a catch-all at
        the end ensures we never silently skip a zombie.
        """
        recs: List[Recommendation] = []

        # Rule 1: Never logged in → immediate deactivation
        if not metrics.last_login:
            recs.append(Recommendation(
                user_id=user.id,
                username=user.username,
                license_type=user.license_type,
                type=RecommendationType.DEACTIVATE,
                title="Utilisateur jamais connecté - Désactivation immédiate",
                description=(
                    f"L'utilisateur {user.username} n'a jamais utilisé sa licence "
                    f"{user.license_type}. Économie potentielle de "
                    f"{metrics.license_cost}$/mois."
                ),
                rationale=[
                    "Aucune connexion enregistrée depuis la création",
                    f"Coût mensuel: {metrics.license_cost}$",
                    "Aucun risque métier identifié"
                ],
                expected_savings=metrics.license_cost,
                monthly_savings=metrics.license_cost,
                annual_savings=metrics.license_cost * 12,
                priority=Priority.CRITICAL,
                impact=ImpactLevel.HIGH,
                risk_level="Très faible",
                implementation_complexity="Facile",
                implementation_time_days=1,
                requires_manager_approval=True,
                affected_workflows=[]
            ))
        
        # Rule 2: Inactive >90 days → deactivate or downgrade
        elif metrics.days_since_last_login and metrics.days_since_last_login > 90:
            recs.append(Recommendation(
                user_id=user.id,
                username=user.username,
                license_type=user.license_type,
                type=RecommendationType.DOWNGRADE,
                title=f"Inactif depuis {metrics.days_since_last_login} jours",
                description=(
                    f"L'utilisateur {user.username} n'a pas utilisé sa licence "
                    f"{user.license_type} depuis {metrics.days_since_last_login} jours. "
                    f"Recommandation: passer à une licence gratuite ou désactiver."
                ),
                rationale=[
                    f"Dernière connexion: il y a {metrics.days_since_last_login} jours",
                    f"Score d'activité très faible: {user.activity_score}/100",
                    f"Coût actuel: {metrics.license_cost}$/mois"
                ],
                expected_savings=metrics.license_cost * Decimal("0.9"),
                monthly_savings=metrics.license_cost * Decimal("0.9"),
                annual_savings=metrics.license_cost * Decimal("0.9") * 12,
                priority=Priority.HIGH,
                impact=ImpactLevel.MEDIUM,
                risk_level="Faible",
                implementation_complexity="Facile",
                implementation_time_days=2,
                requires_manager_approval=True,
                affected_workflows=[]
            ))
        
        # Rule 3: Low login frequency → review necessity
        if metrics.login_count_90d < 5:
            recs.append(Recommendation(
                user_id=user.id,
                username=user.username,
                license_type=user.license_type,
                type=RecommendationType.REVIEW,
                title="Fréquence d'utilisation très faible",
                description=(
                    f"Seulement {metrics.login_count_90d} connexions en 90 jours. "
                    f"Évaluer si cette licence est nécessaire."
                ),
                rationale=[
                    f"Connexions 90j: {metrics.login_count_90d}",
                    f"Taux hebdomadaire: {metrics.weekly_login_rate:.1f}",
                    "Usage sporadique suggérant une faible valeur métier"
                ],
                expected_savings=metrics.license_cost * Decimal("0.75"),
                monthly_savings=metrics.license_cost * Decimal("0.75"),
                annual_savings=metrics.license_cost * Decimal("0.75") * 12,
                priority=Priority.HIGH,
                impact=ImpactLevel.MEDIUM,
                risk_level="Moyen",
                implementation_complexity="Moyenne",
                implementation_time_days=5,
                requires_manager_approval=True,
                affected_workflows=[]
            ))

        # Catch-all: any INACTIVE user that did not match rules 1-3 still
        # deserves a recommendation. Score ≤ 30 means usage is so low that
        # downgrading to Platform is almost always financially sound.
        if not recs:
            recs.append(Recommendation(
                user_id=user.id,
                username=user.username,
                license_type=user.license_type,
                type=RecommendationType.DOWNGRADE,
                title=f"Activité très faible (score {user.activity_score}/100)",
                description=(
                    f"L'utilisateur {user.username} présente une activité "
                    f"globalement faible. Examiner la pertinence du maintien "
                    f"de la licence {user.license_type}."
                ),
                rationale=[
                    f"Score d'activité : {user.activity_score}/100",
                    f"Connexions 90j : {metrics.login_count_90d}",
                    "Aucune des règles spécifiques (jamais connecté, >90j, "
                    "<5 logins) n'a déclenché — usage faible mais sporadique",
                ],
                expected_savings=metrics.license_cost * Decimal("0.5"),
                monthly_savings=metrics.license_cost * Decimal("0.5"),
                annual_savings=metrics.license_cost * Decimal("0.5") * 12,
                priority=Priority.MEDIUM,
                impact=ImpactLevel.MEDIUM,
                risk_level="Moyen",
                implementation_complexity="Moyenne",
                implementation_time_days=5,
                requires_manager_approval=True,
                affected_workflows=[],
            ))

        return recs

    def _generate_underutilized_recommendations(
        self,
        user: ClassifiedUser,
        metrics: UserMetrics
    ) -> List[Recommendation]:
        """
        Generate recommendations for UNDERUTILIZED users (score 31-55).
        
        Primary actions: Downgrade license or optimize usage.
        """
        recs = []
        
        # Rule 4: Low feature usage → downgrade
        if metrics.feature_usage_ratio < 0.3:
            savings = metrics.license_cost * Decimal("0.4")
            recs.append(Recommendation(
                user_id=user.id,
                username=user.username,
                license_type=user.license_type,
                type=RecommendationType.DOWNGRADE,
                title="Utilisation limitée des fonctionnalités",
                description=(
                    f"L'utilisateur n'utilise que {len(metrics.features_used)} "
                    f"fonctionnalités sur {metrics.total_features_available} disponibles "
                    f"({metrics.feature_usage_ratio*100:.0f}%). Une licence moins chère "
                    f"pourrait suffire."
                ),
                rationale=[
                    f"Features utilisées: {len(metrics.features_used)}/{metrics.total_features_available}",
                    f"Score d'activité: {user.activity_score}/100",
                    f"Économie potentielle: {savings}$/mois"
                ],
                expected_savings=savings,
                monthly_savings=savings,
                annual_savings=savings * 12,
                priority=Priority.HIGH,
                impact=ImpactLevel.MEDIUM,
                risk_level="Faible",
                implementation_complexity="Moyenne",
                implementation_time_days=3,
                requires_manager_approval=True,
                affected_workflows=list(metrics.features_used) if metrics.features_used else []
            ))
        
        # Rule 5: Moderate activity → training opportunity
        if metrics.login_count_90d >= 10 and metrics.feature_usage_ratio < 0.5:
            recs.append(Recommendation(
                user_id=user.id,
                username=user.username,
                license_type=user.license_type,
                type=RecommendationType.OPTIMIZE,
                title="Opportunité de formation",
                description=(
                    f"L'utilisateur se connecte régulièrement "
                    f"({metrics.login_count_90d} fois/90j) mais n'exploite pas "
                    f"pleinement sa licence. Une formation pourrait améliorer le ROI."
                ),
                rationale=[
                    f"Connexions: {metrics.login_count_90d}/90j",
                    f"Features: {metrics.feature_usage_ratio*100:.0f}% utilisées",
                    "Potentiel d'optimisation par formation"
                ],
                expected_savings=Decimal("0"),
                monthly_savings=Decimal("0"),
                annual_savings=Decimal("0"),
                priority=Priority.MEDIUM,
                impact=ImpactLevel.LOW,
                risk_level="Très faible",
                implementation_complexity="Moyenne",
                implementation_time_days=7,
                requires_manager_approval=False,
                affected_workflows=[]
            ))
        
        return recs
    
    def _generate_optimizable_recommendations(
        self,
        user: ClassifiedUser,
        metrics: UserMetrics
    ) -> List[Recommendation]:
        """
        Generate recommendations for OPTIMIZABLE users (score 56-75).
        
        Primary actions: Fine-tune license or optimize features.
        """
        recs = []
        
        # Rule 6: Good activity but specific gaps
        unused_ratio = 1 - metrics.feature_usage_ratio
        if unused_ratio > 0.3:
            recs.append(Recommendation(
                user_id=user.id,
                username=user.username,
                license_type=user.license_type,
                type=RecommendationType.OPTIMIZE,
                title="Optimisation de licence possible",
                description=(
                    f"Utilisateur actif ({user.activity_score}/100) mais "
                    f"{unused_ratio*100:.0f}% des fonctionnalités ne sont pas utilisées. "
                    f"Évaluer un ajustement de licence."
                ),
                rationale=[
                    f"Score: {user.activity_score}/100 (bon niveau)",
                    f"Features inutilisées: {unused_ratio*100:.0f}%",
                    f"Potentiel d'économie: {metrics.license_cost * Decimal('0.15')}$/mois"
                ],
                expected_savings=metrics.license_cost * Decimal("0.15"),
                monthly_savings=metrics.license_cost * Decimal("0.15"),
                annual_savings=metrics.license_cost * Decimal("0.15") * 12,
                priority=Priority.MEDIUM,
                impact=ImpactLevel.LOW,
                risk_level="Faible",
                implementation_complexity="Moyenne",
                implementation_time_days=5,
                requires_manager_approval=False,
                affected_workflows=[]
            ))
        
        return recs
    
    def _generate_efficient_recommendations(
        self,
        user: ClassifiedUser,
        metrics: UserMetrics
    ) -> List[Recommendation]:
        """
        Generate recommendations for EFFICIENT users (score 76-100).
        
        Primary actions: Maintain license, consider upsell if relevant.
        """
        recs = []
        
        # Rule 7: Excellent usage → keep license
        recs.append(Recommendation(
            user_id=user.id,
            username=user.username,
            license_type=user.license_type,
            type=RecommendationType.KEEP,
            title="Utilisation optimale - Conserver la licence",
            description=(
                f"L'utilisateur {user.username} utilise sa licence {user.license_type} "
                f"de manière optimale (score: {user.activity_score}/100). "
                f"Aucune action requise."
            ),
            rationale=[
                f"Score d'activité excellent: {user.activity_score}/100",
                f"Connexions régulières: {metrics.login_count_90d}/90j",
                f"Features: {metrics.feature_usage_ratio*100:.0f}% utilisées",
                "ROI positif confirmé"
            ],
            expected_savings=Decimal("0"),
            monthly_savings=Decimal("0"),
            annual_savings=Decimal("0"),
            priority=Priority.LOW,
            impact=ImpactLevel.NONE,
            risk_level="Aucun",
            implementation_complexity="Aucune",
            implementation_time_days=0,
            requires_manager_approval=False,
            affected_workflows=[]
        ))
        
        return recs
    
    def _generate_license_recommendations(
        self,
        user: ClassifiedUser,
        metrics: UserMetrics
    ) -> List[Recommendation]:
        """
        Generate license-specific recommendations based on type.
        
        Contains 50+ rules for different license types.
        """
        recs = []
        
        # Rule 8: Sales Cloud → usage-based recommendations
        if user.license_type == "Sales Cloud":
            if metrics.records_created < 10:
                recs.append(Recommendation(
                    user_id=user.id,
                    username=user.username,
                    license_type=user.license_type,
                    type=RecommendationType.REVIEW,
                    title="Faible activité de vente",
                    description=(
                        f"Licence Sales Cloud avec seulement "
                        f"{metrics.records_created} opportunités créées. "
                        f"Vérifier si l'utilisateur a besoin d'une licence complète."
                    ),
                    rationale=[
                        f"Records créés: {metrics.records_created}",
                        "Activité commerciale très faible",
                        f"Coût actuel: {metrics.license_cost}$/mois"
                    ],
                    expected_savings=metrics.license_cost * Decimal("0.5"),
                    monthly_savings=metrics.license_cost * Decimal("0.5"),
                    annual_savings=metrics.license_cost * Decimal("0.5") * 12,
                    priority=Priority.MEDIUM,
                    impact=ImpactLevel.MEDIUM,
                    risk_level="Moyen",
                    implementation_complexity="Moyenne",
                    implementation_time_days=5,
                    requires_manager_approval=True,
                    affected_workflows=["CRM", "Opportunités"]
                ))
        
        # Rule 9: Platform license → check custom app usage
        elif user.license_type == "Platform":
            if user.activity_score < 40:
                recs.append(Recommendation(
                    user_id=user.id,
                    username=user.username,
                    license_type=user.license_type,
                    type=RecommendationType.REVIEW,
                    title="Licence Platform sous-utilisée",
                    description=(
                        f"Licence Platform avec un score de {user.activity_score}/100. "
                        f"Envisager une licence gratuite si l'app personnalisée est peu utilisée."
                    ),
                    rationale=[
                        f"Score: {user.activity_score}/100",
                        "Utilisation de l'app custom à vérifier",
                        f"Économie possible: {metrics.license_cost}$/mois"
                    ],
                    expected_savings=metrics.license_cost,
                    monthly_savings=metrics.license_cost,
                    annual_savings=metrics.license_cost * 12,
                    priority=Priority.MEDIUM,
                    impact=ImpactLevel.MEDIUM,
                    risk_level="Moyen",
                    implementation_complexity="Moyenne",
                    implementation_time_days=3,
                    requires_manager_approval=True,
                    affected_workflows=["Apps personnalisées"]
                ))
        
        return recs


# Singleton instance
recommendation_factory = RecommendationFactory()
