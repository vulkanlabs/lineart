"""create initial schema

Revision ID: 001_create_initial_schema
Revises:
Create Date: 2025-10-30 00:00:00.000000

Creates all base tables for the Vulkan database schema.
This migration creates tables for policies, workflows, runs, data sources, and related entities.

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_create_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all base tables."""

    # Create enums
    workflow_status = postgresql.ENUM(
        "DRAFT", "PUBLISHED", name="workflowstatus", create_type=True
    )
    workflow_status.create(op.get_bind(), checkfirst=True)

    run_status = postgresql.ENUM(
        "PENDING",
        "QUEUED",
        "RUNNING",
        "SUCCESS",
        "FAILED",
        "CANCELLED",
        name="runstatus",
        create_type=True,
    )
    run_status.create(op.get_bind(), checkfirst=True)

    node_type = postgresql.ENUM(
        "FETCH",
        "TRANSFORM",
        "DECISION",
        "PARALLEL",
        "BRANCH",
        name="nodetype",
        create_type=True,
    )
    node_type.create(op.get_bind(), checkfirst=True)

    data_object_origin = postgresql.ENUM(
        "CACHE", "DATASOURCE", name="dataobjectorigin", create_type=True
    )
    data_object_origin.create(op.get_bind(), checkfirst=True)

    # Create log_record table
    op.create_table(
        "log_record",
        sa.Column(
            "log_record_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("level", sa.String(), nullable=True),
        sa.Column("message", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("log_record_id"),
    )

    # Create policy table
    op.create_table(
        "policy",
        sa.Column(
            "policy_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("allocation_strategy", sa.JSON(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
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
        sa.Column(
            "archived", sa.Boolean(), server_default=sa.text("false"), nullable=True
        ),
        sa.PrimaryKeyConstraint("policy_id"),
    )
    op.create_index("idx_policy_project_id", "policy", ["project_id"])

    # Create workflow table
    op.create_table(
        "workflow",
        sa.Column(
            "workflow_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.Column("requirements", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("variables", sa.ARRAY(sa.String()), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "DRAFT", "PUBLISHED", name="workflowstatus", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("ui_metadata", sa.JSON(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
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
        sa.PrimaryKeyConstraint("workflow_id"),
    )
    op.create_index("idx_workflow_project_id", "workflow", ["project_id"])

    # Create policy_version table (depends on policy and workflow)
    op.create_table(
        "policy_version",
        sa.Column(
            "policy_version_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("policy_id", sa.Uuid(), nullable=True),
        sa.Column("workflow_id", sa.Uuid(), nullable=True),
        sa.Column("alias", sa.String(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
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
        sa.Column(
            "archived", sa.Boolean(), server_default=sa.text("false"), nullable=True
        ),
        sa.ForeignKeyConstraint(["policy_id"], ["policy.policy_id"]),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflow.workflow_id"]),
        sa.PrimaryKeyConstraint("policy_version_id"),
    )
    op.create_index("idx_policy_version_project_id", "policy_version", ["project_id"])

    # Create configuration_value table (depends on policy_version)
    op.create_table(
        "configuration_value",
        sa.Column(
            "configuration_value_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("policy_version_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("nullable", sa.Boolean(), nullable=True),
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
        sa.CheckConstraint(
            "value IS NOT NULL OR nullable = TRUE", name="value_null_only_if_allowed"
        ),
        sa.ForeignKeyConstraint(
            ["policy_version_id"], ["policy_version.policy_version_id"]
        ),
        sa.PrimaryKeyConstraint("configuration_value_id"),
    )
    op.create_index(
        "unique_policy_version_name",
        "configuration_value",
        ["policy_version_id", "name"],
        unique=True,
    )

    # Create run_group table (depends on policy)
    op.create_table(
        "run_group",
        sa.Column(
            "run_group_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("policy_id", sa.Uuid(), nullable=True),
        sa.Column("input_data", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["policy_id"], ["policy.policy_id"]),
        sa.PrimaryKeyConstraint("run_group_id"),
    )

    # Create run table (depends on run_group and policy_version)
    op.create_table(
        "run",
        sa.Column(
            "run_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("run_group_id", sa.Uuid(), nullable=True),
        sa.Column("policy_version_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING",
                "QUEUED",
                "RUNNING",
                "SUCCESS",
                "FAILED",
                "CANCELLED",
                name="runstatus",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("result", sa.String(), nullable=True),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("run_metadata", sa.JSON(), nullable=True),
        sa.Column("backend_run_id", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
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
        sa.ForeignKeyConstraint(["run_group_id"], ["run_group.run_group_id"]),
        sa.ForeignKeyConstraint(
            ["policy_version_id"], ["policy_version.policy_version_id"]
        ),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index("idx_run_project_id", "run", ["project_id"])

    # Create step_metadata table (depends on run)
    op.create_table(
        "step_metadata",
        sa.Column(
            "step_metadata_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("step_name", sa.String(), nullable=True),
        sa.Column(
            "node_type",
            postgresql.ENUM(
                "FETCH",
                "TRANSFORM",
                "DECISION",
                "PARALLEL",
                "BRANCH",
                name="nodetype",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("start_time", sa.Float(), nullable=True),
        sa.Column("end_time", sa.Float(), nullable=True),
        sa.Column("error", sa.JSON(), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run.run_id"]),
        sa.PrimaryKeyConstraint("step_metadata_id"),
    )

    # Create data_source table (with archived column, not status - that comes in next migration)
    op.create_table(
        "data_source",
        sa.Column(
            "data_source_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("source", sa.JSON(), nullable=False),
        sa.Column("caching_enabled", sa.Boolean(), nullable=True),
        sa.Column("caching_ttl", sa.Integer(), nullable=True),
        sa.Column("config_metadata", sa.JSON(), nullable=True),
        sa.Column("runtime_params", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("variables", sa.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "archived", sa.Boolean(), server_default=sa.text("false"), nullable=True
        ),
        sa.Column("project_id", sa.Uuid(), nullable=True),
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
        sa.PrimaryKeyConstraint("data_source_id"),
    )
    # Create unique index for active data sources (archived=false)
    op.execute("""
        CREATE UNIQUE INDEX unique_data_source_name
        ON data_source (name, archived)
        WHERE archived = false
    """)
    op.create_index("idx_data_source_project_id", "data_source", ["project_id"])

    # Create data_source_env_var table (depends on data_source)
    op.create_table(
        "data_source_env_var",
        sa.Column(
            "data_source_env_var_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("data_source_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("nullable", sa.Boolean(), nullable=True),
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
        sa.CheckConstraint(
            "value IS NOT NULL OR nullable = TRUE", name="value_null_only_if_allowed"
        ),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_source.data_source_id"]),
        sa.PrimaryKeyConstraint("data_source_env_var_id"),
    )
    op.create_index(
        "unique_data_source_env_var_name",
        "data_source_env_var",
        ["data_source_id", "name"],
        unique=True,
    )

    # Create workflow_data_dependency table (depends on data_source and workflow)
    op.create_table(
        "workflow_data_dependency",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("data_source_id", sa.Uuid(), nullable=True),
        sa.Column("workflow_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_source.data_source_id"]),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflow.workflow_id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create data_object table (depends on data_source)
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
        sa.ForeignKeyConstraint(["data_source_id"], ["data_source.data_source_id"]),
        sa.PrimaryKeyConstraint("data_object_id"),
    )

    # Create run_data_cache table (depends on data_object)
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
        sa.ForeignKeyConstraint(["data_object_id"], ["data_object.data_object_id"]),
        sa.PrimaryKeyConstraint("key"),
    )

    # Create run_data_request table (depends on run, data_object, data_source)
    op.create_table(
        "run_data_request",
        sa.Column(
            "run_data_request_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("data_object_id", sa.Uuid(), nullable=True),
        sa.Column("data_source_id", sa.Uuid(), nullable=True),
        sa.Column(
            "data_origin",
            postgresql.ENUM(
                "CACHE", "DATASOURCE", name="dataobjectorigin", create_type=False
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("start_time", sa.Float(), nullable=True),
        sa.Column("end_time", sa.Float(), nullable=True),
        sa.Column("error", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run.run_id"]),
        sa.ForeignKeyConstraint(["data_object_id"], ["data_object.data_object_id"]),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_source.data_source_id"]),
        sa.PrimaryKeyConstraint("run_data_request_id"),
    )

    # Create component table (depends on workflow)
    op.create_table(
        "component",
        sa.Column(
            "component_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("workflow_id", sa.Uuid(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column(
            "archived", sa.Boolean(), server_default=sa.text("false"), nullable=True
        ),
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
        sa.ForeignKeyConstraint(["workflow_id"], ["workflow.workflow_id"]),
        sa.PrimaryKeyConstraint("component_id"),
    )
    # Create unique index for active components (archived=false)
    op.execute("""
        CREATE UNIQUE INDEX unique_component_name
        ON component (name, archived)
        WHERE archived = false
    """)
    op.create_index("idx_component_project_id", "component", ["project_id"])


def downgrade() -> None:
    """Drop all base tables."""

    # Drop tables in reverse order of creation (respecting foreign key constraints)
    op.drop_table("component")
    op.drop_table("run_data_request")
    op.drop_table("run_data_cache")
    op.drop_table("data_object")
    op.drop_table("workflow_data_dependency")
    op.drop_table("data_source_env_var")
    op.drop_table("data_source")
    op.drop_table("step_metadata")
    op.drop_table("run")
    op.drop_table("run_group")
    op.drop_table("configuration_value")
    op.drop_table("policy_version")
    op.drop_table("workflow")
    op.drop_table("policy")
    op.drop_table("log_record")

    # Drop enums
    data_object_origin = postgresql.ENUM(name="dataobjectorigin")
    data_object_origin.drop(op.get_bind())

    node_type = postgresql.ENUM(name="nodetype")
    node_type.drop(op.get_bind())

    run_status = postgresql.ENUM(name="runstatus")
    run_status.drop(op.get_bind())

    workflow_status = postgresql.ENUM(name="workflowstatus")
    workflow_status.drop(op.get_bind())
