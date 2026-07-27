import contextlib
import socket
from http.server import ThreadingHTTPServer

from daily_board.constants import HOST, PORT_SEARCH_COUNT
from daily_board.server.state import ServerState


class DailyBoardHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.state = ServerState()


def find_available_port(start_port: int, attempts: int = PORT_SEARCH_COUNT) -> int:
    for port in range(start_port, start_port + attempts):
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.bind((HOST, port))
                return port
            except OSError:
                continue
    raise RuntimeError("사용 가능한 localhost 포트를 찾지 못했습니다.")
