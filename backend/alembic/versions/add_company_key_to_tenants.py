"""Add company_key to tenants

Revision ID: add_company_key_001
Revises: 997bd42011da
Create Date: 2025-12-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_company_key_001'
down_revision = '997bd42011da'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add company_key column to tenants table
    op.add_column('tenants', sa.Column('company_key', sa.String(length=100), nullable=True))


def downgrade() -> None:
    # Remove company_key column from tenants table
    op.drop_column('tenants', 'company_key')
