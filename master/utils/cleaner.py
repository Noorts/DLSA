import time
from abc import ABC, abstractmethod
from threading import Thread


class Cleaner(ABC):
    def __init__(self, interval: float):
        self._cleaning_thread = Thread(target=self._cleaning_loop, daemon=True)
        self._interval = interval
        self._cleaning_thread.start()

    def _cleaning_loop(self) -> None:
        while True:
            self.execute_clean()
            time.sleep(self._interval)

    @abstractmethod
    def execute_clean(self) -> None:
        """This method will be called every self._interval seconds"""