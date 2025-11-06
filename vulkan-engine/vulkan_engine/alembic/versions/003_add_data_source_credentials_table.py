"""add_data_source_credentials_table

Revision ID: 003
Revises: 002_add_datasource_status_column
Create Date: 2025-11-05 20:02:46.579966

Adds data_source_credential table for storing authentication credentials
separately from environment variables.

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002_add_datasource_status_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add data_source_credential table with Enum type."""

    credential_type_enum = postgresql.ENUM(
        "CLIENT_ID", "CLIENT_SECRET", "USERNAME", "PASSWORD", name="credentialtype"
    )
    credential_type_enum.create(op.get_bind())

    # Create data_source_credential table
    op.create_table(
        "data_source_credential",
        sa.Column(
            "credential_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "data_source_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "credential_type",
            sa.Enum(
                "CLIENT_ID",
                "CLIENT_SECRET",
                "USERNAME",
                "PASSWORD",
                name="credentialtype",
            ),
            nullable=False,
        ),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "last_updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["data_source_id"],
            ["data_source.data_source_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("credential_id"),
    )

    # Create unique index for data_source_id + credential_type
    op.create_index(
        "unique_data_source_credential_type",
        "data_source_credential",
        ["data_source_id", "credential_type"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema: drop data_source_credential table and enum."""

    op.drop_index(
        "unique_data_source_credential_type",
        table_name="data_source_credential",
    )

    op.drop_table("data_source_credential")

    credential_type_enum = postgresql.ENUM(
        "CLIENT_ID", "CLIENT_SECRET", "USERNAME", "PASSWORD", name="credentialtype"
    )
    credential_type_enum.drop(op.get_bind())
