import hashlib
import secrets
import threading
import time
from collections import defaultdict, deque

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()

# Verified against when the email is unknown, so response time doesn't reveal which accounts exist.
_DUMMY_HASH = _hasher.hash("moudir-dummy-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def new_token(prefix: str = "") -> str:
    return prefix + secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Tokens are high-entropy random strings, so a plain SHA-256 is enough to store them."""
    return hashlib.sha256(token.encode()).hexdigest()


class LoginRateLimiter:
    """Counts failed sign-ins per key in a sliding window.

    In-memory, so limits are per backend process; put a shared limiter (e.g. at the
    reverse proxy) in front when running several replicas.
    """

    def __init__(self):
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, window_seconds: float) -> deque[float]:
        entries = self._failures[key]
        cutoff = time.monotonic() - window_seconds
        while entries and entries[0] < cutoff:
            entries.popleft()
        return entries

    def is_blocked(self, key: str, max_failures: int, window_seconds: float) -> bool:
        with self._lock:
            return len(self._prune(key, window_seconds)) >= max_failures

    def record_failure(self, key: str) -> None:
        with self._lock:
            self._failures[key].append(time.monotonic())

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._failures.clear()
            else:
                self._failures.pop(key, None)


login_limiter = LoginRateLimiter()
