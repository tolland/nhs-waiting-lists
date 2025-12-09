from typing import Optional

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from nhs_waiting_lists.models.base import Base


class Consolidated(Base):
    __tablename__ = 'consolidated'

    period: Mapped[str] = mapped_column(Text, primary_key=True)
    provider: Mapped[str] = mapped_column(ForeignKey('providers.provider_code'), primary_key=True)
    treatment: Mapped[str] = mapped_column(Text, primary_key=True)
    incomplete: Mapped[Optional[int]] = mapped_column(Integer)
    incomplete_dta: Mapped[Optional[int]] = mapped_column(Integer)
    admitted: Mapped[Optional[int]] = mapped_column(Integer)
    new_periods: Mapped[Optional[int]] = mapped_column(Integer)
    nonadmitted: Mapped[Optional[int]] = mapped_column(Integer)
    incomplete_prev: Mapped[Optional[int]] = mapped_column(Integer)
    incomplete_diff: Mapped[Optional[int]] = mapped_column(Integer)
    incomplete_expected: Mapped[Optional[int]] = mapped_column(Integer)
    untreated: Mapped[Optional[int]] = mapped_column(Integer)
    admitted_prev: Mapped[Optional[int]] = mapped_column(Integer)
    new_periods_prev: Mapped[Optional[int]] = mapped_column(Integer)
    nonadmitted_prev: Mapped[Optional[int]] = mapped_column(Integer)
    total_treatable: Mapped[Optional[int]] = mapped_column(Integer)
    completed: Mapped[Optional[int]] = mapped_column(Integer)
    completed_prev: Mapped[Optional[int]] = mapped_column(Integer)
    wait_gte_18: Mapped[Optional[int]] = mapped_column(Integer)
    wait_lt_18: Mapped[Optional[int]] = mapped_column(Integer)
    wait_pct_lt_18: Mapped[Optional[int]] = mapped_column(Integer)
    # wait_pct_gte_18: Mapped[Optional[int]] = mapped_column(Integer)
    wait_diff: Mapped[Optional[int]] = mapped_column(Integer)
    wait_sum: Mapped[Optional[int]] = mapped_column(Integer)

    # def __repr__(self) -> str:
    #     return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"
