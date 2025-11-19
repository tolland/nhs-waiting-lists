import os
import sys
from pathlib import Path

CYGWIN = sys.platform.startswith("cygwin")
WIN = sys.platform.startswith("win")


class XDGBasedir:
    # this function is derived from the typer library
    @staticmethod
    def _posixify(name: str) -> str:
        return "-".join(name.split()).lower()

    @staticmethod
    def get_home_dir() -> Path:
        """Encapsulates os.path.expanduser for easier mocking."""
        # key = "APPDATA" if roaming else "LOCALAPPDATA"
        # folder = os.environ.get(key)
        # if folder is None:
        #     folder = os.path.expanduser("~")
        # return os.path.join(folder, app_name)
        return Path.home()

    @classmethod
    def get_xdg_state_home(
        cls,
    ) -> Path:
        """Encapsulates os.environ.get for easier mocking."""
        if WIN:
            raise NotImplementedError("Not implemented for Windows")

        return os.environ.get("XDG_STATE_HOME", cls.get_home_dir() / ".local/state")

    @classmethod
    def get_xdg_config_home(
        cls,
    ) -> Path:
        """Encapsulates os.environ.get for easier mocking."""
        return os.environ.get("XDG_CONFIG_HOME") or cls.get_home_dir() / ".config"

    # this function is derived from the typer get_app_dir library method
    @classmethod
    def get_log_dir(
        cls,
        app_name: str,
        roaming: bool = True,
        force_posix: bool = False,
    ) -> Path:
        if force_posix:
            return cls.get_xdg_state_home() / "logs" / cls._posixify(app_name)

        return cls.get_xdg_state_home() / app_name

    @classmethod
    def get_app_dir(
        cls,
        app_name: str,
        roaming: bool = True,
        force_posix: bool = False,
    ) -> Path:
        if force_posix:
            return cls.get_home_dir() / f".{cls._posixify(app_name)}"
        return cls.get_xdg_config_home() / app_name

    @classmethod
    def get_data_dir(
        cls,
        app_name: str,
        roaming: bool = True,
        force_posix: bool = False,
    ) -> Path:
        if force_posix:
            return cls.get_home_dir() / f".{cls._posixify(app_name)}" / "data"
        return cls.get_xdg_state_home() / app_name