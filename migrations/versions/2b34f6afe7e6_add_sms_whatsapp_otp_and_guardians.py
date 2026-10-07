"""add_sms_whatsapp_otp_and_guardians

Revision ID: 2b34f6afe7e6
Revises: 
Create Date: 2026-10-04 13:34:27.753721

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '2b34f6afe7e6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    tables = inspector.get_table_names()

    # 1. Create otp_challenges table if not exists
    if 'otp_challenges' not in tables:
        op.create_table(
            'otp_challenges',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('phone_number', sa.String(length=30), nullable=False),
            sa.Column('channel', sa.String(length=20), nullable=False, server_default='sms'),
            sa.Column('purpose', sa.String(length=30), nullable=False, server_default='2fa_login'),
            sa.Column('otp_hash', sa.String(length=256), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('consumed_at', sa.DateTime(), nullable=True),
            sa.Column('ip_address', sa.String(length=50), nullable=False, server_default='127.0.0.1'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
        )
        op.create_index('ix_otp_challenges_phone_number', 'otp_challenges', ['phone_number'])
        op.create_index('ix_otp_challenges_expires_at', 'otp_challenges', ['expires_at'])
        op.create_index('ix_otp_challenges_created_at', 'otp_challenges', ['created_at'])

    # 2. Create guardians table if not exists
    if 'guardians' not in tables:
        op.create_table(
            'guardians',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('name', sa.String(length=120), nullable=False),
            sa.Column('relationship_type', sa.String(length=50), nullable=False, server_default='Guardian'),
            sa.Column('phone_number', sa.String(length=30), nullable=False),
            sa.Column('preferred_channel', sa.String(length=20), nullable=False, server_default='sms'),
            sa.Column('consent_given', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('consent_at', sa.DateTime(), nullable=True),
            sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('opted_out', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
        )
        op.create_index('ix_guardians_user_id', 'guardians', ['user_id'])
        op.create_index('ix_guardians_phone_number', 'guardians', ['phone_number'])

    # 3. Create notification_log table if not exists
    if 'notification_log' not in tables:
        op.create_table(
            'notification_log',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('recipient_type', sa.String(length=30), nullable=False),
            sa.Column('recipient_ref', sa.String(length=120), nullable=False),
            sa.Column('channel', sa.String(length=20), nullable=False),
            sa.Column('template', sa.String(length=100), nullable=False),
            sa.Column('provider_message_id', sa.String(length=120), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='queued'),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
        )
        op.create_index('ix_notification_log_provider_message_id', 'notification_log', ['provider_message_id'])
        op.create_index('ix_notification_log_created_at', 'notification_log', ['created_at'])

    # 4. Alter existing tables
    with op.batch_alter_table('users', schema=None) as batch_op:
        user_cols = [c['name'] for c in inspector.get_columns('users')]
        if 'phone_number' not in user_cols:
            batch_op.add_column(sa.Column('phone_number', sa.String(length=30), nullable=True))
            batch_op.create_index('ix_users_phone_number', ['phone_number'], unique=False)
        if 'phone_verified' not in user_cols:
            batch_op.add_column(sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        if 'preferred_otp_channel' not in user_cols:
            batch_op.add_column(sa.Column('preferred_otp_channel', sa.String(length=20), nullable=False, server_default='sms'))

    with op.batch_alter_table('activity_logs', schema=None) as batch_op:
        act_cols = [c['name'] for c in inspector.get_columns('activity_logs')]
        if 'action_type' not in act_cols:
            batch_op.add_column(sa.Column('action_type', sa.String(length=100), nullable=True))
        if 'description' not in act_cols:
            batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        if 'prev_hash' not in act_cols:
            batch_op.add_column(sa.Column('prev_hash', sa.String(length=64), nullable=True))
        if 'record_hash' not in act_cols:
            batch_op.add_column(sa.Column('record_hash', sa.String(length=64), nullable=True))

    with op.batch_alter_table('login_history', schema=None) as batch_op:
        log_cols = [c['name'] for c in inspector.get_columns('login_history')]
        if 'phone_attempted' not in log_cols:
            batch_op.add_column(sa.Column('phone_attempted', sa.String(length=30), nullable=True))
        if 'login_method' not in log_cols:
            batch_op.add_column(sa.Column('login_method', sa.String(length=30), nullable=False, server_default='password'))
        if 'success' not in log_cols:
            batch_op.add_column(sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.text('1')))


def downgrade():
    op.drop_table('notification_log')
    op.drop_table('guardians')
    op.drop_table('otp_challenges')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_phone_number')
        batch_op.drop_column('preferred_otp_channel')
        batch_op.drop_column('phone_verified')
        batch_op.drop_column('phone_number')
