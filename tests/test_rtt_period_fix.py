import pandas as pd
import pytest
from nhs_waiting_lists.utils.date_field_parsing import fix_rtt_period


class TestFixRttPeriod:

    def test_fix_rtt_period_handles_rtt_prefix(self) -> None:
        """Handles 'RTT-' prefix correctly."""
        row = pd.Series({"Period": "RTT-JANUARY-2018"})
        assert fix_rtt_period(row) == "2018-01"

    def test_fix_rtt_period_handles_standard_format(self) -> None:
        """Handles standard 'YYYY-YY-MONTH' format correctly."""
        row = pd.Series({"Period": "2022-23-MARCH"})
        assert fix_rtt_period(row) == "2023-03"

    def test_fix_rtt_period_handles_april_to_december(self) -> None:
        """Maps April–December to the start year."""
        row = pd.Series({"Period": "2022-23-APRIL"})
        assert fix_rtt_period(row) == "2022-04"

    def test_fix_rtt_period_handles_january_to_march(self) -> None:
        """Maps January–March to the end year."""
        row = pd.Series({"Period": "2022-23-JANUARY"})
        assert fix_rtt_period(row) == "2023-01"

    def test_fix_rtt_period_raises_keyerror_for_invalid_month(self) -> None:
        """Raises KeyError for invalid month names."""
        row = pd.Series({"Period": "2022-23-INVALID"})
        with pytest.raises(KeyError):
            fix_rtt_period(row)

    def test_fix_rtt_period_raises_valueerror_for_malformed_period(self) -> None:
        """Raises ValueError for malformed period strings."""
        row = pd.Series({"Period": "2022-MARCH"})
        with pytest.raises(ValueError):
            fix_rtt_period(row)
