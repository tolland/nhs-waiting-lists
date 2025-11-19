import typer
from rich.console import Console

from nhs_waiting_lists.commands import provider, scraper, importer

console = Console()

from nhs_waiting_lists.callbacks import get_callback


def create_app() -> typer.Typer:
    callback = get_callback()
    cli = typer.Typer(
        no_args_is_help=True,
        # add_completion=False,
        pretty_exceptions_enable=False,
        rich_markup_mode="rich",
        pretty_exceptions_short=False,
        add_completion=False,
        # @TODO according to doc, this should work. but does not
        # <https://typer.tiangolo.com/tutorial/commands/callback/#adding-a-callback-on-creation>
        # callback=callback,
    )
    cli.callback()(callback)

    # typer.echo("create_app")

    cli.add_typer(provider.app)
    cli.add_typer(scraper.app)
    cli.add_typer(importer.app)
    return cli


def run_cli():
    app = create_app()
    app()
