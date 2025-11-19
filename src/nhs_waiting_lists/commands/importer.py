from pathlib import Path
from typing import Optional

import typer
from rich import inspect
from typing_extensions import Annotated


from sqlalchemy import create_engine

from nhs_waiting_lists.importer.providers import load_providers
from nhs_waiting_lists.utils.proj_paths import find_project_root
from nhs_waiting_lists.utils.utils import get

app = typer.Typer(name="import", no_args_is_help=True)

@app.callback()
def importer_callback(ctx: typer.Context):
    # inspect(ctx.obj, title="inspecting ctx.obj in voices callback")
    typer.echo(f"in the providers callback")


@app.command("auto")
def auto_import(
        ctx: typer.Context,
):
    typer.echo(f"auto importing the providers ....")


def local_file_parser(local_file: str):
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
