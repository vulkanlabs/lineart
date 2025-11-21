"""Remove data broker cache tables

Revision ID: 002_remove_broker_cache_tables
Revises: 001_initial_schema
Create Date: 2025-02-11
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_remove_broker_cache_tables"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "run_data_request_data_object_id_fkey",
        "run_data_request",
        type_="foreignkey",
    )
    op.drop_table("run_data_cache")
    op.drop_table("data_object")


def downgrade() -> None:
    op.create_table(
        "data_object",
        sa.Column(
            "data_object_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("data_source_id", sa.Uuid(), nullable=True),
        sa.Column("key", sa.String(), nullable=True),
        sa.Column("value", sa.LargeBinary(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["data_source_id"],
            ["data_source.data_source_id"],
        ),
        sa.PrimaryKeyConstraint("data_object_id"),
    )
    op.create_table(
        "run_data_cache",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("data_object_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["data_object_id"],
            ["data_object.data_object_id"],
        ),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_foreign_key(
        "run_data_request_data_object_id_fkey",
        "run_data_request",
        "data_object",
        ["data_object_id"],
        ["data_object_id"],
    )
