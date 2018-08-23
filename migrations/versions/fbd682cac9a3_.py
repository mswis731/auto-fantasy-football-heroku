"""Add transactions

Revision ID: fbd682cac9a3
Revises: 6dde42ad8a89
Create Date: 2018-08-22 20:00:36.463828

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fbd682cac9a3'
down_revision = '6dde42ad8a89'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('drop_player', sa.String(length=120), nullable=False),
    sa.Column('add_player', sa.String(length=120), nullable=False),
    sa.Column('status', sa.Enum('COMPLETE', 'ERRORED', 'FAILED', 'PENDING', name='status'), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('transactions')
    op.execute('DROP TYPE status')
