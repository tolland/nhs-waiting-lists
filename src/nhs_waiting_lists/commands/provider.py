import sys
from typing import Optional

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine
from sqlalchemy import text, bindparam

from nhs_waiting_lists.constants import proj_db_path, LARGE_ACUTE_PROVIDER_CODES
from nhs_waiting_lists.utils.utils import find_project_root

app = typer.Typer(name="provider", no_args_is_help=True)


@app.callback()
def providers_callback(ctx: typer.Context):
    # inspect(ctx.obj, title="inspecting ctx.obj in voices callback")
    typer.echo(f"in the providers callback")


@app.command("list")
def list_providers(
    ctx: typer.Context,
    language: Optional[str] = typer.Option(None, "--language", "-l"),
    gender: Optional[str] = typer.Option(None, "--gender", "-g"),
):
    typer.echo(f"Listing the providers ....")


@app.command("report")
def providers_report(
    ctx: typer.Context,
):
    typer.echo(f"reporting the providers ....")

    project_root = find_project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    DB_PATH = project_root / proj_db_path / "nhs_rttwtd.db"
    DATA_DIR = "./data"

    # conn = sqlite3.connect(DB_PATH)

    conn = create_engine(f"sqlite:///{DB_PATH}")

    console = Console()

    query = text(
        """
                 SELECT c.period,
                        COALESCE(NULLIF((strftime('%m', c.period || '-01') + 2) / 3, 0), 4) AS Quarter ,
                        c.provider,
                        c.treatment,
                        c.incomplete,
                        c.admitted,
                        c.nonadmitted,
                        c.new_periods,
                        c.incomplete_prev,
                        c.wait_pct_lt_18,
                        p.provider_name
                 FROM consolidated AS c
                          INNER JOIN providers AS p ON c.provider = p.provider_code
                 WHERE provider IN :provider_codes
                 GROUP BY p.provider_code
                 ORDER BY p.provider_code ASC, treatment ASC, period ASC; \
                 """
    ).bindparams(
        bindparam("provider_codes", expanding=True),
        # bindparam('treatment_codes', expanding=True)
    )

    df = pd.read_sql(
        query,
        conn,
        params={  # type: ignore[arg-type]
            "provider_codes": LARGE_ACUTE_PROVIDER_CODES,
        },
    )
    # df.query("provider == 'RAJ' and treatment == 'C_999' and period == '2025-08'")
    df

    # Convert df to rich Table
    table = Table(title="Consolidated Data")
    for col in df.columns:
        table.add_column(col)

    for _, row in df.iterrows():
        table.add_row(*[str(v) for v in row])

    console.print(table)
