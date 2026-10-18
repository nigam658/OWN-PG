
"""Remove NOTICE_PERIOD from allocation status."""

from alembic import op


# Revision identifiers used by Alembic.
revision = "e37193b91cb7"
down_revision = "01b4be1a2aff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove NOTICE_PERIOD from the MySQL ENUM.
    op.execute("""
        ALTER TABLE bed_allocations
        MODIFY COLUMN status
        ENUM('ACTIVE', 'CHECKED_OUT')
        NOT NULL
    """)


def downgrade() -> None:
    # Restore NOTICE_PERIOD if this migration is rolled back.
    op.execute("""
        ALTER TABLE bed_allocations
        MODIFY COLUMN status
        ENUM('ACTIVE', 'NOTICE_PERIOD', 'CHECKED_OUT')
        NOT NULL
    """)
