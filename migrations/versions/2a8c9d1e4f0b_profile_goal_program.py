"""profile goal_code and assigned_program

Revision ID: 2a8c9d1e4f0b
Revises: 1c0ffd4bab5f
Create Date: 2026-04-21

SQLite: колонки без FK (ограничение движка batch-режима); PostgreSQL — с внешним ключом.

"""
from alembic import op
import sqlalchemy as sa


revision = "2a8c9d1e4f0b"
down_revision = "1c0ffd4bab5f"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("user_profiles", schema=None) as batch_op:
            batch_op.add_column(sa.Column("goal_code", sa.String(length=32), nullable=True))
            batch_op.add_column(sa.Column("assigned_program_id", sa.Integer(), nullable=True))
    else:
        op.add_column("user_profiles", sa.Column("goal_code", sa.String(length=32), nullable=True))
        op.add_column("user_profiles", sa.Column("assigned_program_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_user_profiles_assigned_program_id",
            "user_profiles",
            "training_programs",
            ["assigned_program_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("user_profiles", schema=None) as batch_op:
            batch_op.drop_column("assigned_program_id")
            batch_op.drop_column("goal_code")
    else:
        op.drop_constraint("fk_user_profiles_assigned_program_id", "user_profiles", type_="foreignkey")
        op.drop_column("user_profiles", "assigned_program_id")
        op.drop_column("user_profiles", "goal_code")
