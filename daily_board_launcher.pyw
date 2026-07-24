import atexit
import contextlib
import ctypes
import json
import mimetypes
import os
import socket
import sys
import threading
import time
import webbrowser
import winreg

from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode, urlparse
from urllib.request import Request, urlopen


# Windows 환경의 MIME 데이터베이스 상태와 관계없이
# ES Module 및 정적 리소스 MIME 타입을 확실하게 등록합니다.
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")


# ============================================================
# 기본 설정
# ============================================================

HOST = "127.0.0.1"
START_PORT = 8000
PORT_SEARCH_COUNT = 100

HTML_FILE = "src/index.html"
OPINET_CONFIG_FILE = "opinet_API.json"

OPINET_DETAIL_URL = "https://www.opinet.co.kr/api/detailById.do"
OPINET_REQUEST_TIMEOUT_SECONDS = 12
OPINET_MAX_WORKERS = 5

# 표시할 유종
PRODUCT_NAMES = {
    "B027": "휘발유",
    "D047": "경유",
}

# HTML이 보내는 heartbeat 간격보다 충분히 크게 설정합니다.
HEARTBEAT_TIMEOUT_SECONDS = 10

# EXE가 실행된 후 최초 heartbeat를 기다리는 시간입니다.
STARTUP_GRACE_SECONDS = 30

# pagehide/sendBeacon 수신 직후 바로 종료하지 않고 기다리는 시간입니다.
CLOSE_GRACE_SECONDS = 5

# Windows 시작 프로그램 등록 이름
AUTOSTART_NAME = "DailyBoard"

# 중복 실행 방지용 Windows Mutex 이름
MUTEX_NAME = "Local\\DailyBoardLauncherSingleton"


# ============================================================
# Windows API 상수
# ============================================================

ERROR_ALREADY_EXISTS = 183
SW_SHOWNORMAL = 1


# ============================================================
# 경로 처리
# ============================================================

def resource_dir() -> Path:
    """
    HTML처럼 PyInstaller에 포함되는 내부 리소스의 폴더를 반환합니다.

    개발 중:
        Python 파일이 있는 폴더

    PyInstaller --onefile 실행 중:
        sys._MEIPASS 임시 압축 해제 폴더
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()

    return Path(__file__).resolve().parent


def executable_path() -> Path:
    """
    현재 실행 중인 EXE 또는 Python 스크립트 경로를 반환합니다.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()

    return Path(__file__).resolve()


def executable_dir() -> Path:
    """
    사용자가 수정하는 외부 설정 파일의 기준 폴더를 반환합니다.

    EXE 실행 중:
        DailyBoard.exe가 실제로 위치한 폴더

    Python 실행 중:
        daily_board_launcher.pyw가 위치한 폴더
    """
    return executable_path().parent


def html_path() -> Path:
    return resource_dir() / HTML_FILE


def opinet_config_path() -> Path:
    # opinet_API.json은 EXE 내부가 아니라 EXE와 같은 폴더에서 읽습니다.
    return executable_dir() / OPINET_CONFIG_FILE


# ============================================================
# Windows 자동 실행 등록
# ============================================================

def register_windows_autostart() -> bool:
    """
    현재 사용자(HKCU)의 Windows Run 레지스트리에 등록합니다.
    관리자 권한은 필요하지 않습니다.
    """
    try:
        # Python 소스 실행 중에는 자동 실행을 등록하지 않습니다.
        if not getattr(sys, "frozen", False):
            return False

        command = f'"{executable_path()}" --autostart'
        registry_path = (
            r"Software\Microsoft\Windows"
            r"\CurrentVersion\Run"
        )

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            registry_path,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(
                key,
                AUTOSTART_NAME,
                0,
                winreg.REG_SZ,
                command,
            )

        return True

    except OSError:
        return False


def unregister_windows_autostart() -> bool:
    """
    Windows 자동 실행 등록을 제거합니다.
    """
    try:
        registry_path = (
            r"Software\Microsoft\Windows"
            r"\CurrentVersion\Run"
        )

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            registry_path,
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
    """
    현재 EXE가 Windows 자동 실행으로 등록되어 있는지 확인합니다.
    """
    try:
        registry_path = (
            r"Software\Microsoft\Windows"
            r"\CurrentVersion\Run"
        )

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            registry_path,
            0,
            winreg.KEY_READ,
        ) as key:
            value, _ = winreg.QueryValueEx(
                key,
                AUTOSTART_NAME,
            )

        valid_commands = {
            f'"{executable_path()}"',
            f'"{executable_path()}" --autostart',
        }
        return value in valid_commands

    except (FileNotFoundError, OSError):
        return False


