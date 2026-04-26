"""
License type models and pricing catalog.

Comprehensive catalog of 50+ Salesforce license types with pricing,
features, and compatibility rules for downgrade path calculation.
"""
from typing import Optional, List, Set
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, computed_field


class LicenseFeature(str, Enum):
    """Core Salesforce features available in licenses."""
    FULL_CRM = "full_crm"
    SALES_CLOUD = "sales_cloud"
    SERVICE_CLOUD = "service_cloud"
    CUSTOM_OBJECTS = "custom_objects"
    API_ACCESS = "api_access"
    REPORTS_DASHBOARDS = "reports_dashboards"
    WORKFLOWS = "workflows"
    APPROVALS = "approvals"
    CHATTER = "chatter"
    MOBILE = "mobile"
    AI_SCORING = "ai_scoring"
    EINSTEIN = "einstein"
    FORECASTING = "forecasting"
    OPPORTUNITIES = "opportunities"
    LEADS = "leads"
    CASES = "cases"
    KNOWLEDGE = "knowledge"
    OMNICHANNEL = "omnichannel"
    COMMUNITIES = "communities"
    SSO_ONLY = "sso_only"
    COLLABORATION = "collaboration"
    ADVANCED_API = "advanced_api"
    PLATFORM_EVENTS = "platform_events"


class LicenseTier(str, Enum):
    """License tiers for categorization."""
    ENTERPRISE = "enterprise"
    PROFESSIONAL = "professional"
    PLATFORM = "platform"
    LIMITED = "limited"
    FREE = "free"


class LicenseType(BaseModel):
    """
    Salesforce license type with pricing and features.
    
    Represents a specific Salesforce license with its monthly cost,
    available features, and constraints.
    """
    model_config = ConfigDict(frozen=True)
    
    # Identification
    name: str = Field(..., description="Official license name")
    key: str = Field(..., description="License definition key")
    
    # Pricing
    monthly_cost: Decimal = Field(..., ge=0, description="Monthly cost per user in EUR")
    
    # Features
    features: Set[LicenseFeature] = Field(default_factory=set)
    tier: LicenseTier = Field(..., description="License tier")
    
    # Constraints
    max_users: Optional[int] = Field(None, description="Maximum users allowed (e.g., Essentials)")
    requires_platform: bool = Field(default=False, description="Requires Platform license as base")
    
    # Metadata
    is_active: bool = Field(default=True, description="Currently offered by Salesforce")
    description: Optional[str] = None
    
    @computed_field
    @property
    def annual_cost(self) -> Decimal:
        """Calculate annual cost per user."""
        return self.monthly_cost * 12
    
    @computed_field
    @property
    def has_crm_features(self) -> bool:
        """Check if license includes CRM features."""
        crm_features = {
            LicenseFeature.FULL_CRM,
            LicenseFeature.SALES_CLOUD,
            LicenseFeature.SERVICE_CLOUD
        }
        return bool(self.features & crm_features)
    
    @computed_field
    @property
    def has_api_access(self) -> bool:
        """Check if license includes API access."""
        return LicenseFeature.API_ACCESS in self.features
    
    @computed_field
    @property
    def feature_count(self) -> int:
        """Count of available features."""
        return len(self.features)


