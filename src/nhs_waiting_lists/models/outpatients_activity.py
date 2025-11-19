from typing import Optional

from sqlalchemy import REAL, Text
from sqlalchemy.orm import Mapped, mapped_column

from nhs_waiting_lists.models.base import Base


class OutpatientsActivity(Base):
    __tablename__ = 'outpatients_activity'

    reporting_period: Mapped[str] = mapped_column(Text, primary_key=True)
    geography_level: Mapped[str] = mapped_column(Text, primary_key=True)
    organisation_code: Mapped[str] = mapped_column(Text, primary_key=True)
    measure_type: Mapped[str] = mapped_column(Text, primary_key=True)
    measure: Mapped[str] = mapped_column(Text, primary_key=True)
    measure_value: Mapped[Optional[float]] = mapped_column(REAL)
