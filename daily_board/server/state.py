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
        # self.close_requested_at = None
        self.has_received_heartbeat = False
        self.shutdown_requested = False
        self.lock = threading.Lock()

    def heartbeat(self) -> None:
        with self.lock:
            self.last_heartbeat = time.monotonic()
            self.has_received_heartbeat = True
            # self.close_requested_at = None

    # def request_close(self) -> None:
    #     with self.lock:
    #         self.close_requested_at = time.monotonic()

    def request_shutdown(self) -> None:
        with self.lock:
            self.shutdown_requested = True

    def should_shutdown(self) -> bool:
        with self.lock:
            return self.shutdown_requested

    def seconds_since_heartbeat(self) -> float:
        with self.lock:
            reference_time = (
                self.last_heartbeat
                if self.last_heartbeat is not None
                else self.started_at
            )

            return (
                time.monotonic()
                - reference_time
            )
        
    def heartbeat_timed_out(self, timeout_seconds: float) -> bool:
        with self.lock:
            if self.last_heartbeat is None:
                return (
                    time.monotonic() - self.started_at > timeout_seconds
                )
            return (
                time.monotonic() - self.last_heartbeat > timeout_seconds
            )

    # def should_stop(self) -> bool:
    #     with self.lock:
    #         now = time.monotonic()
    #         if not self.has_received_heartbeat:
    #             return now - self.started_at > STARTUP_GRACE_SECONDS
    #         if self.close_requested_at is not None:
    #             if now - self.close_requested_at > CLOSE_GRACE_SECONDS:
    #                 return True
    #         if self.last_heartbeat is not None:
    #             if now - self.last_heartbeat > HEARTBEAT_TIMEOUT_SECONDS:
    #                 return True
    #         return False
