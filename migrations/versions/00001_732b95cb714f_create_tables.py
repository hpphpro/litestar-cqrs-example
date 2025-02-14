"""create_tables

Revision ID: 00001_732b95cb714f
Revises:
Create Date: 2025-02-11 02:37:16.567799

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from src.core.config import absolute_path

# revision identifiers, used by Alembic.
revision: str = '00001_732b95cb714f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(open(absolute_path("sql", "functions", "uuid_generate_v7.sql"), mode="r").read())
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.create_table('user',
    sa.Column('login', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_login_lower', 'user', [sa.text('lower(login)')], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_user_login_lower', table_name='user')
    op.drop_table('user')
    op.execute("DROP FUNCTION IF EXISTS uuid_generate_v7() CASCADE;")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto CASCADE;")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp" CASCADE;')
    # ### end Alembic commands ###
