from threading import Event, Thread


class StoppableThread(Thread):
    def __init__(self, func, interval):
        super(StoppableThread, self).__init__()
        self._func = func
        self._interval = interval
        self._stop_flag = Event()

    def run(self):
        while not self._stop_flag.is_set():
            self._func()
            self._stop_flag.wait(self._interval)

    def stop(self):
        self._stop_flag.set()


def set_interval(func, interval) -> StoppableThread:
    thread = StoppableThread(func, interval)
    thread.start()
    return thread
