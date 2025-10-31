"""add_datasource_status_column

Revision ID: fb1d7ee648fd
Revises:
Create Date: 2025-10-29 18:42:10.814748

Migrates DataSource table from archived (Boolean) to status (Enum).
Also adds data_source_test_result table and updates indexes.

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_add_datasource_status_column"
down_revision: Union[str, Sequence[str], None] = "001_create_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: migrate DataSource from archived to status column."""

    # Create the DataSourceStatus enum type
    datasource_status = postgresql.ENUM(
        "DRAFT", "PUBLISHED", "ARCHIVED", name="datasourcestatus"
    )
    datasource_status.create(op.get_bind())

    # Add status column (nullable initially to allow data migration)
    op.add_column(
        "data_source",
        sa.Column(
            "status",
            sa.Enum("DRAFT", "PUBLISHED", "ARCHIVED", name="datasourcestatus"),
            nullable=True,
            server_default="DRAFT",
        ),
    )

    # Migrate existing data: archived=false -> status='PUBLISHED', archived=true -> status='ARCHIVED'
    op.execute("""
        UPDATE data_source
        SET status = CASE
            WHEN archived = false THEN 'PUBLISHED'::datasourcestatus
            WHEN archived = true THEN 'ARCHIVED'::datasourcestatus
        END
    """)

    # Make status column NOT NULL now that data is migrated
    op.alter_column("data_source", "status", nullable=False)

    # Drop the old unique constraint (if it exists as a constraint)
    # Note: This was created as a unique index, so we'll drop the index below

    # Drop old indexes
    op.drop_index("unique_data_source_name", table_name="data_source")
    op.drop_index("idx_data_source_project_id", table_name="data_source")

    # Drop the archived column
    op.drop_column("data_source", "archived")

    # Create new unique index with status condition
    op.execute("""
        CREATE UNIQUE INDEX unique_data_source_name
        ON data_source (name)
        WHERE status != 'ARCHIVED'::datasourcestatus
    """)

    # Create new indexes
    op.create_index("idx_data_source_status", "data_source", ["status"])
    op.create_index(
        "idx_data_source_project_status", "data_source", ["project_id", "status"]
    )

    # Create data_source_test_result table
    op.create_table(
        "data_source_test_result",
        sa.Column(
            "test_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("request", sa.JSON(), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("test_id"),
    )


def downgrade() -> None:
    """Downgrade schema: revert DataSource from status to archived column."""

    # Drop data_source_test_result table
    op.drop_table("data_source_test_result")

    # Drop new indexes
    op.drop_index("idx_data_source_project_status", table_name="data_source")
    op.drop_index("idx_data_source_status", table_name="data_source")
    op.drop_index("unique_data_source_name", table_name="data_source")

    # Add back archived column
    op.add_column(
        "data_source",
        sa.Column(
            "archived", sa.Boolean(), nullable=True, server_default=sa.text("false")
        ),
    )

    # Migrate data back: status -> archived
    op.execute("""
        UPDATE data_source
        SET archived = CASE
            WHEN status = 'ARCHIVED'::datasourcestatus THEN true
            ELSE false
        END
    """)

    # Make archived column NOT NULL
    op.alter_column("data_source", "archived", nullable=False)

    # Drop status column
    op.drop_column("data_source", "status")

    # Drop the enum type
    datasource_status = postgresql.ENUM(
        "DRAFT", "PUBLISHED", "ARCHIVED", name="datasourcestatus"
    )
    datasource_status.drop(op.get_bind())

    # Recreate old unique constraint with archived condition
    op.execute("""
        CREATE UNIQUE INDEX unique_data_source_name
        ON data_source (name, archived)
        WHERE archived = false
    """)

    # Recreate old index
    op.create_index("idx_data_source_project_id", "data_source", ["project_id"])
