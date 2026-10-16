import time
from functools import wraps


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
