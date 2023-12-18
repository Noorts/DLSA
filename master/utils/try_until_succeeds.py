import time
from typing import Callable, TypeVar, Any

T = TypeVar("T")


def try_until_succeeds(
    func: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    while True:
        # noinspection PyBroadException
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)
            # sleep for 5ms before retrying
            time.sleep(0.005)
