import zipfile
from pathlib import Path

import pandas as pd
import typer
from alembic import command
from alembic.config import Config

import nhs_waiting_lists as nhs
from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.models import Consolidated
from nhs_waiting_lists.utils.canned_queries import get_consolidated_for_export, engine
from nhs_waiting_lists.utils.path_utils import init_paths
from nhs_waiting_lists.utils.xdg import XDGBasedir

project_root = Path(XDGBasedir.get_data_dir(__app_name__))


app = typer.Typer(name="init", no_args_is_help=False)

@app.callback()
def init_callback(
    _ctx: typer.Context,
):
    """
    Parse the raw outpatient activity data from csv and xlsx files downloaded by the scrapy spider.
    """

    print(f"in the init callback")

@app.command("exporter")
def bundled_db_exporter(
    ctx: typer.Context,
):
    typer.echo(f"bundled exporter ....")

    start_period = "2023-01"
    end_period = "2025-09"

    consolidated_df = (
        get_consolidated_for_export(
        start_period,
        end_period,
    )
    .query("provider_type == 'Acute trust'")
        [["period","provider","treatment","incomplete","incomplete_dta","admitted","new_periods","nonadmitted","incomplete_prev","incomplete_diff","incomplete_expected","untreated","admitted_prev","new_periods_prev","nonadmitted_prev","total_treatable","completed","completed_prev","wait_gte_18","wait_lt_18","wait_pct_lt_18","wait_diff","wait_sum"]]
    )
    print(consolidated_df.head())
    print(len(consolidated_df))

    zip_file_path = "src/nhs_waiting_lists/fixtures/consolidated_df.zip"
    csv_file_name_in_zip = "consolidated_df.csv"

    compression_opts = dict(method="zip", archive_name=csv_file_name_in_zip)

    consolidated_df.to_csv(
        zip_file_path,
        index=False,
        compression=compression_opts,
    )


@app.command("exporter-providers")
def bundled_provider_db_exporter(
    ctx: typer.Context,
):
    typer.echo(f"bundled exporter providers ....")

    df = nhs.load_dataset("provider")

    print(df.head())


    zip_file_path = "src/nhs_waiting_lists/fixtures/provider_df.zip"
    csv_file_name_in_zip = "provider_df.csv"

    compression_opts = dict(method="zip", archive_name=csv_file_name_in_zip)

    df.to_csv(
        zip_file_path,
        index=False,
        compression=compression_opts,
    )


@app.command("importer")
def bundled_db_importer(
    ctx: typer.Context,
):
    typer.echo(f"bundled importer ....")

    package_root = Path(nhs.__file__).parent

    zip_file_path = package_root / "fixtures/consolidated_df.zip"
    csv_file_name_in_zip = "consolidated_df.csv"

    with zipfile.ZipFile(zip_file_path, "r") as zf:
        with zf.open(csv_file_name_in_zip) as f:
            df = pd.read_csv(f)
            print(df.head())

            df.to_sql(
                Consolidated.__tablename__,
                con=engine,
                if_exists="append",  # 'append' is fine since we just deleted everything
                index=False,
            )

@app.command("auto")
def auto_setup(
    ctx: typer.Context,
):
    typer.echo(f"auto setup ....")

    init_paths()

    alembic_dir = Path(__file__).parent.parent / "migrations"

    # Create an Alembic configuration object
    alembic_cfg = Config(alembic_dir / "alembic.ini")
    alembic_cfg.set_main_option("script_location", str(alembic_dir))

    command.upgrade(alembic_cfg, "head")
