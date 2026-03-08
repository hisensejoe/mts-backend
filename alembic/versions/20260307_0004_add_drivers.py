"""add drivers

Revision ID: 20260307_0004
Revises: 20260307_0003
Create Date: 2026-03-07 23:55:00.000000
"""

from collections.abc import Sequence
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260307_0004"
down_revision: Optional[str] = "20260307_0003"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'driver_status') THEN
                CREATE TYPE driver_status AS ENUM ('available', 'on_trip', 'inactive');
            END IF;
        END
        $$;
        """
    )

    driver_status = postgresql.ENUM(
        "available",
        "on_trip",
        "inactive",
        name="driver_status",
        create_type=False,
    )

    op.create_table(
        "drivers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("license_number", sa.String(length=100), nullable=False),
        sa.Column("trip_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("per_diem", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", driver_status, server_default="available", nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_drivers")),
    )
    op.create_index(op.f("ix_drivers_full_name"), "drivers", ["full_name"], unique=False)
    op.create_index(op.f("ix_drivers_phone"), "drivers", ["phone"], unique=True)
    op.create_index(
        op.f("ix_drivers_license_number"),
        "drivers",
        ["license_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_drivers_license_number"), table_name="drivers")
    op.drop_index(op.f("ix_drivers_phone"), table_name="drivers")
    op.drop_index(op.f("ix_drivers_full_name"), table_name="drivers")
    op.drop_table("drivers")
    op.execute("DROP TYPE IF EXISTS driver_status")
