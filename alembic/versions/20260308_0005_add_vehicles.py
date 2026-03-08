"""add vehicles

Revision ID: 20260308_0005
Revises: 20260307_0004
Create Date: 2026-03-08 00:05:00.000000
"""

from collections.abc import Sequence
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260308_0005"
down_revision: Optional[str] = "20260307_0004"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vehicle_status') THEN
                CREATE TYPE vehicle_status AS ENUM ('available', 'on_trip', 'maintenance', 'inactive');
            END IF;
        END
        $$;
        """
    )

    vehicle_status = postgresql.ENUM(
        "available",
        "on_trip",
        "maintenance",
        "inactive",
        name="vehicle_status",
        create_type=False,
    )

    op.create_table(
        "vehicles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("registration_number", sa.String(length=50), nullable=False),
        sa.Column("make", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("manufacture_year", sa.Integer(), nullable=False),
        sa.Column("body_type", sa.String(length=100), nullable=False),
        sa.Column("fuel_type", sa.String(length=50), nullable=False),
        sa.Column("odometer_km", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", vehicle_status, server_default="available", nullable=False),
        sa.Column("assigned_driver_id", postgresql.UUID(as_uuid=True), nullable=True),
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
            ["assigned_driver_id"],
            ["drivers.id"],
            name=op.f("fk_vehicles_assigned_driver_id_drivers"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vehicles")),
    )
    op.create_index(
        op.f("ix_vehicles_registration_number"),
        "vehicles",
        ["registration_number"],
        unique=True,
    )
    op.create_index(
        op.f("ix_vehicles_assigned_driver_id"),
        "vehicles",
        ["assigned_driver_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_vehicles_assigned_driver_id"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_registration_number"), table_name="vehicles")
    op.drop_table("vehicles")
    op.execute("DROP TYPE IF EXISTS vehicle_status")
