
"""Add billing_month generated column to monthly_rents.

Revision ID: 64e3cca30d6e
Revises: e37193b91cb7
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic revision identifiers.
revision: str = "64e3cca30d6e"
down_revision: Union[str, Sequence[str], None] = "e37193b91cb7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add a generated column containing the first day of each billing month."""

    op.add_column(
        "monthly_rents",
        sa.Column(
            "billing_month",
            sa.Date(),
            sa.Computed(
                "DATE_SUB(due_date, INTERVAL (DAYOFMONTH(due_date) - 1) DAY)",
                persisted=True,
            ),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove the generated billing month column."""

    op.drop_column("monthly_rents", "billing_month")
