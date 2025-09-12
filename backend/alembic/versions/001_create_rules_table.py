"""Create initial rules table with plaintext storage

Revision ID: 001
Revises: 
Create Date: 2025-09-12 14:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create rules table with plaintext storage as per design specification."""
    
    # Create rules table with correct schema from the start
    op.create_table('rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_defined', sa.Boolean(), nullable=True),
        sa.Column('rule_text', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('parent_rule_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_rule_id'], ['rules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop rules table."""
    op.drop_table('rules')