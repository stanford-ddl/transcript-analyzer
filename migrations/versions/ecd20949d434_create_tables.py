"""Create tables

Revision ID: ecd20949d434
Revises: 
Create Date: 2025-02-11 05:40:55.891052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ecd20949d434'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.create_table('jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), server_default='pending'),
        sa.Column('progress', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_table('projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('project_name', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
    )
    op.create_table('files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.Text(), nullable=False),
        sa.Column('s3_key', sa.Text()),  # Add if using S3
        sa.Column('processed_s3_key', sa.Text()), # Add if using S3
        sa.Column('status', sa.Text(), server_default='pending'),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('results', postgresql.JSONB()),
        sa.Column('uploaded_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
    )

def downgrade() -> None:
    op.drop_table('files')
    op.drop_table('projects')
    op.drop_table('jobs')