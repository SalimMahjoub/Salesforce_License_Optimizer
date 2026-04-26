"""Savings Tracking model for ROI calculation."""
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from enum import Enum

from sqlalchemy import Date, DateTime, ForeignKey, func, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OptimizationAction(str, Enum):
    """Types of optimization actions that generate savings."""
    DEACTIVATE = "DEACTIVATE"
    DOWNGRADE = "DOWNGRADE"
    OPTIMIZE = "OPTIMIZE"
    KEEP = "KEEP"


class SavingsTracking(Base):
    """
    Savings Tracking model.
    
    Tracks monthly savings and calculates commission for billing.
    Used for ROI reporting and customer success metrics.
    """
    __tablename__ = "savings_tracking"
    __table_args__ = (
        Index('idx_savings_tracking_tenant_month', 'tenant_id', 'month', unique=True),
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
    
    # Period
    month: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Cost tracking
    baseline_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )
    current_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )
    savings: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )
    
    # Commission calculation
    commission_rate: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("0.30")  # 30% default
    )
    commission_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="savings_tracking")

    def __repr__(self) -> str:
        return f"<SavingsTracking(tenant_id={self.tenant_id}, month={self.month}, savings={self.savings})>"

