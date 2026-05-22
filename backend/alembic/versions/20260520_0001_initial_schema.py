"""Initial schema: tenants, sf_users, usage_metrics, recommendations, security_alerts, savings_tracking.

Revision ID: 20260520_0001
Revises:
Create Date: 2026-05-20
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260520_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- tenants ---------------------------------------------------------
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sf_org_id", sa.String(18), unique=True, nullable=True),
        sa.Column("sf_instance_url", sa.String(255), nullable=True),
        sa.Column("sf_access_token", sa.String(500), nullable=True),
        sa.Column("sf_refresh_token", sa.String(500), nullable=True),
        sa.Column("sf_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tenants_id", "tenants", ["id"])
    op.create_index("ix_tenants_sf_org_id", "tenants", ["sf_org_id"])

    # --- sf_users --------------------------------------------------------
    op.create_table(
        "sf_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sf_user_id", sa.String(18), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("license_type", sa.String(100), nullable=False),
        sa.Column("profile_name", sa.String(255), nullable=False),
        sa.Column("last_login_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sf_users_tenant_id", "sf_users", ["tenant_id"])
    op.create_index("idx_sf_user_tenant_sfid", "sf_users", ["tenant_id", "sf_user_id"])
    op.create_index("idx_sf_user_license", "sf_users", ["license_type"])
    op.create_index("idx_sf_user_last_login", "sf_users", ["last_login_date"])

    # --- usage_metrics ---------------------------------------------------
    op.create_table(
        "usage_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sf_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sf_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("login_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("features_used", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("records_created", sa.Integer, nullable=False, server_default="0"),
        sa.Column("records_modified", sa.Integer, nullable=False, server_default="0"),
        sa.Column("score", sa.Integer, nullable=True),
        sa.Column("category", sa.String(20), nullable=True),
        sa.Column("score_last_login", sa.Integer, nullable=True),
        sa.Column("score_frequency", sa.Integer, nullable=True),
        sa.Column("score_features", sa.Integer, nullable=True),
        sa.Column("score_records", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="score_range_check"),
    )
    op.create_index("ix_usage_metrics_sf_user_id", "usage_metrics", ["sf_user_id"])
    op.create_index("idx_usage_metric_user_period", "usage_metrics",
                    ["sf_user_id", "period_start"])
    op.create_index("idx_usage_metric_category", "usage_metrics", ["category"])

    # --- recommendations -------------------------------------------------
    recommendation_action = sa.Enum(
        "DEACTIVATE", "DOWNGRADE", "KEEP", "UPGRADE",
        name="recommendationaction",
    )
    recommendation_status = sa.Enum(
        "PENDING", "APPROVED", "REJECTED", "IMPLEMENTED",
        name="recommendationstatus",
    )
    risk_level = sa.Enum("LOW", "MEDIUM", "HIGH", name="risklevel")
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sf_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sf_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("current_license", sa.String(100), nullable=False),
        sa.Column("recommended_license", sa.String(100), nullable=True),
        sa.Column("action", recommendation_action, nullable=False),
        sa.Column("monthly_savings", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("annual_savings", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("risk_level", risk_level, nullable=False, server_default="LOW"),
        sa.Column("justification", sa.String(1000), nullable=True),
        sa.Column("confidence_score", sa.Integer, nullable=True),
        sa.Column("status", recommendation_status, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("implemented_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_recommendation_tenant", "recommendations", ["tenant_id"])
    op.create_index("idx_recommendation_status", "recommendations", ["status"])
    op.create_index("idx_recommendation_savings", "recommendations", ["annual_savings"])

    # --- security_alerts -------------------------------------------------
    alert_type = sa.Enum("CRITICAL", "HIGH", "MEDIUM", "LOW", name="alerttype")
    alert_status = sa.Enum(
        "OPEN", "ACKNOWLEDGED", "RESOLVED", "FALSE_POSITIVE",
        name="alertstatus",
    )
    op.create_table(
        "security_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_type", alert_type, nullable=False),
        sa.Column("permission", sa.String(100), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sf_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("recommended_action", sa.Text, nullable=False),
        sa.Column("status", alert_status, nullable=False, server_default="OPEN"),
        sa.Column("detected_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_security_alert_tenant", "security_alerts", ["tenant_id"])
    op.create_index("idx_security_alert_type", "security_alerts", ["alert_type"])
    op.create_index("idx_security_alert_status", "security_alerts", ["status"])
    op.create_index("idx_security_alert_detected", "security_alerts", ["detected_at"])

    # --- savings_tracking ------------------------------------------------
    op.create_table(
        "savings_tracking",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.Date, nullable=False),
        sa.Column("baseline_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("current_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("savings", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("commission_rate", sa.Numeric(4, 2), nullable=False, server_default="0.30"),
        sa.Column("commission_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_savings_tracking_tenant_month", "savings_tracking",
                    ["tenant_id", "month"], unique=True)


def downgrade() -> None:
    op.drop_table("savings_tracking")
    op.drop_table("security_alerts")
    op.execute("DROP TYPE IF EXISTS alertstatus")
    op.execute("DROP TYPE IF EXISTS alerttype")
    op.drop_table("recommendations")
    op.execute("DROP TYPE IF EXISTS recommendationstatus")
    op.execute("DROP TYPE IF EXISTS recommendationaction")
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.drop_table("usage_metrics")
    op.drop_table("sf_users")
    op.drop_table("tenants")
