"""Initial migration with corrected schema

Revision ID: 8da948186dbb
Revises: 
Create Date: 2025-01-14 01:21:22.916116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8da948186dbb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Step 1: Create a temporary table with the desired schema
    op.create_table(
        'books_temp',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('author', sa.String, nullable=False),
        sa.Column('published_date', sa.Text),
        sa.Column('summary', sa.String),
        sa.Column('genre', sa.String, nullable=False),
    )

    # Step 2: Copy data from the old table to the new table
    op.execute("""
    INSERT INTO books_temp (id, title, author, published_date, summary, genre)
    SELECT id, title, author, published_date, summary, genre FROM books
    """)

    # Step 3: Drop the old table
    op.drop_table('books')

    # Step 4: Rename the temporary table to the original table name
    op.rename_table('books_temp', 'books')

def downgrade():
    # Revert the changes (reverse of the above)
    op.create_table(
        'books_old',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('author', sa.String, nullable=False),
        sa.Column('published_date', sa.Text),  # Adjust if needed
        sa.Column('summary', sa.String),
        sa.Column('genre', sa.String, nullable=False),
    )

    op.execute("""
    INSERT INTO books_old (id, title, author, published_date, summary, genre)
    SELECT id, title, author, published_date, summary, genre FROM books
    """)

    op.drop_table('books')
    op.rename_table('books_old', 'books')