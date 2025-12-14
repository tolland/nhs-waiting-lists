import os
from pathlib import Path


def test_pytest_setup(xdg_state_home: Path):

    import nhs_waiting_lists as nhs
    # first time you run this.
    nhs.init_db() # load bundled data into sqlite

    expected_file = xdg_state_home / "your_package_name" / "state.db"

    assert os.environ["XDG_STATE_HOME"] != ""

    start_period = "2024-01"
    end_period = "2024-01"
    summary_df = nhs.get_consolidated_df(
        start_period,
        end_period,
        nhs.constants.LARGE_ACUTE_PROVIDER_CODES,
        nhs.constants.TOTAL_ONLY_TREATMENT_CODES
    ).groupby(["period", "provider"]).sum()
    assert summary_df.shape == (23, 13)
