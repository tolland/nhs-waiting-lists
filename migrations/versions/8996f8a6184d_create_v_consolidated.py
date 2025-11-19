"""create v_consolidated

Revision ID: 8996f8a6184d
Revises: 6bcd6014e3b3
Create Date: 2025-10-26 03:28:23.545947

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8996f8a6184d'
down_revision: Union[str, Sequence[str], None] = '6bcd6014e3b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
CREATE VIEW v_consolidated as
SELECT c.period,
       CASE
           WHEN CAST(substr(period, 6, 2) AS INTEGER) >= 4
               THEN substr(period, 1, 4) || '-' || substr(CAST(CAST(substr(period, 1, 4) AS INTEGER) + 1 AS TEXT), 3, 2)
           ELSE substr(CAST(CAST(substr(period, 1, 4) AS INTEGER) - 1 AS TEXT), 1, 4) || '-' || substr(period, 3, 2)
           END                                                             AS nhs_year,
       p.provider_name,
       p.subtype,
       COALESCE(NULLIF((strftime('%m', c.period || '-01') + 2) / 3, 0), 4) AS Quarter,
       c.provider,
       c.treatment,
       c.incomplete,
       c.admitted,
       c.nonadmitted,
       c.new_periods,
       c.incomplete_prev,
       c.untreated,
       c.wait_pct_lt_18
FROM consolidated AS c
         INNER JOIN providers AS p ON c.provider = p.provider_code
WHERE p.subtype = 'Acute - Large'
  AND treatment = 'C_999'
ORDER BY p.provider_code, c.treatment, c.period;


    """)


def downgrade() -> None:
    op.execute("DROP VIEW v_consolidated")
