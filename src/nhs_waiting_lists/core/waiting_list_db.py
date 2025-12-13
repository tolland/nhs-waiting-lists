from datetime import date
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text

from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import proj_db_path, DB_FILE
from nhs_waiting_lists.utils.xdg import XDGBasedir

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / DB_FILE
DATA_DIR = project_root / "data"

class WaitingListsDB:

    def __init__(self):
        # self.db = create_engine(ensure_data_downloaded())
        self.db = create_engine(f"sqlite:///{DB_PATH}", echo=False)

    def get_connection(self):
        return self.db.raw_connection()

    # RTT/WTD queries
    def rtt_by_provider(
        self,
        provider_codes: str | List[str],
        start_date: date|None = None,
        end_date: date|None = None,
    ) -> pd.DataFrame:
        """
        Get RTT data for a specific provider within a date range.
        
        Args:
            provider_code: The provider code or codes to filter by
            start_date: Start date for the query
            end_date: End date for the query
            
        Returns:
            DataFrame containing RTT data for the provider
            :param end_date:
            :param start_date:
            :param provider_codes:
        """
        if isinstance(provider_codes, str):
            provider_codes = [provider_codes]

        query = text(
            """
                     WITH wait_summary AS (
                         SELECT
                             c.provider,
                             c.nhs_year,
                             SUM(c.untreated) AS sum_untreated
                         FROM v_consolidated AS c
                         WHERE c.treatment = 'C_999'
                         GROUP BY c.provider, c.nhs_year
                     ),
                          dna_summary AS (
                              SELECT
                                  oa.organisation_code AS provider,
                                  oa.reporting_period,
                                  SUM(oa.measure_value) AS sum_dna
                              FROM outpatients_activity AS oa
                              WHERE  oa.measure_type = 'Attendance Type'
                                AND oa.measure LIKE 'Did not%'
                                AND oa.geography_level = 'Provider'
                              GROUP BY oa.organisation_code, oa.reporting_period
                          )
                     SELECT
                         w.provider,
                         w.nhs_year,
                         w.sum_untreated,
                         d.sum_dna,
                         (w.sum_untreated + d.sum_dna) unexplained_untreated
                     FROM wait_summary AS w
                              JOIN dna_summary AS d
                                   ON w.provider = d.provider
                                       AND w.nhs_year = d.reporting_period
                     ORDER BY unexplained_untreated; \
                     """
        ).bindparams(
            # bindparam('provider_codes', expanding=True),
            # bindparam('treatment_codes', expanding=True)
        )

        df = pd.read_sql(
            query,
            self.db,
            params={  # type: ignore[arg-type]
                "provider_codes": provider_codes,
            },
        )
        # df.query("provider == 'RAJ' and treatment == 'C_999' and period == '2025-08'")
        return df

    def rtt_by_treatment(self, treatment_code: str, start_date: date, end_date: date) -> pd.DataFrame:
        """
        Get RTT data for a specific treatment within a date range.
        
        Args:
            treatment_code: The treatment code to filter by
            start_date: Start date for the query
            end_date: End date for the query
            
        Returns:
            DataFrame containing RTT data for the treatment
        """
        # TODO: Implement SQL query for RTT data by treatment
        pass

    def rtt_by_month(self, year: int, month: int) -> pd.DataFrame:
        """
        Get RTT data for a specific month and year.
        
        Args:
            year: The year to filter by
            month: The month to filter by (1-12)
            
        Returns:
            DataFrame containing RTT data for the specified month
        """
        # TODO: Implement SQL query for RTT data by month
        pass

    # Pathway breakdown
    def admitted_pathways(self, provider_code: str, month: str) -> pd.DataFrame:
        """
        Get admitted pathways data for a specific provider and month.
        
        Args:
            provider_code: The provider code to filter by
            month: The month in format 'YYYY-MM'
            
        Returns:
            DataFrame containing admitted pathways data
        """
        # TODO: Implement SQL query for admitted pathways
        pass

    def non_admitted_pathways(self, provider_code: str, month: str) -> pd.DataFrame:
        """
        Get non-admitted pathways data for a specific provider and month.
        
        Args:
            provider_code: The provider code to filter by
            month: The month in format 'YYYY-MM'
            
        Returns:
            DataFrame containing non-admitted pathways data
        """
        # TODO: Implement SQL query for non-admitted pathways
        pass

    def incomplete_pathways(self, provider_code: str, month: str) -> pd.DataFrame:
        """
        Get incomplete pathways data for a specific provider and month.
        
        Args:
            provider_code: The provider code to filter by
            month: The month in format 'YYYY-MM'
            
        Returns:
            DataFrame containing incomplete pathways data
        """
        # TODO: Implement SQL query for incomplete pathways
        pass

    def new_periods(self, provider_code: str, month: str) -> pd.DataFrame:
        """
        Get new periods data for a specific provider and month.
        
        Args:
            provider_code: The provider code to filter by
            month: The month in format 'YYYY-MM'
            
        Returns:
            DataFrame containing new periods data
        """
        # TODO: Implement SQL query for new periods
        pass

    # Provider metadata
    def providers(self) -> pd.DataFrame:
        """
        Get all providers with rankings, type, and financial information.
        
        Returns:
            DataFrame containing all provider information
        """
        # TODO: Implement SQL query for all providers
        pass

    def provider_info(self, provider_code: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific provider.
        
        Args:
            provider_code: The provider code to look up
            
        Returns:
            Dictionary containing provider information
        """
        # TODO: Implement SQL query for specific provider info
        pass

    # Outpatients reconciliation
    def outpatient_activity(self, provider_code: str, year: int) -> pd.DataFrame:
        """
        Get outpatient activity data for a specific provider and year.
        
        Args:
            provider_code: The provider code to filter by
            year: The year to filter by
            
        Returns:
            DataFrame containing outpatient activity data
        """
        # TODO: Implement SQL query for outpatient activity
        pass

    def attendance_outcomes(self, provider_code: str, year: int) -> pd.DataFrame:
        """
        Get attendance outcomes data for a specific provider and year.
        
        Args:
            provider_code: The provider code to filter by
            year: The year to filter by
            
        Returns:
            DataFrame containing attendance outcomes data
        """
        # TODO: Implement SQL query for attendance outcomes
        pass

    # Low-level query method
    def query(self, sql: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Execute a raw SQL query with optional parameters.
        
        Args:
            sql: The SQL query string
            params: Optional dictionary of parameters for the query
            
        Returns:
            DataFrame containing the query results
        """
        if params is None:
            params = {}

        try:
            return pd.read_sql_query(sql, self.db, params=params)
        except Exception as e:
            raise Exception(f"Query failed: {e}")
