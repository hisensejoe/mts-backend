"""add auth otp challenges

Revision ID: 20260308_0008
Revises: 20260308_0007
Create Date: 2026-03-08 21:50:00.000000
"""

from collections.abc import Sequence
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260308_0008"
down_revision: Optional[str] = "20260308_0007"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.create_table(
        "auth_otp_challenges",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_auth_otp_challenges_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_otp_challenges")),
    )
    op.create_index(
        op.f("ix_auth_otp_challenges_user_id"),
        "auth_otp_challenges",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_otp_challenges_phone"),
        "auth_otp_challenges",
        ["phone"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_auth_otp_challenges_phone"),
        table_name="auth_otp_challenges",
    )
    op.drop_index(
        op.f("ix_auth_otp_challenges_user_id"),
        table_name="auth_otp_challenges",
    )
    op.drop_table("auth_otp_challenges")
