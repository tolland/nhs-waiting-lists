from typing import Optional

from sqlalchemy import Index, REAL, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from nhs_waiting_lists.models.base import Base


class Provider(Base):
    __tablename__ = 'provider'
    __table_args__ = (
        Index('provider_Trust_code_uindex', 'provider', unique=True),
    )

    # This is currently being populated by a pandas to_sql, this is just for reference
    region_name: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[Optional[str]] = mapped_column(Text)
    subtype: Mapped[Optional[str]] = mapped_column(Text)
    provider: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)
    provider_name: Mapped[Optional[str]] = mapped_column(Text)
