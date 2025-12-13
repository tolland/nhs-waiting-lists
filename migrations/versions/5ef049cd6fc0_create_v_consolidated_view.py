"""create v_consolidated view

Revision ID: 5ef049cd6fc0
Revises: d365667bdc31
Create Date: 2025-12-09 19:21:25.969609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ef049cd6fc0'
down_revision: Union[str, Sequence[str], None] = 'd365667bdc31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
               CREATE VIEW consolidated_summary AS
               SELECT i.period,
                      i.provider,
                      i.treatment,
                      i.untreated           AS untreated,
                      i.new_periods         AS new_periods,
                      i.incomplete,
                      i.incomplete_prev     AS incomplete_prev,
                      i.incomplete_diff     AS incomplete_diff,
                      i.completed,
                      i.completed           AS treated,
                      p.provider_name,
                      p.type                AS provider_type,
                      p.subtype             AS provider_subtype,
                      i.total_treatable     AS total_treatable,
                      i.incomplete_expected AS incomplete_expected
               FROM consolidated AS i
                        JOIN provider AS p ON i.provider = p.provider
               ORDER BY i.provider, i.period
               """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS provider_summary")
