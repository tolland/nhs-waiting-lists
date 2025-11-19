from sqlalchemy import Column, REAL, Table, Text

from nhs_waiting_lists.models.base import Base

t_providers = Table(
    "providers",
    Base.metadata,
    Column("region_name", Text),
    Column("type", Text),
    Column("subtype", Text),
    Column("provider_code", Text),
    Column("provider_name", Text),
    Column("Reporting_date", Text),
    Column("Average_score", REAL),
    Column("Likely_range_of_average_score", Text),
    Column("Segment", REAL),
    Column("Trust_in_financial_deficit", Text),
    Column("Rank", REAL),
    Column("Likely_range_of_rank", Text),
)
