from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import platformdirs
import typer


class AppConfig(BaseSettings):
    debug: bool = False
    timeout: int = 30

    model_config = SettingsConfigDict(
        env_file=Path(platformdirs.user_config_dir("myapp")) / "config.env",
        env_prefix="MYAPP_",
    )
