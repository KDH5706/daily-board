import atexit
import mimetypes
import os
import sys
import threading
import time

from daily_board.browser import open_browser
from daily_board.constants import HOST, HTML_FILE, MUTEX_NAME, OPINET_CONFIG_FILE, START_PORT
from daily_board.paths import html_path, opinet_config_path, resource_dir
from daily_board.server.handler import QuietRequestHandler
from daily_board.server.http_server import DailyBoardHTTPServer, find_available_port
from daily_board.windows.dialogs import show_error
from daily_board.windows.single_instance import SingleInstance

from daily_board.constants import (
    BROWSER_REOPEN_COOLDOWN_SECONDS,
    HEARTBEAT_TIMEOUT_SECONDS,
)


def register_mime_types() -> None:
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("application/javascript", ".mjs")
    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("application/json", ".json")


def run() -> None:
    register_mime_types()
    single_instance = SingleInstance(MUTEX_NAME)
    if not single_instance.acquire():
        return
    atexit.register(single_instance.release)

    internal_html_path = html_path()
    external_config_path = opinet_config_path()
    if not internal_html_path.is_file():
        show_error(f"{HTML_FILE} 파일을 찾을 수 없습니다.\n\n검색 위치:\n{internal_html_path}")
        return
    if not external_config_path.is_file():
        show_error(
            f"{OPINET_CONFIG_FILE} 파일을 찾을 수 없습니다.\n\n"
            f"검색 위치:\n{external_config_path}\n\n"
            f"{OPINET_CONFIG_FILE} 파일을 DailyBoard.exe와 같은 폴더에 두세요."
        )
        return

    os.chdir(resource_dir())
    try:
        port = find_available_port(START_PORT)
        server = DailyBoardHTTPServer((HOST, port), QuietRequestHandler)
    except Exception as error:
        show_error(f"Daily Board 서버를 시작하지 못했습니다.\n\n{error}")
        return

    atexit.register(server.server_close)
    server_thread = threading.Thread(
        target=server.serve_forever,
        name="DailyBoardHTTPServer",
        daemon=True,
    )
    server_thread.start()

    url = f"http://{HOST}:{port}/{HTML_FILE}"
    browser_delay = (
        5 if "--autostart" in sys.argv else 0
    )
    threading.Thread(
        target=open_browser,
        args=(url, browser_delay),
        name="DailyBoardBrowserLauncher",
        daemon=True,
    ).start()

    last_browser_launch_at = time.monotonic()

    try:
        while server_thread.is_alive():

            # 명시적인 종료 요청만 서버 종료
            if server.state.should_shutdown():
                break
            # heartbeat가 끊긴 경우
            heartbeat_age = (
                server.state.seconds_since_heartbeat()
            )
            if (
                heartbeat_age
                > HEARTBEAT_TIMEOUT_SECONDS
            ):
                now = time.monotonic()

                if(
                    now - last_browser_launch_at >= BROWSER_REOPEN_COOLDOWN_SECONDS
                ):
                    threading.Thread(
                        target=open_browser,
                        args=(url, 0),
                        name="DailyBoardBrowserRelauncher",
                        daemon=True,
                    ).start()

                    last_browser_launch_at = now
            
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()

        if server_thread.is_alive():
            server_thread.join(timeout=3)
    # try:
    #     while server_thread.is_alive():
    #         if server.state.should_stop():
    #             break
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     pass
    # finally:
    #     server.shutdown()
    #     server.server_close()
    #     if server_thread.is_alive():
    #         server_thread.join(timeout=3)
