from typing import Annotated, Optional

import typer
from rich import inspect
import tempfile

# import pprint

from nhs_waiting_lists import (
    __app_name__,
    __version__,
)
from nhs_waiting_lists.config.app_config import AppConfig


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


def get_callback():

    # noinspection PyUnusedLocal
    def callback(
        ctx: typer.Context,
        _: Annotated[
            Optional[bool],
            typer.Option(
                "--version",
                "-V",
                callback=_version_callback,
                is_eager=True,
            ),
        ] = None,
        verbose: Annotated[
            Optional[int],
            typer.Option(
                ...,
                "--verbose",
                "-v",
                count=True,
                help="increase verbosity",
                show_default=False,
                show_envvar=False,
                min=0,
                # max=1000,
                # callback=callback_verbose,
                # hidden=True,
            ),
        ] = None,
    ):
        if ctx.invoked_subcommand is None:
            typer.echo("No subcommand invoked")
            ctx.get_help()
            return

        # inspect(ctx.params, title="inspecting ctx.params in main callback")

        if not ctx.obj:
            ctx.obj = {}
            # ctx.obj["configuration"] = Configuration(host=ctx.params["base_url"])

            # def cleanup(str: str):
            #     # print(f"cleaning up requests_debugger: {message}")
            #     ctx.obj["temp_dir"].cleanup()



            ctx.obj["temp_dir"] = tempfile.TemporaryDirectory()
            config_dict: dict[str, any] = {}
            config = AppConfig(**config_dict)

            # atexit.register(cleanup, "atexit")
            # signal.signal(signal.SIGINT, lambda signum, frame: cleanup("sigint"))
            # signal.signal(signal.SIGTERM, lambda signum, frame: cleanup("sigterm"))
        # inspect(ctx)

    return callback
