"""Add CafeTopic

Revision ID: a49d90c3f04
Revises: 3f31ff87f70e
Create Date: 2015-09-23 11:06:12.022980

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a49d90c3f04'
down_revision = '3f31ff87f70e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'zq_cafe_topic',
        sa.Column('cafe_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('topic_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.SmallInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('cafe_id', 'topic_id')
    )
    op.add_column(
        u'zq_topic',
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True)
    )
    op.drop_column(u'zq_topic', 'fork_id')


def downgrade():
    op.add_column(
        u'zq_topic',
        sa.Column('fork_id', sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.drop_column(u'zq_topic', 'tags')
    op.drop_table('zq_cafe_topic')