# ============================================================
# 중복 실행 방지
# ============================================================

class SingleInstance:
    """
    Windows Named Mutex를 사용해 DailyBoard.exe의 중복 실행을 방지합니다.
    """

    def __init__(self, mutex_name: str):
        self.mutex_name = mutex_name
        self.handle = None

    def acquire(self) -> bool:
        kernel32 = ctypes.windll.kernel32

        self.handle = kernel32.CreateMutexW(
            None,
            False,
            self.mutex_name,
        )

        if not self.handle:
            return False

        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(self.handle)
            self.handle = None
            return False

        return True

    def release(self) -> None:
        if self.handle:
            ctypes.windll.kernel32.ReleaseMutex(self.handle)
            ctypes.windll.kernel32.CloseHandle(self.handle)
            self.handle = None


# ============================================================
# 서버 상태 관리
# ============================================================

class ServerState:
    """
    HTML 페이지의 heartbeat와 닫힘 요청을 관리합니다.
    """

    def __init__(self):
        now = time.monotonic()
        self.started_at = now
        self.last_heartbeat = None
        self.close_requested_at = None
        self.has_received_heartbeat = False
        self.lock = threading.Lock()

    def heartbeat(self) -> None:
        with self.lock:
            self.last_heartbeat = time.monotonic()
            self.has_received_heartbeat = True
            self.close_requested_at = None

    def request_close(self) -> None:
        with self.lock:
            self.close_requested_at = time.monotonic()

    def should_stop(self) -> bool:
        with self.lock:
            now = time.monotonic()

            if not self.has_received_heartbeat:
                return now - self.started_at > STARTUP_GRACE_SECONDS

            if self.close_requested_at is not None:
                if now - self.close_requested_at > CLOSE_GRACE_SECONDS:
                    return True

            if self.last_heartbeat is not None:
                if now - self.last_heartbeat > HEARTBEAT_TIMEOUT_SECONDS:
                    return True

            return False


SERVER_STATE = ServerState()


# ============================================================
# 오피넷 설정 및 API 처리
# ============================================================

class OpinetError(RuntimeError):
    pass


def load_opinet_config() -> dict:
    """
    EXE와 같은 폴더에 있는 opinet_API.json을 읽고 검증합니다.
    """
    config_path = opinet_config_path()

    if not config_path.is_file():
        raise FileNotFoundError(
            f"{OPINET_CONFIG_FILE} 파일을 찾을 수 없습니다.\n"
            f"파일 위치: {config_path}\n"
            f"{OPINET_CONFIG_FILE}을 DailyBoard.exe와 같은 폴더에 두세요."
        )

    try:
        with config_path.open("r", encoding="utf-8-sig") as file:
            config = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{OPINET_CONFIG_FILE} JSON 형식이 올바르지 않습니다. "
            f"(줄 {error.lineno}, 열 {error.colno})"
        ) from error

    if not isinstance(config, dict):
        raise ValueError(
            f"{OPINET_CONFIG_FILE}의 최상위 값은 JSON 객체여야 합니다."
        )

    code = config.get("code")
    if not isinstance(code, str) or not code.strip():
        raise ValueError(
            f"{OPINET_CONFIG_FILE}에 유효한 code 값이 없습니다."
        )

    normalized = {"code": code.strip()}

    for group_name in ("favorites", "highway"):
        raw_ids = config.get(group_name, [])

        if raw_ids is None:
            raw_ids = []

        if not isinstance(raw_ids, list):
            raise ValueError(
                f"{OPINET_CONFIG_FILE}의 {group_name} 값은 배열이어야 합니다."
            )

        station_ids = []
        seen = set()

        for value in raw_ids:
            if not isinstance(value, str):
                continue

            station_id = value.strip()
            if station_id and station_id not in seen:
                seen.add(station_id)
                station_ids.append(station_id)

        normalized[group_name] = station_ids

    return normalized


def normalize_oil_list(value) -> list:
    """
    OIL_PRICE 또는 OIL 필드가 객체 하나이거나 배열인 경우를 모두 처리합니다.
    """
    if value is None:
        return []

    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        return [value]

    return []


