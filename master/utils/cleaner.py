import logging
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
            try:
                self.execute_clean()
            except Exception as e:
                # Get the filename of the class that extends the cleaner class
                super_class_file_name = self.__class__.__module__.split(".")[-1]
                logger = logging.getLogger(super_class_file_name)
                logger.debug(f"Exception in cleaner thread: {e}")

            time.sleep(self._interval)

    @abstractmethod
    def execute_clean(self) -> None:
        """This method will be called every self._interval seconds"""
