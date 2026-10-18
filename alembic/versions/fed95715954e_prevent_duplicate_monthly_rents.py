"""prevent duplicate monthly rents

Revision ID: fed95715954e
Revises: e37193b91cb7
Create Date: 2026-10-11 22:58:31.376810

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fed95715954e'
down_revision: Union[str, Sequence[str], None] = 'e37193b91cb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a unique index for one rent per allocation per month.
    # Keep the old index until the new index has been created.
    op.create_index(
        "uq_bed_allocation_billing_month",
        "monthly_rents",
        ["bed_allocation_id", "billing_month"],
        unique=True,
    )

    # Remove the old exact-date uniqueness rule after the new index exists.
    op.drop_index(
        "uq_bed_allocation_due_date",
        table_name="monthly_rents",
    )




def downgrade() -> None:
    # Restore the original unique index on the exact due date.
    op.create_index(
        "uq_bed_allocation_due_date",
        "monthly_rents",
        ["bed_allocation_id", "due_date"],
        unique=True,
    )

    # Remove the new unique index on the billing month.
    op.drop_index(
        "uq_bed_allocation_billing_month",
        table_name="monthly_rents",
    )

    # Keep billing_month because it existed before this migration.

