import pytest
import pandas as pd

from nhs_waiting_lists.utils.date_field_parsing import (
    fiscal_to_calendar,
)


class TestFiscalToCalendar:
    """Test fiscal year to calendar period conversion."""

    def test_april_december_use_start_year(self) -> None:
        """April–December should map to start year."""
        test_cases = [
            ("2016-17", "APRIL", "2016-04"),
            ("2016-17", "JUNE", "2016-06"),
            ("2016-17", "DECEMBER", "2016-12"),
            ("2020-21", "OCTOBER", "2020-10"),
        ]
        for year, month, expected in test_cases:
            row = pd.Series({"Year": year, "Period Name": month})
            assert fiscal_to_calendar(row) == expected

    def test_january_march_use_end_year(self) -> None:
        """January–March should map to end year."""
        test_cases = [
            ("2016-17", "JANUARY", "2017-01"),
            ("2016-17", "FEBRUARY", "2017-02"),
            ("2016-17", "MARCH", "2017-03"),
            ("2020-21", "MARCH", "2021-03"),
        ]
        for year, month, expected in test_cases:
            row = pd.Series({"Year": year, "Period Name": month})
            assert fiscal_to_calendar(row) == expected

    def test_case_insensitivity(self) -> None:
        """Month names should work in any case."""
        row_upper = pd.Series({"Year": "2016-17", "Period Name": "JUNE"})
        row_lower = pd.Series({"Year": "2016-17", "Period Name": "june"})
        row_mixed = pd.Series({"Year": "2016-17", "Period Name": "June"})

        expected = "2016-06"
        assert fiscal_to_calendar(row_upper) == expected
        assert fiscal_to_calendar(row_lower) == expected
        assert fiscal_to_calendar(row_mixed) == expected

    def test_year_boundary_cases(self) -> None:
        """Test with different starting years."""
        test_cases = [
            ("2000-01", "JANUARY", "2001-01"),
            ("2000-01", "APRIL", "2000-04"),
            ("2099-00", "DECEMBER", "2099-12"),
        ]
        for year, month, expected in test_cases:
            row = pd.Series({"Year": year, "Period Name": month})
            assert fiscal_to_calendar(row) == expected

    def test_output_format(self) -> None:
        """Output should always be YYYY-MM with zero padding."""
        row = pd.Series({"Year": "2009-10", "Period Name": "JANUARY"})
        result = fiscal_to_calendar(row)

        assert len(result) == 7
        assert result[4] == "-"
        assert result == "2010-01"

    def test_dataframe_apply(self) -> None:
        """Test integration with DataFrame.apply()."""
        df = pd.DataFrame(
            {
                "Year": ["2016-17", "2016-17", "2016-17"],
                "Period Name": ["APRIL", "JANUARY", "DECEMBER"],
            }
        )

        result = df.apply(fiscal_to_calendar, axis=1)
        expected = pd.Series(["2016-04", "2017-01", "2016-12"])

        pd.testing.assert_series_equal(result, expected)

    def test_invalid_month_raises(self) -> None:
        """Invalid month names should raise KeyError."""
        row = pd.Series({"Year": "2016-17", "Period Name": "INVALID"})
        with pytest.raises(KeyError):
            fiscal_to_calendar(row)

    def test_malformed_year_raises(self) -> None:
        """Malformed year should raise ValueError."""
        row = pd.Series({"Year": "2016", "Period Name": "JANUARY"})
        with pytest.raises(ValueError):
            fiscal_to_calendar(row)


