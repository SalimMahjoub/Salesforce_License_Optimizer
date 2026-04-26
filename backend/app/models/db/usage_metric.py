"""Usage Metrics model for tracking user activity."""
from datetime import date, datetime
from uuid import uuid4
from typing import Optional

from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, func, ARRAY, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UsageMetric(Base):
    """
    Usage Metrics model.
    
    Stores aggregated usage statistics for a user during a specific period.
    Used for calculating user scores and classifications.
    """
    __tablename__ = "usage_metrics"
    __table_args__ = (
        CheckConstraint('score >= 0 AND score <= 100', name='score_range_check'),
        Index('idx_usage_metric_user_period', 'sf_user_id', 'period_start'),
        Index('idx_usage_metric_category', 'category'),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    sf_user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sf_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Period
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Usage statistics
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    features_used: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_modified: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Classification results
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Score breakdown for explainability
    score_last_login: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score_frequency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score_features: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score_records: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    sf_user: Mapped["SfUser"] = relationship("SfUser", back_populates="usage_metrics")

    def __repr__(self) -> str:
        return f"<UsageMetric(user_id={self.sf_user_id}, score={self.score}, category='{self.category}')>"

