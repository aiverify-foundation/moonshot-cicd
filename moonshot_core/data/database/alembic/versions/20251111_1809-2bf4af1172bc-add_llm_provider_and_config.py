"""Initial schema: Create tables for LLM Provider and Model Configurations

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
    
    # Create table to store LLM Providers
    op.create_table(
        'llm_provider',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('system_name', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('system_name', 'version', name='uq_llm_provider_system_name_version'),
    )
    
    # Create table to store LLM name under a LLM Provider
    op.create_table(
        'llm_provider_model',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('llm_provider_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('create_dt', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['llm_provider_id'], ['llm_provider.id']),
        sa.UniqueConstraint('llm_provider_id', 'name')
    )
    
    # Create table to store LLM configuration
    op.create_table(
        'llm_provider_model_config',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('updated_dt', sa.Date(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_used_dt', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['model_id'], ['llm_provider_model.id']),
    )
    
    # Create table to store under LLM configuration's key-value pairs
    # Note: This table is not meant for storing sensitive information like API keys, etc.
    op.create_table(
        'llm_provider_model_config_parameters',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['config_id'], ['llm_provider_model_config.id']),
        sa.UniqueConstraint(
            'config_id',
            'key',
            name='uq_llm_provider_model_config_parameters_config_key',
        ),
    )

    # Create table to store LLM Provider's API key (encrypted)
    # Each LLM Provider can store multiple API keys
    op.create_table(
        'llm_provider_api_key',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('llm_provider_id', sa.Integer(), nullable=False),
        sa.Column('encrypted_key', sa.String(), nullable=False),
        sa.Column('salt', sa.String(), nullable=False),
        sa.Column('nonce', sa.String, nullable=False),
        sa.Column('authentication_tag', sa.String, nullable=False),
        sa.Column('created_dt', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_used_dt', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['llm_provider_id'], ['llm_provider.id']),
    )

    # Create table to store application configurations as key-value pairs
    op.create_table(
        'moonshot_config',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('moonshot_config')
    op.drop_table('llm_provider_api_key')
    op.drop_table('llm_provider_model_config_parameters')
    op.drop_table('llm_provider_model_config')
    op.drop_table('llm_provider_model')
    op.drop_table('llm_provider')
