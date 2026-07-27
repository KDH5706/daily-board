import threading
import time

from daily_board.constants import (
    CLOSE_GRACE_SECONDS,
    HEARTBEAT_TIMEOUT_SECONDS,
    STARTUP_GRACE_SECONDS,
)


class ServerState:
    def __init__(self):
        self.started_at = time.monotonic()
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
