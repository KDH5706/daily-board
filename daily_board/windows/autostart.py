import sys
import winreg

from daily_board.constants import AUTOSTART_NAME
from daily_board.paths import executable_path

_REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def register_windows_autostart() -> bool:
    try:
        if not getattr(sys, "frozen", False):
            return False
        command = f'"{executable_path()}" --autostart'
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, command)
        return True
    except OSError:
        return False


def unregister_windows_autostart() -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, AUTOSTART_NAME)
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


def is_windows_autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REGISTRY_PATH,
            0,
            winreg.KEY_READ,
        ) as key:
            value, _ = winreg.QueryValueEx(key, AUTOSTART_NAME)
        valid_commands = {
            f'"{executable_path()}"',
            f'"{executable_path()}" --autostart',
        }
        return value in valid_commands
    except (FileNotFoundError, OSError):
        return False
