import time


def current_ms() -> int:
    return int(round(time.time() * 1000))
