"""uuid primary keys

Revision ID: 20260307_0003
Revises: 20260307_0002
Create Date: 2026-03-07 23:35:00.000000
"""

from collections.abc import Sequence
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260307_0003"
down_revision: Optional[str] = "20260307_0002"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.add_column(
        "roles",
        sa.Column(
            "id_uuid",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "id_uuid",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "id_uuid",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
    )
    op.add_column("users", sa.Column("role_id_uuid", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("users", sa.Column("customer_id_uuid", postgresql.UUID(as_uuid=True), nullable=True))

    op.execute(
        """
        UPDATE users AS u
        SET role_id_uuid = r.id_uuid
        FROM roles AS r
        WHERE u.role_id = r.id
        """
    )
    op.execute(
        """
        UPDATE users AS u
        SET customer_id_uuid = c.id_uuid
        FROM customers AS c
        WHERE u.customer_id = c.id
        """
    )

    op.alter_column("users", "role_id_uuid", nullable=False)

    op.drop_constraint(op.f("fk_users_role_id_roles"), "users", type_="foreignkey")
    op.drop_constraint(op.f("fk_users_customer_id_customers"), "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_role_id"), table_name="users")
    op.drop_index(op.f("ix_users_customer_id"), table_name="users")

    op.drop_constraint(op.f("pk_users"), "users", type_="primary")
    op.drop_constraint(op.f("pk_roles"), "roles", type_="primary")
    op.drop_constraint(op.f("pk_customers"), "customers", type_="primary")

    op.drop_column("users", "role_id")
    op.drop_column("users", "customer_id")
    op.drop_column("users", "id")
    op.drop_column("roles", "id")
    op.drop_column("customers", "id")

    op.alter_column("users", "id_uuid", new_column_name="id")
    op.alter_column("users", "role_id_uuid", new_column_name="role_id")
    op.alter_column("users", "customer_id_uuid", new_column_name="customer_id")
    op.alter_column("roles", "id_uuid", new_column_name="id")
    op.alter_column("customers", "id_uuid", new_column_name="id")

    op.create_primary_key(op.f("pk_roles"), "roles", ["id"])
    op.create_primary_key(op.f("pk_customers"), "customers", ["id"])
    op.create_primary_key(op.f("pk_users"), "users", ["id"])

    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"], unique=False)
    op.create_index(op.f("ix_users_customer_id"), "users", ["customer_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_users_role_id_roles"),
        "users",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        op.f("fk_users_customer_id_customers"),
        "users",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    raise NotImplementedError("Downgrade for UUID primary key migration is not supported.")