def find_station_record(payload: object) -> dict:
    """
    오피넷 JSON 응답에서 주유소 상세 레코드를 추출합니다.
    일반적으로 RESULT.OIL 구조이지만 변형된 응답도 일부 수용합니다.
    """
    if not isinstance(payload, dict):
        raise OpinetError("오피넷 응답의 최상위 값이 객체가 아닙니다.")

    result = payload.get("RESULT", payload)

    if isinstance(result, dict):
        oil = result.get("OIL")

        if isinstance(oil, list):
            for item in oil:
                if isinstance(item, dict):
                    return item

        if isinstance(oil, dict):
            return oil

        # 오류 응답 메시지 확인
        message = (
            result.get("MESSAGE")
            or result.get("MSG")
            or result.get("message")
        )
        if message:
            raise OpinetError(str(message))

        # 일부 응답이 RESULT 자체를 레코드로 반환하는 경우
        if "OS_NM" in result or "UNI_ID" in result:
            return result

    raise OpinetError("오피넷 응답에서 주유소 상세정보를 찾지 못했습니다.")


def parse_price(value):
    """
    숫자 또는 숫자 문자열을 JSON 숫자로 변환합니다.
    값이 없거나 0 이하이면 None을 반환합니다.
    """
    if value is None:
        return None

    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None

    if number <= 0:
        return None

    if number.is_integer():
        return int(number)

    return number


def fetch_station_detail(api_code: str, station_id: str) -> dict:
    """
    detailById.do를 호출하고 화면에 필요한 정보만 반환합니다.
    """
    query = urlencode({
        "code": api_code,
        "id": station_id,
        "out": "json",
    })
    url = f"{OPINET_DETAIL_URL}?{query}"

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "DailyBoard/1.0",
        },
        method="GET",
    )

    try:
        with urlopen(
            request,
            timeout=OPINET_REQUEST_TIMEOUT_SECONDS,
        ) as response:
            raw_data = response.read()

    except HTTPError as error:
        raise OpinetError(
            f"오피넷 HTTP 오류: {error.code}"
        ) from error

    except URLError as error:
        reason = getattr(error, "reason", error)
        raise OpinetError(
            f"오피넷 연결 실패: {reason}"
        ) from error

    except TimeoutError as error:
        raise OpinetError("오피넷 요청 시간이 초과되었습니다.") from error

    try:
        text = raw_data.decode("utf-8-sig")
        payload = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OpinetError(
            "오피넷 응답을 JSON으로 해석하지 못했습니다."
        ) from error

    station = find_station_record(payload)

    station_name = str(
        station.get("OS_NM")
        or station.get("UNI_ID")
        or station_id
    ).strip()

    prices = {
        code: {
            "productCode": code,
            "productName": name,
            "price": None,
            "tradeDate": None,
            "tradeTime": None,
        }
        for code, name in PRODUCT_NAMES.items()
    }

    oil_prices = normalize_oil_list(
        station.get("OIL_PRICE")
        or station.get("OIL_PRICE_LIST")
    )

    # 응답에 따라 OIL_PRICE가 {"OIL": [...]} 형태일 수 있습니다.
    if len(oil_prices) == 1:
        nested = oil_prices[0].get("OIL")
        if nested is not None:
            oil_prices = normalize_oil_list(nested)

    for oil in oil_prices:
        product_code = str(oil.get("PRODCD", "")).strip()

        if product_code not in prices:
            continue

        prices[product_code] = {
            "productCode": product_code,
            "productName": PRODUCT_NAMES[product_code],
            "price": parse_price(oil.get("PRICE")),
            "tradeDate": oil.get("TRADE_DT"),
            "tradeTime": oil.get("TRADE_TM"),
        }

    return {
        "id": str(station.get("UNI_ID") or station_id),
        "name": station_name,
        "brandCode": station.get("POLL_DIV_CD"),
        "address": station.get("NEW_ADR") or station.get("VAN_ADR"),
        "prices": prices,
    }


