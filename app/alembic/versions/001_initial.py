"""consolidated initial

Revision ID: 001_initial
Revises:
Create Date: 2026-04-09 16:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users table ---
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # --- database_connections table ---
    op.create_table(
        'database_connections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('db_name', sa.String(length=100), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('encrypted_password', sa.String(length=1000), nullable=False),
        sa.Column('blocked_tables', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_database_connections_user_id'), 'database_connections', ['user_id'], unique=False)

    # --- mdl_schemas table ---
    op.create_table(
        'mdl_schemas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('database_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('schema_json', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_generating', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['database_id'], ['database_connections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mdl_schemas_database_id'), 'mdl_schemas', ['database_id'], unique=False)
    op.create_index(op.f('ix_mdl_schemas_name'), 'mdl_schemas', ['name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_mdl_schemas_name'), table_name='mdl_schemas')
    op.drop_index(op.f('ix_mdl_schemas_database_id'), table_name='mdl_schemas')
    op.drop_table('mdl_schemas')
    op.drop_index(op.f('ix_database_connections_user_id'), table_name='database_connections')
    op.drop_table('database_connections')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
