from pathlib import Path
from typing import Optional

import typer
from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import proj_db_path, DB_FILE
from nhs_waiting_lists.importer.outpatient_activity import import_outpatient_activity_period
from nhs_waiting_lists.importer.providers import load_providers
from nhs_waiting_lists.importer.rtt import import_all_rtt_from_jsonl
from nhs_waiting_lists.importer.rtt_metrics import import_rtt_to_rtt_metrics
from nhs_waiting_lists.importer.rtt_pathways import import_rtt_to_rtt_pathways
from nhs_waiting_lists.utils.date_field_parsing import generate_periods
from nhs_waiting_lists.utils.utils import get, find_project_root
from nhs_waiting_lists.utils.xdg import XDGBasedir
from rich import inspect
from sqlalchemy import create_engine
from typing_extensions import Annotated

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / DB_FILE

app = typer.Typer(name="import", no_args_is_help=True)


@app.callback()
def importer_callback(ctx: typer.Context):
    # inspect(ctx.obj, title="inspecting ctx.obj in voices callback")
    typer.echo(f"in the importer callback")


def local_file_parser(local_file: str):
    """
    The purpose of this function is to provide the validation of
    a path given to an importer, to allow use of various formats
    such as prefixe with a schema.
    """
    print(f"in the local file parser")
    if local_file.startswith("file:///"):
        print(f"stripping prefix")
        return local_file.removeprefix("file://")
    elif local_file.startswith("https://"):
        data = get(local_file)
        import tempfile

        new_file, filename = tempfile.mkstemp()

        with open(new_file, "wb") as f:
            f.write(data.content)

        return filename

    return local_file


@app.command("excel")
def excel_import(
    _ctx: typer.Context,
    source_filepath: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            # writable=False,
            readable=True,
            resolve_path=True,
            # parser=local_file_parser,
        ),
    ],
):
    typer.echo(f"auto importing the file ....")
    inspect(source_filepath, title="inspecting source_filepath")
    project_root = find_project_root()
    DB_PATH = project_root / "db/nhs_rttwtd.db"

    conn = create_engine(f"sqlite:///{DB_PATH}", echo=True)


@app.command("providers")
def import_providers(
    _ctx: typer.Context,
    source_filepath: Annotated[
        Optional[Path],
        typer.Option(
            file_okay=True,
            exists=True,
            dir_okay=False,
            # writable=False,
            readable=True,
            resolve_path=True,
            # parser=local_file_parser,
        ),
    ] = None,
):
    """
    Import providers from a file. currently only acute trusts.
    """

    typer.echo(f"auto importing the file ....")
    inspect(source_filepath, title="inspecting source_filepath")

    # Validate file exists if provided
    if source_filepath is not None and not source_filepath.exists():
        typer.echo(f"Error: File {source_filepath} does not exist")
        raise typer.Exit(1)

    load_providers()

    conn = create_engine(f"sqlite:///{DB_PATH}", echo=True)


@app.command("rtt-raw")
def import_rtt(
    _ctx: typer.Context,
    start_period: Annotated[
        Optional[str],
        typer.Option("--start-period", help="Start period in YYYY-MM format")
    ] = None,
    end_period: Annotated[
        Optional[str],
        typer.Option("--end-period", help="End period in YYYY-MM format")
    ] = None,
    check_only: Annotated[
        Optional[bool],
        typer.Option("--check-only", help="Check only, do not import")
    ] = False,
):
    """
    Import the raw RTT data from csv files downloaded by the scrapy spider. This is the first stage of import. Prerequisite for further processing.
    """

    print(f"in the rtt callback {start_period=} {end_period=}")

    import_all_rtt_from_jsonl(
        check_only=check_only,
        start_period=start_period,
        end_period=end_period,
    )


@app.command("rtt-metrics")
def import_rtt(
    _ctx: typer.Context,
    start_period: Annotated[
        Optional[str],
        typer.Option("--start-period", help="Start period in YYYY-MM format")
    ] = None,
    end_period: Annotated[
        Optional[str],
        typer.Option("--end-period", help="End period in YYYY-MM format")
    ] = None,
    check_only: Annotated[
        Optional[bool],
        typer.Option("--check-only", help="Check only, do not import")
    ] = False,
):
    """
    Convert the long format into wide with summarized types and aggregated by
    provider, parent org, commissioning org
    """

    print(f"in the rtt-metrics command method {start_period=} {end_period=}")

    import_rtt_to_rtt_metrics(
        check_only=check_only,
        start_period=start_period,
        end_period=end_period,
    )



@app.command("rtt-pathways")
def import_rtt_pathways(
    _ctx: typer.Context,
    start_period: Annotated[
        Optional[str],
        typer.Option("--start-period", help="Start period in YYYY-MM format")
    ] = None,
    end_period: Annotated[
        Optional[str],
        typer.Option("--end-period", help="End period in YYYY-MM format")
    ] = None,
    check_only: Annotated[
        Optional[bool],
        typer.Option("--check-only", help="Check only, do not import")
    ] = False,
):
    """
    Extract the pathways from the RTT data into dedicated tables.
    admitted
    nonadmitted
    incomplete
    new_periods
    incomplete_with_dta
    """

    print(f"in the rtt-pathways command method {start_period=} {end_period=}")

    import_rtt_to_rtt_pathways(
        check_only=check_only,
        start_period=start_period,
        end_period=end_period,
    )


@app.command("outpatient-activity-raw")
def import_outp_raw(
    _ctx: typer.Context,
    start_period: Annotated[
        Optional[str],
        typer.Option("--start-period", help="Start period in YYYY-MM format")
    ] = "2023-04",
    end_period: Annotated[
        Optional[str],
        typer.Option("--end-period", help="End period in YYYY-MM format")
    ] = None,
    check_only: Annotated[
        Optional[bool],
        typer.Option("--check-only", help="Check only, do not import")
    ] = False,
):
    """
    Parse the raw outpatient activity data from csv and xlsx files downloaded by the scrapy spider.
    """

    print(f"in the outpatients actitivity raw callback start_period={start_period}")

    try:
        periods = generate_periods(start_period, end_period)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Importing periods: {', '.join(periods)}")

    for period in periods:
        typer.echo(f"Processing period {period}...")
        import_outpatient_activity_period(
            check_only=check_only,
            period=period,
        )
