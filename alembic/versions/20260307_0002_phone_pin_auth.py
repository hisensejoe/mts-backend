"""phone pin auth and customers

Revision ID: 20260307_0002
Revises: 20260307_0001
Create Date: 2026-03-07 23:15:00.000000
"""

from collections.abc import Sequence
from typing import Optional

from alembic import op
import sqlalchemy as sa


revision: str = "20260307_0002"
down_revision: Optional[str] = "20260307_0001"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    bind = op.get_bind()
    user_status = sa.Enum("active", "inactive", "locked", name="user_status")
    user_status.create(bind, checkfirst=True)

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customers")),
    )
    op.create_index(op.f("ix_customers_company_name"), "customers", ["company_name"], unique=True)

    op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("pin_hash", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("status", user_status, nullable=True))
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("customer_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_users_customer_id_customers"),
        "users",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_users_customer_id"), "users", ["customer_id"], unique=False)

    op.execute(
        "UPDATE users "
        "SET status = CASE "
        "WHEN is_active THEN 'active'::user_status "
        "ELSE 'inactive'::user_status "
        "END"
    )

    op.alter_column("users", "status", server_default="active", nullable=False)
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_column("users", "email")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "is_active")


def downgrade() -> None:
    op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False))
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.drop_index(op.f("ix_users_phone"), table_name="users")
    op.drop_index(op.f("ix_users_customer_id"), table_name="users")
    op.drop_constraint(op.f("fk_users_customer_id_customers"), "users", type_="foreignkey")
    op.drop_column("users", "customer_id")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
    op.drop_column("users", "status")
    op.drop_column("users", "pin_hash")
    op.drop_column("users", "phone")

    op.drop_index(op.f("ix_customers_company_name"), table_name="customers")
    op.drop_table("customers")
    sa.Enum(name="user_status").drop(op.get_bind(), checkfirst=True)
