from typing import Sequence

import pandas as pd
from sqlalchemy import create_engine, Engine
from sqlalchemy import select, and_, bindparam, table, column
from sqlalchemy import text
from sqlalchemy.orm import Session

from nhs_waiting_lists.models import Provider
from nhs_waiting_lists.utils.path_utils import (
    init_paths,
    get_db_path,
)

engine: Engine|None = None

def get_engine() -> Engine:
    global engine
    if engine is not None:
        return engine
    else:
        init_paths()
        db_path = get_db_path()
        engine = create_engine(f"sqlite:///{db_path}")
        return engine

def get_consolidated_df2(
    start_period: str,
    end_period: str,
    provider_codes: Sequence[str],
    treatment_codes: Sequence[str],
) -> pd.DataFrame:
    consolidated_summary = table(
        "consolidated_summary",
        column("period"),
        column("provider"),
        column("treatment"),
        column("untreated"),
        column("new_periods"),
        column("incomplete"),
        column("incomplete_prev"),
        column("completed"),
        column("total_treatable"),
    )

    conditions = [
        consolidated_summary.c.treatment.in_(
            bindparam("treatment_codes", expanding=True)
        ),
        consolidated_summary.c.period >= bindparam("start_period"),
        consolidated_summary.c.period <= bindparam("end_period"),
    ]

    if provider_codes:
        conditions.append(
            consolidated_summary.c.provider.in_(
                bindparam("provider_codes", expanding=True)
            )
        )

    stmt = select(consolidated_summary).where(and_(*conditions))

    df = pd.read_sql(
        stmt,
        con=get_engine(),
        params={
            "provider_codes": provider_codes,
            "treatment_codes": treatment_codes,
            "start_period": start_period,
            "end_period": end_period,
        },
    )

    return df


def get_consolidated_df(
    start_period: str,
    end_period: str,
    provider_codes: Sequence[str],
    treatment_codes: Sequence[str],
) -> pd.DataFrame:
    """
    this method is a low level access the consolidated summary table for a subset of providers and treatments.
    It is used when further processing is required of aggregates and groupby at different levels
    :param engine:
    :param start_period:
    :param end_period:
    :param provider_codes:
    :param treatment_codes:
    :return:
    """

    consolidated_query = text(
        """
        SELECT *
        FROM consolidated_summary AS i
        WHERE provider IN :provider_codes
          AND i.treatment IN :treatment_codes
          AND i.period >= :start_period
          AND i.period <= :end_period; \
        """
    ).bindparams(
        bindparam("provider_codes", expanding=True),
        bindparam("treatment_codes", expanding=True),
        bindparam("start_period", expanding=False),
        bindparam("end_period", expanding=False),
    )

    consolidated_df = pd.read_sql(
        consolidated_query,
        get_engine(),
        params={
            "provider_codes": provider_codes,
            "treatment_codes": treatment_codes,
            "start_period": start_period,
            "end_period": end_period,
        },
    )  # type: ignore[arg-type]

    consolidated_df["period"] = pd.to_datetime(
        consolidated_df["period"], errors="coerce"
    )

    return consolidated_df


def get_consolidated_for_export(
    start_period: str,
    end_period: str,
) -> pd.DataFrame:
    """
    this method is a low level access the consolidated summary table for a subset of providers and treatments.
    It is used when further processing is required of aggregates and groupby at different levels
    :param engine:
    :param start_period:
    :param end_period:
    :param provider_codes:
    :param treatment_codes:
    :return:
    """

    consolidated_query = text(
        """
        SELECT i.*,
               p.type    AS provider_type,
               p.subtype AS provider_subtype
        FROM consolidated AS i
                 LEFT JOIN provider AS p
                           ON i.provider = p.provider
        WHERE i.period >= :start_period
          AND i.period <= :end_period
        ORDER BY i.provider, i.period
        """
    ).bindparams(
        bindparam("start_period", expanding=False),
        bindparam("end_period", expanding=False),
    )

    consolidated_df = pd.read_sql(
        consolidated_query,
        get_engine(),
        params={
            "start_period": start_period,
            "end_period": end_period,
        },
    )  # type: ignore[arg-type]

    return consolidated_df


def load_dataset(
    dataset: str
) -> pd.DataFrame:

    session = Session(get_engine())

    stmt = select(Provider)

    df = pd.read_sql(
        stmt,
        con=get_engine(),

    )

    return df
