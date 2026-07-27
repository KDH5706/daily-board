import ctypes
import time
import webbrowser

from daily_board.constants import SW_SHOWNORMAL


def open_browser(url: str, delay_seconds: float = 0) -> None:
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    try:
        if webbrowser.open(url, new=1, autoraise=True):
            return
    except Exception:
        pass
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "open", url, None, None, SW_SHOWNORMAL
        )
    except Exception:
        pass
