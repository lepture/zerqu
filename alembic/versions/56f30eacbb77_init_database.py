"""Init database

Revision ID: 56f30eacbb77
Revises: None
Create Date: 2015-07-19 03:38:33.878092

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '56f30eacbb77'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'zq_auth_session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('platform', sa.String(length=20), nullable=True),
        sa.Column('browser', sa.String(length=40), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'zq_cafe',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=30), nullable=False),
        sa.Column('name', sa.Unicode(length=30), nullable=False),
        sa.Column('description', sa.Unicode(length=140), nullable=True),
        sa.Column('intro', sa.Integer(), nullable=True),
        sa.Column('style', JSON(), nullable=True),
        sa.Column('features', sa.Integer(), nullable=True),
        sa.Column('permission', sa.SmallInteger(), nullable=True),
        sa.Column('status', sa.SmallInteger(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(
        op.f('ix_zq_cafe_slug'),
        'zq_cafe', ['slug'], unique=True,
    )
    op.create_index(
        op.f('ix_zq_cafe_user_id'),
        'zq_cafe', ['user_id'], unique=False
    )
    op.create_table(
        'zq_cafe_member',
        sa.Column('cafe_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('role', sa.SmallInteger(), nullable=True),
        sa.Column('reputation', sa.Integer(), nullable=True),
        sa.Column('description', sa.Unicode(length=140), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('cafe_id', 'user_id')
    )
    op.create_table(
        'zq_comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.UnicodeText(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reply_to', sa.Integer(), nullable=True),
        sa.Column('status', sa.SmallInteger(), nullable=True),
        sa.Column('flag_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_zq_comment_topic_id'),
        'zq_comment', ['topic_id'], unique=False
    )
    op.create_index(
        op.f('ix_zq_comment_user_id'),
        'zq_comment', ['user_id'], unique=False
    )
    op.create_table(
        'zq_comment_like',
        sa.Column('comment_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('comment_id', 'user_id')
    )
    op.create_table(
        'zq_oauth_client',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(length=40), nullable=False),
        sa.Column('avatar_url', sa.String(length=260), nullable=True),
        sa.Column('description', sa.Unicode(length=140), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(length=64), nullable=True),
        sa.Column('client_secret', sa.String(length=64), nullable=True),
        sa.Column('is_confidential', sa.Boolean(), nullable=True),
        sa.Column('default_scope', sa.String(length=140), nullable=True),
        sa.Column('redirect_uris', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(
        op.f('ix_zq_oauth_client_client_id'),
        'zq_oauth_client', ['client_id'], unique=True
    )
    op.create_index(
        op.f('ix_zq_oauth_client_client_secret'),
        'zq_oauth_client', ['client_secret'], unique=True
    )
    op.create_index(
        op.f('ix_zq_oauth_client_user_id'),
        'zq_oauth_client', ['user_id'], unique=False,
    )
    op.create_table(
        'zq_oauth_token',
        sa.Column('client_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('access_token', sa.String(length=34), nullable=True),
        sa.Column('refresh_token', sa.String(length=34), nullable=True),
        sa.Column('token_type', sa.String(length=10), nullable=True),
        sa.Column('scope', sa.String(length=480), nullable=True),
        sa.Column('expires_in', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('client_id', 'user_id')
    )
    op.create_index(
        op.f('ix_zq_oauth_token_access_token'),
        'zq_oauth_token', ['access_token'], unique=True,
    )
    op.create_index(
        op.f('ix_zq_oauth_token_refresh_token'),
        'zq_oauth_token', ['refresh_token'], unique=True,
    )
    op.create_table(
        'zq_social_user',
        sa.Column('service', sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column('uuid', sa.String(length=64), nullable=False),
        sa.Column('info', JSON(), nullable=True),
        sa.Column('status', sa.SmallInteger(), nullable=True),
        sa.Column('reputation', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('service', 'uuid')
    )
    op.create_table(
        'zq_topic',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Unicode(length=140), nullable=False),
        sa.Column('webpage', sa.String(length=34), nullable=True),
        sa.Column('content', sa.UnicodeText(), nullable=True),
        sa.Column('info', JSON(), nullable=True),
        sa.Column('cafe_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('fork_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.SmallInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_zq_topic_cafe_id'),
        'zq_topic', ['cafe_id'], unique=False,
    )
    op.create_index(
        op.f('ix_zq_topic_user_id'),
        'zq_topic', ['user_id'], unique=False,
    )
    op.create_table(
        'zq_topic_like',
        sa.Column('topic_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('topic_id', 'user_id')
    )
    op.create_table(
        'zq_topic_read',
        sa.Column('topic_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('percent', sa.SmallInteger(), nullable=True),
        sa.PrimaryKeyConstraint('topic_id', 'user_id')
    )
    op.create_table(
        'zq_topic_status',
        sa.Column('topic_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('reads', sa.Integer(), nullable=True),
        sa.Column('flags', sa.Integer(), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.Column('comments', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.Integer(), nullable=True),
        sa.Column('reputation', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('topic_id')
    )
    op.create_table(
        'zq_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=24), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=260), nullable=True),
        sa.Column('password', sa.String(length=100), nullable=True),
        sa.Column('name', sa.Unicode(length=40), nullable=True),
        sa.Column('description', sa.Unicode(length=280), nullable=True),
        sa.Column('role', sa.SmallInteger(), nullable=True),
        sa.Column('reputation', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_table(
        'zq_webpage',
        sa.Column('uuid', sa.String(length=34), nullable=False),
        sa.Column('link', sa.String(length=400), nullable=False),
        sa.Column('title', sa.Unicode(length=80), nullable=True),
        sa.Column('image', sa.String(length=256), nullable=True),
        sa.Column('description', sa.Unicode(length=140), nullable=True),
        sa.Column('info', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('domain', sa.String(length=200), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('uuid')
    )


def downgrade():
    op.drop_table('zq_webpage')
    op.drop_table('zq_user')
    op.drop_table('zq_topic_status')
    op.drop_table('zq_topic_read')
    op.drop_table('zq_topic_like')
    op.drop_index(op.f('ix_zq_topic_user_id'), table_name='zq_topic')
    op.drop_index(op.f('ix_zq_topic_cafe_id'), table_name='zq_topic')
    op.drop_table('zq_topic')
    op.drop_table('zq_social_user')
    op.drop_index(op.f('ix_zq_oauth_token_refresh_token'), table_name='zq_oauth_token')
    op.drop_index(op.f('ix_zq_oauth_token_access_token'), table_name='zq_oauth_token')
    op.drop_table('zq_oauth_token')
    op.drop_index(op.f('ix_zq_oauth_client_user_id'), table_name='zq_oauth_client')
    op.drop_index(op.f('ix_zq_oauth_client_client_secret'), table_name='zq_oauth_client')
    op.drop_index(op.f('ix_zq_oauth_client_client_id'), table_name='zq_oauth_client')
    op.drop_table('zq_oauth_client')
    op.drop_table('zq_comment_like')
    op.drop_index(op.f('ix_zq_comment_user_id'), table_name='zq_comment')
    op.drop_index(op.f('ix_zq_comment_topic_id'), table_name='zq_comment')
    op.drop_table('zq_comment')
    op.drop_table('zq_cafe_member')
    op.drop_index(op.f('ix_zq_cafe_user_id'), table_name='zq_cafe')
    op.drop_index(op.f('ix_zq_cafe_slug'), table_name='zq_cafe')
    op.drop_table('zq_cafe')
    op.drop_table('zq_auth_session')
