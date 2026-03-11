"""add trips

Revision ID: 20260311_0008
Revises: 20260308_0008
Create Date: 2026-03-11 12:00:00.000000
"""

from collections.abc import Sequence
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260311_0008"
down_revision: Optional[str] = "20260308_0008"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'trip_status') THEN
                CREATE TYPE trip_status AS ENUM (
                    'scheduled',
                    'in_progress',
                    'completed',
                    'cancelled'
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
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'trip_milestone_status') THEN
                CREATE TYPE trip_milestone_status AS ENUM (
                    'depart_base',
                    'enter_port',
                    'load_container',
                    'gate_out',
                    'in_transit',
                    'arrive_at_customer',
                    'start_offload',
                    'finish_offload',
                    'start_return',
                    'drop_container',
                    'back_at_base',
                    'cancelled'
                );
            END IF;
        END
        $$;
        """
    )

    trip_status = postgresql.ENUM(
        "scheduled",
        "in_progress",
        "completed",
        "cancelled",
        name="trip_status",
        create_type=False,
    )
    trip_milestone_status = postgresql.ENUM(
        "depart_base",
        "enter_port",
        "load_container",
        "gate_out",
        "in_transit",
        "arrive_at_customer",
        "start_offload",
        "finish_offload",
        "start_return",
        "drop_container",
        "back_at_base",
        "cancelled",
        name="trip_milestone_status",
        create_type=False,
    )

    op.create_table(
        "trips",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("booking_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trip_reference", sa.String(length=50), nullable=False),
        sa.Column("waybill_number", sa.String(length=100), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_vehicle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "container_type",
            postgresql.ENUM(
                "20ft_container",
                "30ft_container",
                "40ft_container",
                "double_container",
                name="booking_request_container_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("cargo_description", sa.Text(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("planned_pickup_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivery_address", sa.String(length=500), nullable=False),
        sa.Column("delivery_contact_name", sa.String(length=255), nullable=False),
        sa.Column("delivery_contact_phone", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", trip_status, server_default="scheduled", nullable=False),
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
            name=op.f("fk_trips_assigned_driver_id_drivers"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_vehicle_id"],
            ["vehicles.id"],
            name=op.f("fk_trips_assigned_vehicle_id_vehicles"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["booking_request_id"],
            ["booking_requests.id"],
            name=op.f("fk_trips_booking_request_id_booking_requests"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_trips_created_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name=op.f("fk_trips_customer_id_customers"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["route_id"],
            ["routes.id"],
            name=op.f("fk_trips_route_id_routes"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trips")),
    )
    op.create_index(
        op.f("ix_trips_assigned_driver_id"),
        "trips",
        ["assigned_driver_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trips_assigned_vehicle_id"),
        "trips",
        ["assigned_vehicle_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trips_booking_request_id"),
        "trips",
        ["booking_request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trips_created_by_user_id"),
        "trips",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trips_customer_id"),
        "trips",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trips_route_id"),
        "trips",
        ["route_id"],
        unique=False,
    )
    op.create_index(op.f("ix_trips_status"), "trips", ["status"], unique=False)
    op.create_index(
        op.f("ix_trips_trip_reference"),
        "trips",
        ["trip_reference"],
        unique=True,
    )

    op.create_table(
        "trip_milestones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", trip_milestone_status, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
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
            ["recorded_by_user_id"],
            ["users.id"],
            name=op.f("fk_trip_milestones_recorded_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            name=op.f("fk_trip_milestones_trip_id_trips"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trip_milestones")),
    )
    op.create_index(
        op.f("ix_trip_milestones_recorded_by_user_id"),
        "trip_milestones",
        ["recorded_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trip_milestones_status"),
        "trip_milestones",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trip_milestones_trip_id"),
        "trip_milestones",
        ["trip_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_trip_milestones_trip_id"),
        table_name="trip_milestones",
    )
    op.drop_index(
        op.f("ix_trip_milestones_status"),
        table_name="trip_milestones",
    )
    op.drop_index(
        op.f("ix_trip_milestones_recorded_by_user_id"),
        table_name="trip_milestones",
    )
    op.drop_table("trip_milestones")

    op.drop_index(op.f("ix_trips_trip_reference"), table_name="trips")
    op.drop_index(op.f("ix_trips_status"), table_name="trips")
    op.drop_index(op.f("ix_trips_route_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_customer_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_created_by_user_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_booking_request_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_assigned_vehicle_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_assigned_driver_id"), table_name="trips")
    op.drop_table("trips")

    op.execute("DROP TYPE IF EXISTS trip_milestone_status")
    op.execute("DROP TYPE IF EXISTS trip_status")
