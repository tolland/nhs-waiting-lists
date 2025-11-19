from typing import Optional

import typer
from nhs_waiting_lists.core import NhsCtlCore
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# from bacula_ctl.core.main import BaculaCtlCore

app = typer.Typer(name="scraper", no_args_is_help=True)

# Create the core
core = NhsCtlCore()


@app.callback()
def scraper_callback(ctx: typer.Context):
    # inspect(ctx.obj, title="inspecting ctx.obj in voices callback")
    typer.echo(f"in the scraper callback")


@app.command("list")
def list_scrapers(
        ctx: typer.Context,
):
    """
    List all available data scrapers.
    """
    typer.echo("Available scrapers:")
    typer.echo("")
    typer.echo("  rtt                    - RTT waiting times (monthly, per-provider, per-specialty)")
    typer.echo("  outpatients-activity   - Outpatient attendance data (yearly, per-provider)")
    typer.echo("  providers              - NHS Oversight Framework provider metadata")
    typer.echo("")
    typer.echo("Usage: nhsctl scraper <scraper-name>")

@app.command("outpatients-activity")
def outpatients_activity(
        ctx: typer.Context,
):
    """
    Scrape the outpatients activity time series data. This data set relates the
    counts of attendence types to provider and treatment on a per-year basis.
    """

    process = CrawlerProcess(get_project_settings())

    process.crawl("outpatient-activity")
    process.start()

@app.command("rtt")
def rtt_waiting_times(
        ctx: typer.Context,
):
    """
    Scrape the referral-to-treatment waiting times data. This is a per-provder,
    per-treatment per-month dataset. Quite a lot of data here.
    """

    process = CrawlerProcess(get_project_settings())

    process.crawl("rtt-waiting-times")
    process.start()

@app.command("providers")
def scrape_providers(
        ctx: typer.Context,
):
    """
    Scrape the NHS Oversight Framework provider metadata CSV. This information is
    used to provide more information about the provider codes being referenced in
    the RTT and outpatient activity datasets, including trust type, region, and
    performance metrics.
    """

    process = CrawlerProcess(get_project_settings())

    process.crawl("provider-oversight")
    process.start()