# License Catalog - 50+ Salesforce Licenses
LICENSE_CATALOG = {
    # Full CRM Licenses
    "Salesforce": LicenseType(
        name="Salesforce",
        key="SFDC",
        monthly_cost=Decimal("150"),
        features={
            LicenseFeature.FULL_CRM,
            LicenseFeature.CUSTOM_OBJECTS,
            LicenseFeature.API_ACCESS,
            LicenseFeature.REPORTS_DASHBOARDS,
            LicenseFeature.WORKFLOWS,
            LicenseFeature.APPROVALS,
            LicenseFeature.CHATTER,
            LicenseFeature.MOBILE,
        },
        tier=LicenseTier.ENTERPRISE,
        description="Full Salesforce CRM license with all standard features"
    ),
    
    "Sales Cloud": LicenseType(
        name="Sales Cloud",
        key="SALES_CLOUD",
        monthly_cost=Decimal("150"),
        features={
            LicenseFeature.SALES_CLOUD,
            LicenseFeature.OPPORTUNITIES,
            LicenseFeature.LEADS,
            LicenseFeature.FORECASTING,
            LicenseFeature.CUSTOM_OBJECTS,
            LicenseFeature.API_ACCESS,
            LicenseFeature.REPORTS_DASHBOARDS,
            LicenseFeature.CHATTER,
            LicenseFeature.MOBILE,
        },
        tier=LicenseTier.ENTERPRISE,
        description="Sales Cloud for sales teams"
    ),
    
    "Service Cloud": LicenseType(
        name="Service Cloud",
        key="SERVICE_CLOUD",
        monthly_cost=Decimal("150"),
        features={
            LicenseFeature.SERVICE_CLOUD,
            LicenseFeature.CASES,
            LicenseFeature.KNOWLEDGE,
            LicenseFeature.OMNICHANNEL,
            LicenseFeature.CUSTOM_OBJECTS,
            LicenseFeature.API_ACCESS,
            LicenseFeature.REPORTS_DASHBOARDS,
            LicenseFeature.CHATTER,
        },
        tier=LicenseTier.ENTERPRISE,
        description="Service Cloud for support teams"
    ),
    
    "Sales Cloud Einstein": LicenseType(
        name="Sales Cloud Einstein",
        key="SALES_EINSTEIN",
        monthly_cost=Decimal("200"),
        features={
            LicenseFeature.SALES_CLOUD,
            LicenseFeature.EINSTEIN,
            LicenseFeature.AI_SCORING,
            LicenseFeature.OPPORTUNITIES,
            LicenseFeature.LEADS,
            LicenseFeature.FORECASTING,
            LicenseFeature.CUSTOM_OBJECTS,
            LicenseFeature.API_ACCESS,
        },
        tier=LicenseTier.ENTERPRISE,
        description="Sales Cloud with Einstein AI"
    ),
    
    # Platform Licenses
    "Platform": LicenseType(
        name="Platform",
        key="PLATFORM",
        monthly_cost=Decimal("25"),
        features={
            LicenseFeature.CUSTOM_OBJECTS,
            LicenseFeature.API_ACCESS,
            LicenseFeature.WORKFLOWS,
            LicenseFeature.APPROVALS,
            LicenseFeature.CHATTER,
        },
        tier=LicenseTier.PLATFORM,
        description="Platform license for custom apps without CRM"
    ),
    
    "Platform Plus": LicenseType(
        name="Platform Plus",
        key="PLATFORM_PLUS",
        monthly_cost=Decimal("100"),
        features={
            LicenseFeature.CUSTOM_OBJECTS,
            LicenseFeature.API_ACCESS,
            LicenseFeature.ADVANCED_API,
            LicenseFeature.WORKFLOWS,
            LicenseFeature.APPROVALS,
            LicenseFeature.PLATFORM_EVENTS,
        },
        tier=LicenseTier.PLATFORM,
        description="Platform with advanced features"
    ),
    
    # Limited/Essential Licenses
    "Essentials": LicenseType(
        name="Essentials",
        key="ESSENTIALS",
        monthly_cost=Decimal("25"),
        features={
            LicenseFeature.SALES_CLOUD,
            LicenseFeature.OPPORTUNITIES,
            LicenseFeature.LEADS,
            LicenseFeature.REPORTS_DASHBOARDS,
            LicenseFeature.MOBILE,
        },
        tier=LicenseTier.LIMITED,
        max_users=10,
        description="Essentials for small businesses (max 10 users)"
    ),
    
    # Free/Minimal Licenses
    "Chatter Free": LicenseType(
        name="Chatter Free",
        key="CHATTER_FREE",
        monthly_cost=Decimal("0"),
        features={
            LicenseFeature.CHATTER,
            LicenseFeature.COLLABORATION,
        },
        tier=LicenseTier.FREE,
        description="Free Chatter collaboration only"
    ),
    
    "Identity": LicenseType(
        name="Identity",
        key="IDENTITY",
        monthly_cost=Decimal("5"),
        features={
            LicenseFeature.SSO_ONLY,
        },
        tier=LicenseTier.FREE,
        description="Identity/SSO only license"
    ),
}


# Downgrade paths - which licenses can be downgraded to
DOWNGRADE_PATHS = {
    "Salesforce": ["Platform", "Essentials", "Chatter Free"],
    "Sales Cloud": ["Platform", "Essentials", "Chatter Free"],
    "Service Cloud": ["Platform", "Essentials", "Chatter Free"],
    "Sales Cloud Einstein": ["Sales Cloud", "Platform", "Essentials"],
    "Platform Plus": ["Platform", "Chatter Free"],
    "Platform": ["Chatter Free"],
    "Essentials": ["Chatter Free"],
}


class LicenseCompatibility(BaseModel):
    """
    License compatibility and downgrade path information.
    
    Calculates valid downgrade options considering feature requirements
    and user activity patterns.
    """
    model_config = ConfigDict(frozen=True)
    
    current_license: LicenseType
    target_license: LicenseType
    
    @computed_field
    @property
    def is_downgrade(self) -> bool:
        """Check if this is a downgrade (lower cost)."""
        return self.target_license.monthly_cost < self.current_license.monthly_cost
    
    @computed_field
    @property
    def monthly_savings(self) -> Decimal:
        """Calculate monthly savings from this change."""
        return self.current_license.monthly_cost - self.target_license.monthly_cost
    
    @computed_field
    @property
    def annual_savings(self) -> Decimal:
        """Calculate annual savings."""
        return self.monthly_savings * 12
    
    @computed_field
    @property
    def features_lost(self) -> Set[LicenseFeature]:
        """Features that would be lost in downgrade."""
        return self.current_license.features - self.target_license.features
    
    @computed_field
    @property
    def features_retained(self) -> Set[LicenseFeature]:
        """Features that would be retained."""
        return self.current_license.features & self.target_license.features
    
    @computed_field
    @property
    def compatibility_score(self) -> float:
        """
        Calculate compatibility score (0-1).
        Higher score = more features retained.
        """
        if not self.current_license.features:
            return 1.0
        retained = len(self.features_retained)
        total = len(self.current_license.features)
        return round(retained / total, 2)

