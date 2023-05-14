"""add user id to recovery

Revision ID: 2023_05_12_1518
Revises: 2023_05_12_1511
Create Date: 2023-05-12 15:18:51.311768

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2023_05_12_1518'
down_revision = '2023_05_12_1511'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('recovery_log', sa.Column('user_id', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('recovery_log', 'user_id')
    # ### end Alembic commands ###
