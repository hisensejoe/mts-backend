"""add booking requests

Revision ID: 20260308_0007
Revises: 20260308_0006
Create Date: 2026-03-08 00:35:00.000000
"""

from collections.abc import Sequence
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260308_0007"
down_revision: Optional[str] = "20260308_0006"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'booking_request_container_type') THEN
                CREATE TYPE booking_request_container_type AS ENUM (
                    '20ft_container',
                    '30ft_container',
                    '40ft_container',
                    'double_container'
                );
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'booking_request_status') THEN
                CREATE TYPE booking_request_status AS ENUM ('pending', 'confirmed', 'cancelled');
            END IF;
        END
        $$;
        """
    )

    container_type = postgresql.ENUM(
        "20ft_container",
        "30ft_container",
        "40ft_container",
        "double_container",
        name="booking_request_container_type",
        create_type=False,
    )
    booking_status = postgresql.ENUM(
        "pending",
        "confirmed",
        "cancelled",
        name="booking_request_status",
        create_type=False,
    )

    op.create_table(
        "booking_requests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pickup_location", sa.String(length=255), nullable=False),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("container_type", container_type, nullable=False),
        sa.Column("weight_tonnes", sa.Numeric(10, 2), nullable=True),
        sa.Column("preferred_pickup_date", sa.Date(), nullable=False),
        sa.Column("preferred_pickup_time", sa.Time(), nullable=True),
        sa.Column("delivery_address", sa.String(length=500), nullable=False),
        sa.Column("recipient_name", sa.String(length=255), nullable=False),
        sa.Column("recipient_phone", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", booking_status, server_default="pending", nullable=False),
        sa.Column("quoted_amount", sa.Numeric(12, 2), nullable=False),
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
            ["customer_id"],
            ["customers.id"],
            name=op.f("fk_booking_requests_customer_id_customers"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["users.id"],
            name=op.f("fk_booking_requests_requested_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["route_id"],
            ["routes.id"],
            name=op.f("fk_booking_requests_route_id_routes"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_booking_requests")),
    )
    op.create_index(
        op.f("ix_booking_requests_customer_id"),
        "booking_requests",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_booking_requests_requested_by_user_id"),
        "booking_requests",
        ["requested_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_booking_requests_route_id"),
        "booking_requests",
        ["route_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_booking_requests_status"),
        "booking_requests",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_booking_requests_status"), table_name="booking_requests")
    op.drop_index(op.f("ix_booking_requests_route_id"), table_name="booking_requests")
    op.drop_index(
        op.f("ix_booking_requests_requested_by_user_id"),
        table_name="booking_requests",
    )
    op.drop_index(
        op.f("ix_booking_requests_customer_id"), table_name="booking_requests"
    )
    op.drop_table("booking_requests")
    op.execute("DROP TYPE IF EXISTS booking_request_status")
    op.execute("DROP TYPE IF EXISTS booking_request_container_type")
