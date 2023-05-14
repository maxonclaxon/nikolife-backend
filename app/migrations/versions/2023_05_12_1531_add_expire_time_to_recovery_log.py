"""add expire time to recovery log

Revision ID: 2023_05_12_1531
Revises: 2023_05_12_1518
Create Date: 2023-05-12 15:31:29.234651

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2023_05_12_1531'
down_revision = '2023_05_12_1518'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('recovery_log', sa.Column('expire', sa.DateTime(timezone=True), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('recovery_log', 'expire')
    # ### end Alembic commands ###
