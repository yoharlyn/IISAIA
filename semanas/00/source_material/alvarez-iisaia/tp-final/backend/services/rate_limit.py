from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class LoginRateLimiter:
    max_failures: int = 5
    window_seconds: int = 900
    clock: Callable[[], float] = time.monotonic
    _attempts: dict[str, list[float]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def _recent(self, key: str, now: float) -> list[float]:
        return [stamp for stamp in self._attempts.get(key, []) if now - stamp < self.window_seconds]

    def retry_after(self, key: str) -> int:
        now = self.clock()
        with self._lock:
            recent = self._recent(key, now)
            self._attempts[key] = recent
            if len(recent) < self.max_failures:
                return 0
            return max(1, int(self.window_seconds - (now - recent[0])))

    def fail(self, key: str) -> None:
        now = self.clock()
        with self._lock:
            recent = self._recent(key, now)
            recent.append(now)
            self._attempts[key] = recent

    def success(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._attempts.clear()


login_rate_limiter = LoginRateLimiter()
