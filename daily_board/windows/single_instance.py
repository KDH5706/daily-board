import ctypes

from daily_board.constants import ERROR_ALREADY_EXISTS


class SingleInstance:
    """Windows Named Mutex를 사용해 중복 실행을 방지합니다."""

    def __init__(self, mutex_name: str):
        self.mutex_name = mutex_name
        self.handle = None

    def acquire(self) -> bool:
        kernel32 = ctypes.windll.kernel32
        self.handle = kernel32.CreateMutexW(None, False, self.mutex_name)
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
