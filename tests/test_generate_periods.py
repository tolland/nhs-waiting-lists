import pytest
import pandas as pd
from nhs_waiting_lists.utils.date_field_parsing import generate_periods


class TestGeneratePeriods:
    """Test period generation."""

    def test_generate_periods_01(self):

        periods =       generate_periods('2003-01', '2003-02')
        assert len(periods) == 2
        assert periods[0] == '2003-01'
        assert periods[1] == '2003-02'
