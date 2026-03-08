"""add routes

Revision ID: 20260308_0006
Revises: 20260308_0005
Create Date: 2026-03-08 00:20:00.000000
"""

from collections.abc import Sequence
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260308_0006"
down_revision: Optional[str] = "20260308_0005"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'route_type') THEN
                CREATE TYPE route_type AS ENUM ('domestic', 'international');
            END IF;
        END
        $$;
        """
    )

    route_type = postgresql.ENUM(
        "domestic",
        "international",
        name="route_type",
        create_type=False,
    )

    op.create_table(
        "routes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("origin", sa.String(length=255), nullable=False),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("distance_km", sa.Integer(), nullable=False),
        sa.Column("route_type", route_type, server_default="domestic", nullable=False),
        sa.Column("price_20ft", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_30ft", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_40ft", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_double", sa.Numeric(12, 2), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_routes")),
        sa.UniqueConstraint("origin", "destination", name=op.f("uq_routes_origin")),
    )
    op.create_index(op.f("ix_routes_origin"), "routes", ["origin"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_routes_origin"), table_name="routes")
    op.drop_table("routes")
    op.execute("DROP TYPE IF EXISTS route_type")
