"""add expenses

Revision ID: 20260311_0009
Revises: 20260311_0008
Create Date: 2026-03-11 13:00:00.000000
"""

from collections.abc import Sequence
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260311_0009"
down_revision: Optional[str] = "20260311_0008"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'expense_type') THEN
                CREATE TYPE expense_type AS ENUM (
                    'fuel',
                    'per_diem',
                    'maintenance',
                    'toll'
                );
            END IF;
        END
        $$;
        """
    )

    expense_type = postgresql.ENUM(
        "fuel",
        "per_diem",
        "maintenance",
        "toll",
        name="expense_type",
        create_type=False,
    )

    op.create_table(
        "expenses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expense_type", expense_type, nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("expense_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vendor_name", sa.String(length=255), nullable=True),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
            ["driver_id"],
            ["drivers.id"],
            name=op.f("fk_expenses_driver_id_drivers"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by_user_id"],
            ["users.id"],
            name=op.f("fk_expenses_recorded_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            name=op.f("fk_expenses_trip_id_trips"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["vehicles.id"],
            name=op.f("fk_expenses_vehicle_id_vehicles"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expenses")),
    )
    op.create_index(op.f("ix_expenses_trip_id"), "expenses", ["trip_id"], unique=False)
    op.create_index(
        op.f("ix_expenses_vehicle_id"), "expenses", ["vehicle_id"], unique=False
    )
    op.create_index(
        op.f("ix_expenses_driver_id"), "expenses", ["driver_id"], unique=False
    )
    op.create_index(
        op.f("ix_expenses_recorded_by_user_id"),
        "expenses",
        ["recorded_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_expenses_expense_type"),
        "expenses",
        ["expense_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_expenses_expense_type"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_recorded_by_user_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_driver_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_vehicle_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_trip_id"), table_name="expenses")
    op.drop_table("expenses")
    op.execute("DROP TYPE IF EXISTS expense_type")
