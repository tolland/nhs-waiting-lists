from pathlib import Path
from typing import Optional

import typer
from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import proj_db_path, DB_FILE
from nhs_waiting_lists.importer.providers import load_providers
from nhs_waiting_lists.importer.rtt import import_all_rtt_from_jsonl
from nhs_waiting_lists.utils.proj_paths import find_project_root
from nhs_waiting_lists.utils.utils import get
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
    typer.echo(f"in the providers callback")


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


@app.command("rtt")
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
):
    """
    Import rtt data, optionally restricted to period ranges
    """

    print(f"in the rtt callback start_period={start_period}")

    import_all_rtt_from_jsonl(
        check_only=True,
        start_period=start_period,
        end_period=end_period,
    )

