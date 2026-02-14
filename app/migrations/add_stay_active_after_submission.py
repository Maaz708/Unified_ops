"""Add stay_active_after_submission to form_templates

Revision ID: add_stay_active_after_submission
Revises: add_form_templates_booking_type_id
Create Date: 2026-02-14 15:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_stay_active_after_submission'
down_revision = 'add_form_templates_booking_type_id'
branch_labels = None
depends_on = None


def upgrade():
    # Add stay_active_after_submission column to form_templates table
    op.add_column('form_templates', sa.Column('stay_active_after_submission', sa.Boolean(), nullable=False, server_default='true'))


def downgrade():
    # Remove stay_active_after_submission column from form_templates table
    op.drop_column('form_templates', 'stay_active_after_submission')
