"""Permission monitor.

Generates ``SecurityAlertDTO`` events from an ``AnalysisResult`` by spotting
suspicious patterns. Phase 1 rules (kept narrow on purpose):

- INACTIVE user with admin profile      → CRITICAL  (orphan admin)
- High-privilege license never used     → HIGH
- INACTIVE user holding a Salesforce    → MEDIUM  (cost + audit risk)
  license (full CRM) for 90+ days

A real implementation would also consume ``PermissionSetAssignment`` data and
push to the ``security_alerts`` table; this slice is the demo-able skeleton.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from app.models.user import ClassifiedUser, UserCategory
from app.services.analysis_service import AnalysisResult

logger = logging.getLogger(__name__)

_ADMIN_PROFILE_NAMES = {
    "System Administrator",
    "Customer Administrator",
    "Modify All Data",
}
_HIGH_VALUE_LICENSES = {
    "Salesforce",
    "Sales Cloud",
    "Service Cloud",
    "Sales Cloud Einstein",
}
# Score threshold below which a high-value licence is considered effectively
# unused. 5 = barely any meaningful activity (<2 logins, no features).
_UNUSED_SCORE_THRESHOLD = 10


@dataclass(frozen=True)
class SecurityAlert:
    user_id: str
    username: str
    severity: str          # CRITICAL / HIGH / MEDIUM / LOW
    permission: str        # tag for the kind of rule that fired
    description: str
    recommended_action: str


class PermissionMonitor:
    def scan(self, result: AnalysisResult) -> List[SecurityAlert]:
        alerts: List[SecurityAlert] = []
        for user in result.classified:
            alerts.extend(self._rules(user))
        logger.info(
            "PermissionMonitor scan complete: %d alerts on %d users",
            len(alerts), len(result.classified),
        )
        return alerts

    def _rules(self, user: ClassifiedUser) -> List[SecurityAlert]:
        out: List[SecurityAlert] = []

        is_inactive = user.category == UserCategory.INACTIVE
        is_admin = user.profile_name in _ADMIN_PROFILE_NAMES
        is_high_value = user.license_type in _HIGH_VALUE_LICENSES
        long_dormant = user.days_inactive is not None and user.days_inactive >= 90

        if is_inactive and is_admin:
            out.append(SecurityAlert(
                user_id=user.id,
                username=user.username,
                severity="CRITICAL",
                permission="orphan_admin",
                description=(
                    f"Compte administrateur ({user.profile_name}) inactif depuis "
                    f"{user.days_inactive or 'plus de 90'} jours — risque de "
                    f"compromission silencieuse."
                ),
                recommended_action="Désactiver immédiatement ou révoquer les permissions admin",
            ))

        if is_high_value and user.activity_score <= _UNUSED_SCORE_THRESHOLD:
            out.append(SecurityAlert(
                user_id=user.id,
                username=user.username,
                severity="HIGH",
                permission="unused_high_value_license",
                description=(
                    f"Licence {user.license_type} quasiment inutilisée "
                    f"(score {user.activity_score}/100)."
                ),
                recommended_action="Revoir l'attribution de licence ou désactiver l'utilisateur",
            ))

        if is_inactive and is_high_value and long_dormant and not is_admin:
            out.append(SecurityAlert(
                user_id=user.id,
                username=user.username,
                severity="MEDIUM",
                permission="dormant_high_value_license",
                description=(
                    f"Licence {user.license_type} inutilisée depuis "
                    f"{user.days_inactive} jours."
                ),
                recommended_action="Downgrade vers Platform ou désactivation",
            ))

        return out


permission_monitor = PermissionMonitor()
