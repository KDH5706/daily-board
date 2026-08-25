import threading
import time


class ServerState:
    def __init__(self):
        self.started_at = time.monotonic()
        self.last_heartbeat = None
        self.shutdown_requested = False
        self.lock = threading.Lock()

    def heartbeat(self) -> None:
        with self.lock:
            self.last_heartbeat = time.monotonic()

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

            return (time.monotonic() - reference_time)