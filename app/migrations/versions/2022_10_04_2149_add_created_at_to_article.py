"""add created_at to article

Revision ID: 2022_10_04_2149
Revises: 2022_10_04_2140
Create Date: 2022-10-04 21:49:39.987020

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2022_10_04_2149'
down_revision = '2022_10_04_2140'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('article', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                                       nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('article', 'created_at')
    # ### end Alembic commands ###
