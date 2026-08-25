import json
from http.server import SimpleHTTPRequestHandler
from urllib.parse import unquote, urlparse

from daily_board.constants import HTML_FILE
from daily_board.opinet.errors import OpinetError
from daily_board.opinet.service import build_opinet_response
from daily_board.paths import opinet_config_path
from daily_board.windows.autostart import (
    is_windows_autostart_enabled,
    register_windows_autostart,
    unregister_windows_autostart,
)


class QuietRequestHandler(SimpleHTTPRequestHandler):
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

    @property
    def app_state(self):
        return self.server.state

    def log_message(self, format_string, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def send_empty_response(self, status_code: int = 204):
        self.send_response(status_code)
        self.end_headers()

    def send_json(self, data: object, status_code: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path = unquote(urlparse(self.path).path)
        if path == "/__heartbeat__":
            self.app_state.heartbeat()
            self.send_empty_response(204)
            return
        if path == "/__shutdown__":
            self.send_json(
                {
                    "success": True,
                    "message": "Server shutdown requested"
                }, 
                200,
            )
            self.app_state.request_shutdown()
            return
        
        if path == "/__autostart__":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(content_length).decode("utf-8"))
                enabled = bool(data.get("enabled"))
                success = register_windows_autostart() if enabled else unregister_windows_autostart()
                self.send_json(
                    {"success": success, "enabled": is_windows_autostart_enabled()},
                    200 if success else 500,
                )
            except Exception as error:
                self.send_json({"success": False, "error": str(error)}, 400)
            return
        self.send_error(404, "Not Found")

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == "/__heartbeat__":
            self.app_state.heartbeat()
            self.send_empty_response(204)
            return
        if path == "/__status__":
            self.send_json({"status": "running", "configPath": str(opinet_config_path())})
            return
        if path == "/__autostart__":
            self.send_json({"enabled": is_windows_autostart_enabled()})
            return
        if path == "/__opinet__":
            try:
                self.send_json(build_opinet_response(), 200)
            except FileNotFoundError as error:
                self.send_json(
                    {"success": False, "error": str(error), "configPath": str(opinet_config_path())},
                    404,
                )
            except (ValueError, OpinetError) as error:
                self.send_json({"success": False, "error": str(error)}, 400)
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
