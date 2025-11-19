from typing import Optional

from sqlalchemy import Index, REAL, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from nhs_waiting_lists.models.base import Base


class Provider(Base):
    __tablename__ = 'provider'
    __table_args__ = (
        Index('provider_Trust_code_uindex', 'Trust_code', unique=True),
    )

    Region: Mapped[Optional[str]] = mapped_column(Text)
    Trust_type: Mapped[Optional[str]] = mapped_column(Text)
    Trust_subtype: Mapped[Optional[str]] = mapped_column(Text)
    Trust_code: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)
    Trust_name: Mapped[Optional[str]] = mapped_column(Text)
    Reporting_date: Mapped[Optional[str]] = mapped_column(Text)
    Average_score: Mapped[Optional[float]] = mapped_column(REAL)
    Likely_range_of_average_score: Mapped[Optional[str]] = mapped_column(Text)
    Segment: Mapped[Optional[float]] = mapped_column(REAL)
    Trust_in_financial_deficit: Mapped[Optional[str]] = mapped_column(Text)
    Rank: Mapped[Optional[float]] = mapped_column(REAL)
    Likely_range_of_rank: Mapped[Optional[str]] = mapped_column(Text)