def fetch_group(
    group_name: str,
    station_ids: list[str],
    api_code: str,
) -> list[dict]:
    """
    한 그룹의 주유소들을 병렬로 조회하되 설정 파일의 순서를 유지합니다.
    """
    if not station_ids:
        return []

    indexed_results = [None] * len(station_ids)

    worker_count = min(
        OPINET_MAX_WORKERS,
        max(1, len(station_ids)),
    )

    with ThreadPoolExecutor(
        max_workers=worker_count,
        thread_name_prefix=f"Opinet-{group_name}",
    ) as executor:
        futures = {
            executor.submit(
                fetch_station_detail,
                api_code,
                station_id,
            ): (index, station_id)
            for index, station_id in enumerate(station_ids)
        }

        for future in as_completed(futures):
            index, station_id = futures[future]

            try:
                indexed_results[index] = future.result()
            except Exception as error:
                indexed_results[index] = {
                    "id": station_id,
                    "name": station_id,
                    "brandCode": None,
                    "address": None,
                    "prices": {
                        code: {
                            "productCode": code,
                            "productName": name,
                            "price": None,
                            "tradeDate": None,
                            "tradeTime": None,
                        }
                        for code, name in PRODUCT_NAMES.items()
                    },
                    "error": str(error),
                }

    return indexed_results


def build_opinet_response() -> dict:
    """
    설정 파일의 즐겨찾기/고속도로 주유소를 조회해 프런트용 JSON을 만듭니다.
    """
    config = load_opinet_config()
    api_code = config["code"]

    groups = {}

    # 그룹 두 개를 동시에 조회합니다.
    with ThreadPoolExecutor(
        max_workers=2,
        thread_name_prefix="OpinetGroup",
    ) as executor:
        future_map = {
            executor.submit(
                fetch_group,
                "favorites",
                config["favorites"],
                api_code,
            ): "favorites",
            executor.submit(
                fetch_group,
                "highway",
                config["highway"],
                api_code,
            ): "highway",
        }

        for future in as_completed(future_map):
            group_name = future_map[future]
            groups[group_name] = future.result()

    # 프런트에서 항상 같은 키 순서로 받을 수 있게 재구성합니다.
    groups = {
        "favorites": groups.get("favorites", []),
        "highway": groups.get("highway", []),
    }

    failed_count = sum(
        1
        for stations in groups.values()
        for station in stations
        if station.get("error")
    )

    return {
        "success": True,
        "updatedAt": time.strftime(
            "%Y-%m-%dT%H:%M:%S%z",
            time.localtime(),
        ),
        "groups": groups,
        "summary": {
            "total": sum(len(items) for items in groups.values()),
            "failed": failed_count,
        },
    }


# ============================================================
# HTTP 서버
# ============================================================

class QuietRequestHandler(SimpleHTTPRequestHandler):
    """
    콘솔 로그를 출력하지 않는 로컬 HTTP 요청 처리기입니다.
    JavaScript ES Module이 정상 로드되도록 MIME 타입을 명시합니다.
    """

    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript",
        ".mjs": "application/javascript",
        ".css": "text/css",
        ".json": "application/json",
        ".html": "text/html",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
    }

    def log_message(self, format_string, *args):
        pass

    def end_headers(self):
        self.send_header(
            "Cache-Control",
            "no-store, no-cache, must-revalidate, max-age=0",
        )
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def send_empty_response(self, status_code: int = 204):
        self.send_response(status_code)
        self.end_headers()

    def send_json(self, data: object, status_code: int = 200):
        body = json.dumps(
            data,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path = unquote(urlparse(self.path).path)

        if path == "/__heartbeat__":
            SERVER_STATE.heartbeat()
            self.send_empty_response(204)
            return

        if path == "/__closed__":
            SERVER_STATE.request_close()
            self.send_empty_response(204)
            return

        if path == "/__autostart__":
            try:
                content_length = int(
                    self.headers.get("Content-Length", "0")
                )
                raw_body = self.rfile.read(content_length)
                data = json.loads(raw_body.decode("utf-8"))

                enabled = bool(data.get("enabled"))

                if enabled:
                    success = register_windows_autostart()
                else:
                    success = unregister_windows_autostart()

                current_state = is_windows_autostart_enabled()

                self.send_json(
                    {
                        "success": success,
                        "enabled": current_state,
                    },
                    200 if success else 500,
                )

            except Exception as error:
                self.send_json(
                    {
                        "success": False,
                        "error": str(error),
                    },
                    400,
                )

            return

        self.send_error(404, "Not Found")

    def do_GET(self):
        path = unquote(urlparse(self.path).path)

        if path == "/__heartbeat__":
            SERVER_STATE.heartbeat()
            self.send_empty_response(204)
            return

        if path == "/__status__":
            self.send_json({
                "status": "running",
                "configPath": str(opinet_config_path()),
            })
            return

        if path == "/__autostart__":
            self.send_json({
                "enabled": is_windows_autostart_enabled()
            })
            return

        if path == "/__opinet__":
            try:
                result = build_opinet_response()
                self.send_json(result, 200)

            except FileNotFoundError as error:
                self.send_json(
                    {
                        "success": False,
                        "error": str(error),
                        "configPath": str(opinet_config_path()),
                    },
                    404,
                )

            except (ValueError, OpinetError) as error:
                self.send_json(
                    {
                        "success": False,
                        "error": str(error),
                    },
                    400,
                )

            except Exception as error:
                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "오피넷 정보를 처리하는 중 오류가 발생했습니다. "
                            f"{type(error).__name__}: {error}"
                        ),
                    },
                    500,
                )

            return

        if path == "/":
            self.send_response(302)
            self.send_header("Location", f"/{HTML_FILE}")
            self.end_headers()
            return

        super().do_GET()


class DailyBoardHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


# ============================================================
# 포트 선택
# ============================================================

def find_available_port(
    start_port: int,
    attempts: int = PORT_SEARCH_COUNT,
) -> int:
    for port in range(start_port, start_port + attempts):
        with contextlib.closing(
            socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM,
            )
        ) as sock:
            try:
                sock.bind((HOST, port))
                return port
            except OSError:
                continue

    raise RuntimeError(
        "사용 가능한 localhost 포트를 찾지 못했습니다."
    )


# ============================================================
# 브라우저 실행
# ============================================================

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
            None,
            "open",
            url,
            None,
            None,
            SW_SHOWNORMAL,
        )
    except Exception:
        pass


# ============================================================
# 오류 처리
# ============================================================

def show_error(message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(
            None,
            message,
            "Daily Board 오류",
            0x10,
        )
    except Exception:
        pass


# ============================================================
# 메인 실행
# ============================================================

def main() -> None:
    single_instance = SingleInstance(MUTEX_NAME)

    if not single_instance.acquire():
        return

    atexit.register(single_instance.release)

    internal_html_path = html_path()
    external_config_path = opinet_config_path()

    if not internal_html_path.is_file():
        show_error(
            f"{HTML_FILE} 파일을 찾을 수 없습니다.\n\n"
            f"검색 위치:\n{internal_html_path}"
        )
        return

    if not external_config_path.is_file():
        show_error(
            f"{OPINET_CONFIG_FILE} 파일을 찾을 수 없습니다.\n\n"
            f"검색 위치:\n{external_config_path}\n\n"
            f"{OPINET_CONFIG_FILE} 파일을 DailyBoard.exe와 "
            "같은 폴더에 두세요."
        )
        return

    # SimpleHTTPRequestHandler가 내부 HTML 파일을 제공하도록
    # PyInstaller 리소스 폴더로 작업 디렉터리를 변경합니다.
    os.chdir(resource_dir())

    try:
        port = find_available_port(START_PORT)
        server = DailyBoardHTTPServer(
            (HOST, port),
            QuietRequestHandler,
        )

    except Exception as error:
        show_error(
            "Daily Board 서버를 시작하지 못했습니다.\n\n"
            f"{error}"
        )
        return

    atexit.register(server.server_close)

    server_thread = threading.Thread(
        target=server.serve_forever,
        name="DailyBoardHTTPServer",
        daemon=True,
    )
    server_thread.start()

    url = f"http://{HOST}:{port}/{HTML_FILE}"

    is_autostart = "--autostart" in sys.argv
    browser_delay = 5 if is_autostart else 0

    browser_thread = threading.Thread(
        target=open_browser,
        args=(url, browser_delay),
        name="DailyBoardBrowserLauncher",
        daemon=True,
    )
    browser_thread.start()

    try:
        while server_thread.is_alive():
            if SERVER_STATE.should_stop():
                break
            time.sleep(1)

    except KeyboardInterrupt:
        pass

    finally:
        server.shutdown()
        server.server_close()

        if server_thread.is_alive():
            server_thread.join(timeout=3)


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        show_error(
            "Daily Board 실행 중 오류가 발생했습니다.\n\n"
            f"{type(error).__name__}: {error}"
        )
