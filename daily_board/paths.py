import sys
from pathlib import Path

from daily_board.constants import HTML_FILE, OPINET_CONFIG_FILE


def project_root() -> Path:
    """개발 중 프로젝트 루트 또는 PyInstaller 임시 리소스 폴더를 반환합니다."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parent.parent


def resource_dir() -> Path:
    return project_root()


def executable_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return project_root() / "daily_board_launcher.pyw"


def executable_dir() -> Path:
    return executable_path().parent


def html_path() -> Path:
    return resource_dir() / HTML_FILE


def opinet_config_path() -> Path:
    return executable_dir() / OPINET_CONFIG_FILE
