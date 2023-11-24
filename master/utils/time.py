import time


def current_ms() -> int:
    return int(round(time.time() * 1000))


def current_sec() -> int:
    return int(round(time.time()))
