import ctypes


def show_error(message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(None, message, "Daily Board 오류", 0x10)
    except Exception:
        pass
