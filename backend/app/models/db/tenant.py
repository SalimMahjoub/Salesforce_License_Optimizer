"""Tenant model for multi-tenancy support."""
from datetime import datetime
from uuid import uuid4
from typing import List

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tenant(Base):
    """
    Tenant/Client organization model.
    
    Represents a company using the Salesforce License Optimizer.
    Each tenant has their own Salesforce org and isolated data.
    """
    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sf_org_id: Mapped[str] = mapped_column(String(18), unique=True, nullable=True, index=True)
    sf_instance_url: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # OAuth tokens (encrypted)
    sf_access_token: Mapped[str] = mapped_column(String(500), nullable=True)
    sf_refresh_token: Mapped[str] = mapped_column(String(500), nullable=True)
    sf_token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
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
    sf_users: Mapped[List["SfUser"]] = relationship(
        "SfUser",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    security_alerts: Mapped[List["SecurityAlert"]] = relationship(
        "SecurityAlert",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    savings_tracking: Mapped[List["SavingsTracking"]] = relationship(
        "SavingsTracking",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', sf_org_id='{self.sf_org_id}')>"

