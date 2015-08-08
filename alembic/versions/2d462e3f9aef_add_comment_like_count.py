"""Add comment like_count

Revision ID: 2d462e3f9aef
Revises: 56f30eacbb77
Create Date: 2015-08-08 02:55:45.855068

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2d462e3f9aef'
down_revision = '56f30eacbb77'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'zq_comment', sa.Column('like_count', sa.Integer(), nullable=True)
    )


def downgrade():
    op.drop_column('zq_comment', 'like_count')
