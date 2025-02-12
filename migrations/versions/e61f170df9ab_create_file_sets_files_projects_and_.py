"""Create file_sets, files, projects, and jobs tables

Revision ID: e61f170df9ab
Revises: 6c12fcedb21c
Create Date: 2025-02-12 04:16:57.653815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e61f170df9ab'
down_revision: Union[str, None] = '6c12fcedb21c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table('file_sets',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('files',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('file_set_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('file_path', sa.Text(), nullable=False),
    sa.Column('original_filename', sa.Text(), nullable=False),
    sa.Column('status', sa.Text(), nullable=False, server_default='uploaded'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['file_set_id'], ['file_sets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('projects',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('file_set_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('user_id', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['file_set_id'], ['file_sets.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('jobs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('status', sa.Text(), nullable=False, server_default='pending'),
    sa.Column('progress', sa.REAL(), nullable=True, server_default='0.0'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('user_id', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('jobs')
    op.drop_table('projects')
    op.drop_table('files')
    op.drop_table('file_sets')
