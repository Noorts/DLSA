import time
from abc import ABC, abstractmethod
from threading import Thread


class Cleaner(ABC):
    def __init__(self, interval: int):
        self._cleaning_thread = Thread(target=self._cleaning_loop, daemon=True)
        self._interval = interval
        self._cleaning_thread.start()

    def _cleaning_loop(self):
        while True:
            self.execute_clean()
            time.sleep(self._interval)

    @abstractmethod
    def execute_clean(self):
        pass
