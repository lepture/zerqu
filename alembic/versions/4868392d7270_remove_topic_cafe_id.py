"""Remove Topic.cafe_id

Revision ID: 4868392d7270
Revises: a49d90c3f04
Create Date: 2015-10-12 06:58:59.165762

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4868392d7270'
down_revision = 'a49d90c3f04'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('zq_cafe', 'features')
    op.drop_index('ix_zq_topic_cafe_id', table_name='zq_topic')
    op.drop_column('zq_topic', 'cafe_id')


def downgrade():
    op.add_column(
        'zq_topic',
        sa.Column('cafe_id', sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.create_index(
        'ix_zq_topic_cafe_id', 'zq_topic', ['cafe_id'], unique=False
    )
    op.add_column(
        'zq_cafe',
        sa.Column('features', sa.INTEGER(), autoincrement=False, nullable=True)
    )
