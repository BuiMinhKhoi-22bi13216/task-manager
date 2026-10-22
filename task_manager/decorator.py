import time
from functools import wraps
from .notifier import Notifier


def log_execution_time(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        start = time.perf_counter()

        result = func(*args, **kwargs)

        end = time.perf_counter()

        print(
            f"{func.__name__} executed in "
            f"{end - start:.6f} seconds"
        )

        return result

    return wrapper


class NotifierDecorator(Notifier):
    """Wrap any Notifier without changing its original implementation."""

    def __init__(self, wrapped: Notifier):
        self._wrapped = wrapped

    def send(self, message: str) -> None:
        self._wrapped.send(message)


class PrefixNotifier(NotifierDecorator):
    def __init__(self, wrapped: Notifier, prefix: str):
        super().__init__(wrapped)
        self._prefix = prefix

    def send(self, message: str) -> None:
        self._wrapped.send(f"{self._prefix}{message}")
