"""Add teams

Revision ID: 6dde42ad8a89
Revises: 3dddf5af5fc4
Create Date: 2018-08-22 14:13:26.303425

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6dde42ad8a89'
down_revision = '3dddf5af5fc4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('teams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('external_id', sa.String(length=120), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('external_id')
    )


def downgrade():
    op.drop_table('teams')
