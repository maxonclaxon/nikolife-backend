"""add recovery log table

Revision ID: 2023_05_12_1511
Revises: 2023_05_11_1310
Create Date: 2023-05-12 15:12:04.245582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2023_05_12_1511'
down_revision = '2023_05_11_1310'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('recovery_log',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('key', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('recovery_log')
    # ### end Alembic commands ###