"""Recommendation model for license optimization suggestions."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, func, Numeric, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class RecommendationAction(enum.Enum):
    """Types of recommendations."""
    DEACTIVATE = "deactivate"
    DOWNGRADE = "downgrade"
    KEEP = "keep"
    UPGRADE = "upgrade"


class RecommendationStatus(enum.Enum):
    """Status of recommendation implementation."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class RiskLevel(enum.Enum):
    """Risk level of implementing recommendation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Recommendation(Base):
    """
    Recommendation model.
    
    Stores license optimization recommendations for users.
    Tracks savings potential and implementation status.
    """
    __tablename__ = "recommendations"
    __table_args__ = (
        Index('idx_recommendation_tenant', 'tenant_id'),
        Index('idx_recommendation_status', 'status'),
        Index('idx_recommendation_savings', 'annual_savings'),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sf_user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sf_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # License information
    current_license: Mapped[str] = mapped_column(String(100), nullable=False)
    recommended_license: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action: Mapped[RecommendationAction] = mapped_column(
        SQLEnum(RecommendationAction),
        nullable=False
    )
    
    # Financial impact
    monthly_savings: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )
    annual_savings: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )
    
    # Risk assessment
    risk_level: Mapped[RiskLevel] = mapped_column(
        SQLEnum(RiskLevel),
        nullable=False,
        default=RiskLevel.LOW
    )
    
    # Justification and metadata
    justification: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    confidence_score: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Status tracking
    status: Mapped[RecommendationStatus] = mapped_column(
        SQLEnum(RecommendationStatus),
        nullable=False,
        default=RecommendationStatus.PENDING
    )
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    implemented_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="recommendations")
    sf_user: Mapped["SfUser"] = relationship("SfUser", back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, action={self.action.value}, savings={self.annual_savings})>"

