"""
Remove Profile table and all profile-related foreign keys/relationships.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260121_remove_profile'
down_revision = 'bf25aa0ffc73'
branch_labels = None
depends_on = None

def upgrade():
    # Drop foreign key constraints to profiles.id
    with op.batch_alter_table('subscriptions') as batch_op:
        batch_op.drop_constraint('subscriptions_user_id_fkey', type_='foreignkey')
    with op.batch_alter_table('payments') as batch_op:
        batch_op.drop_constraint('payments_user_id_fkey', type_='foreignkey')
    with op.batch_alter_table('api_keys') as batch_op:
        batch_op.drop_constraint('api_keys_user_id_fkey', type_='foreignkey')
    with op.batch_alter_table('user_media') as batch_op:
        batch_op.drop_constraint('user_media_user_id_fkey', type_='foreignkey')

    # Drop the profiles table
    op.drop_table('profiles')

    # Remove relationships in models already handled by SQLAlchemy model changes

def downgrade():
    # Not implemented: would need to recreate profiles table and FKs
    pass
