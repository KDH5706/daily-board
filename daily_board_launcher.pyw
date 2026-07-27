from daily_board.app import run
from daily_board.windows.dialogs import show_error


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        show_error(
            "Daily Board 실행 중 오류가 발생했습니다.\n\n"
            f"{type(error).__name__}: {error}"
        )
