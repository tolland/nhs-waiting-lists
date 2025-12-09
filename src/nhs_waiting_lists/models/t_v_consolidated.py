from sqlalchemy import Column, Integer, String, Float

from nhs_waiting_lists.models.base import Base


class VConsolidated(Base):
    __tablename__ = "v_consolidated"
    __table_args__ = {"extend_existing": True}

    period: str = Column(String, primary_key=True)
    provider: str = Column(String, primary_key=True)
    treatment: str = Column(String, primary_key=True)
    nhs_year: str = Column(String)
    provider_name: str = Column(String)
    subtype: str = Column(String)
    quarter: int = Column(Integer)
    incomplete: int = Column(Integer)
    admitted: int = Column(Integer)
    nonadmitted: int = Column(Integer)
    new_periods: int = Column(Integer)
    incomplete_prev: int = Column(Integer)
    untreated: int = Column(Integer)
    wait_pct_lt_18: float = Column(Float)
