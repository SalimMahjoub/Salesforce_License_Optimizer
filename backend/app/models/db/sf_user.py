"""Salesforce User model."""
from datetime import datetime
from uuid import uuid4
from typing import Optional, List

from sqlalchemy import String, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SfUser(Base):
    """
    Salesforce User model.
    
    Stores information about Salesforce users from the User API.
    Tracks license type, profile, and last login for analysis.
    """
    __tablename__ = "sf_users"
    __table_args__ = (
        Index('idx_sf_user_tenant_sfid', 'tenant_id', 'sf_user_id'),
        Index('idx_sf_user_license', 'license_type'),
        Index('idx_sf_user_last_login', 'last_login_date'),
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
    
    # Salesforce User fields
    sf_user_id: Mapped[str] = mapped_column(String(18), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    license_type: Mapped[str] = mapped_column(String(100), nullable=False)
    profile_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_login_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="sf_users")
    usage_metrics: Mapped[List["UsageMetric"]] = relationship(
        "UsageMetric",
        back_populates="sf_user",
        cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="sf_user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SfUser(id={self.id}, username='{self.username}', license='{self.license_type}')>"

