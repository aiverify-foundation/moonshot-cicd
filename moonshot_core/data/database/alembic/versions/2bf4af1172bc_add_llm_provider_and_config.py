"""Initial schema: create llm_provider, model, config, model_config, and config_parameters tables

Revision ID: 2bf4af1172bc
Revises: 
Create Date: 2025-11-11 18:09:15.604899

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bf4af1172bc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    # Enable foreign key constraints for SQLite
    op.execute("PRAGMA foreign_keys = ON")
    
    # Create llm_provider table
    op.create_table(
        'llm_provider',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create model table
    op.create_table(
        'model',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('llm_provider_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('create_dt', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['llm_provider_id'], ['llm_provider.id']),
        sa.UniqueConstraint('llm_provider_id', 'name')
    )
    
    # Create config table
    op.create_table(
        'config',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('last_update_dt', sa.Date(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create model_config junction table
    op.create_table(
        'model_config',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('last_run_dt', sa.Date(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['model_id'], ['model.id']),
        sa.ForeignKeyConstraint(['config_id'], ['config.id']),
        sa.UniqueConstraint('model_id', 'config_id')
    )
    
    # Create config_parameters table
    op.create_table(
        'config_parameters',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['config_id'], ['config.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_id', 'key')
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('config_parameters')
    op.drop_table('model_config')
    op.drop_table('config')
    op.drop_table('model')
    op.drop_table('llm_provider')
