"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-14
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("tax_code", sa.String(20), unique=True),
        sa.Column("type", sa.Enum("broker", "law_firm", "bank", "individual", name="org_type"), nullable=False),
        sa.Column("tier", sa.Enum("trial", "standard", "enterprise", name="org_tier"), nullable=False),
        sa.Column("contact_email", sa.String(255)),
        sa.Column("contact_phone", sa.String(40)),
    )

    op.create_table(
        "user",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("organization_id", sa.String(40), sa.ForeignKey("organization.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("owner", "admin", "analyst", "viewer", name="user_role"), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("mfa_secret", sa.String(64)),
    )
    op.create_index("ix_user_organization_id", "user", ["organization_id"])

    op.create_table(
        "api_key",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("organization_id", sa.String(40), sa.ForeignKey("organization.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("key_prefix", sa.String(32), nullable=False),
        sa.Column("key_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("scopes", sa.String(500), nullable=False),
    )
    op.create_index("ix_api_key_organization_id", "api_key", ["organization_id"])
    op.create_index("ix_api_key_key_prefix", "api_key", ["key_prefix"])

    op.create_table(
        "certificate",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("organization_id", sa.String(40), sa.ForeignKey("organization.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_key", sa.String(500), nullable=False),
        sa.Column("file_sha256", sa.String(64), nullable=False),
        sa.Column("file_size", sa.BigInteger, nullable=False),
        sa.Column("mime_type", sa.String(80), nullable=False),
        sa.Column("ocr_engine", sa.String(40)),
        sa.Column("ocr_confidence", sa.Numeric(5, 4)),
        sa.Column("ocr_raw_text", sa.Text),
        sa.Column("ocr_completed_at", sa.String(40)),
        sa.Column(
            "form",
            sa.Enum(
                "so_do_1993", "so_hong_1995", "unified_2009", "unified_2024", "unknown",
                name="certificate_form",
            ),
            nullable=False,
        ),
        sa.Column("serial_number_enc", sa.Text),
        sa.Column("book_number_enc", sa.Text),
        sa.Column("issued_at", sa.String(20)),
        sa.Column("issued_by", sa.String(200)),
        sa.Column("owner_name_enc", sa.Text),
        sa.Column("owner_id_enc", sa.Text),
        sa.Column("parcel_number", sa.String(40)),
        sa.Column("sheet_number", sa.String(40)),
        sa.Column("area_sqm", sa.Numeric(14, 2)),
        sa.Column("land_use_purpose", sa.String(200)),
        sa.Column("land_use_term", sa.String(120)),
        sa.Column("address", sa.String(500)),
        sa.Column("ward", sa.String(120)),
        sa.Column("district", sa.String(120)),
        sa.Column("province", sa.String(120)),
        sa.Column("extra", sa.JSON),
    )
    op.create_index("ix_certificate_organization_id", "certificate", ["organization_id"])
    op.create_index("ix_certificate_file_sha256", "certificate", ["file_sha256"])
    op.create_index("ix_certificate_parcel_number", "certificate", ["parcel_number"])
    op.create_index("ix_certificate_sheet_number", "certificate", ["sheet_number"])

    op.create_table(
        "due_diligence_job",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("organization_id", sa.String(40), sa.ForeignKey("organization.id", ondelete="CASCADE"), nullable=False),
        sa.Column("certificate_id", sa.String(40), sa.ForeignKey("certificate.id", ondelete="SET NULL")),
        sa.Column("api_key_id", sa.String(40), sa.ForeignKey("api_key.id", ondelete="SET NULL")),
        sa.Column(
            "status",
            sa.Enum(
                "queued", "ocr", "verifying", "zoning", "history",
                "scoring", "rendering", "completed", "failed", "cancelled",
                name="job_status",
            ),
            nullable=False,
        ),
        sa.Column("options", sa.JSON, nullable=False),
        sa.Column("progress_pct", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(80)),
        sa.Column("error_detail", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("callback_url", sa.String(500)),
    )
    op.create_index("ix_dd_job_org", "due_diligence_job", ["organization_id"])
    op.create_index("ix_dd_job_status", "due_diligence_job", ["status"])

    op.create_table(
        "due_diligence_report",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("job_id", sa.String(40), sa.ForeignKey("due_diligence_job.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("risk_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("risk_level", sa.Enum("low", "medium", "high", "critical", name="risk_level"), nullable=False),
        sa.Column("red_flags", sa.JSON, nullable=False),
        sa.Column("findings", sa.JSON, nullable=False),
        sa.Column("sources", sa.JSON, nullable=False),
        sa.Column("pdf_key", sa.String(500)),
        sa.Column("pdf_sha256", sa.String(64)),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("organization_id", sa.String(40), sa.ForeignKey("organization.id", ondelete="SET NULL")),
        sa.Column("actor_id", sa.String(40)),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("resource_type", sa.String(40)),
        sa.Column("resource_id", sa.String(40)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(255)),
        sa.Column("metadata_json", sa.JSON),
    )
    op.create_index("ix_audit_org", "audit_log", ["organization_id"])
    op.create_index("ix_audit_actor", "audit_log", ["actor_id"])
    op.create_index("ix_audit_action", "audit_log", ["action"])
    op.create_index("ix_audit_resource", "audit_log", ["resource_type", "resource_id"])

    op.create_table(
        "webhook_endpoint",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("organization_id", sa.String(40), sa.ForeignKey("organization.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("secret", sa.String(128), nullable=False),
        sa.Column("events", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_webhook_org", "webhook_endpoint", ["organization_id"])


def downgrade() -> None:
    for t in [
        "webhook_endpoint", "audit_log", "due_diligence_report", "due_diligence_job",
        "certificate", "api_key", "user", "organization",
    ]:
        op.drop_table(t)
    for enum in ["org_type", "org_tier", "user_role", "certificate_form", "job_status", "risk_level"]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
