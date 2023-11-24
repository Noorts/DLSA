from threading import Timer


def set_timeout(func, timeout) -> Timer:
    timer = Timer(timeout, func)
    timer.start()
    return timer
