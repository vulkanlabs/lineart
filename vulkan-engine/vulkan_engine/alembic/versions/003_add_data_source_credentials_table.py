"""add_data_source_credentials_table

Revision ID: 003
Revises: 002_add_datasource_status_column
Create Date: 2025-11-03 20:16:16.663184

Creates data_source_credential table to store authentication credentials
(CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD) separately from environment variables.

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
    """Create data_source_credential table."""

    op.create_table(
        "data_source_credential",
        sa.Column(
            "credential_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "data_source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("data_source.data_source_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("credential_type", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index(
        "unique_data_source_credential_type",
        "data_source_credential",
        ["data_source_id", "credential_type"],
        unique=True,
    )

    op.create_check_constraint(
        "valid_credential_type",
        "data_source_credential",
        "credential_type IN ('CLIENT_ID', 'CLIENT_SECRET', 'USERNAME', 'PASSWORD')",
    )


def downgrade() -> None:
    """Drop data_source_credential table."""

    op.drop_table("data_source_credential")
