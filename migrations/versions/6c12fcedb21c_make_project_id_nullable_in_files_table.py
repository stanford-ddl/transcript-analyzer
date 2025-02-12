"""Make project_id nullable in files table

Revision ID: 6c12fcedb21c
Revises: ecd20949d434
Create Date: 2025-02-11 05:51:08.997415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c12fcedb21c'
down_revision: Union[str, None] = 'ecd20949d434'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
     # Drop the foreign key constraint
     op.drop_constraint('files_project_id_fkey', 'files', type_='foreignkey')
     # Alter the column to allow NULL
     op.alter_column('files', 'project_id',
            existing_type=sa.UUID(),
            nullable=True)

def downgrade() -> None:
    # Make the column NOT NULL again
    op.alter_column('files', 'project_id',
        existing_type=sa.UUID(),
        nullable=False)
    # Add the foreign key constraint back
    op.create_foreign_key('files_project_id_fkey', 'files', 'projects', ['project_id'], ['id'], ondelete='CASCADE')
