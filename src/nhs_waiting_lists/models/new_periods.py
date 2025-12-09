from typing import Optional

from sqlalchemy import Integer, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from nhs_waiting_lists.models.base import Base


class NewPeriods(Base):
    """
    Bucketed waiting times.
    """
    __tablename__ = "new_periods"

    # Primary key - includes commissioner to preserve all rows before grouping
    period: Mapped[str] = mapped_column(Text, primary_key=True)
    provider: Mapped[str] = mapped_column(Text, primary_key=True)
    treatment: Mapped[str] = mapped_column(Text, primary_key=True)

    # Summary columns
    total_all: Mapped[Optional[int]] = mapped_column(Integer)

    # QA/validation columns (computed during import for integrity checks)
    qa_wait_sum: Mapped[Optional[int]] = mapped_column(Integer)  # Sum of all wait buckets
    qa_diff_total: Mapped[Optional[int]] = mapped_column(Integer)  # wait_sum - total (should be ~0)
    qa_diff_total_all: Mapped[Optional[int]] = mapped_column(Integer)  # wait_sum - total_all + unknown (should be ~0)
