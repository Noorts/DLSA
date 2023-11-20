from typing import Dict

from .scheduler.work_scheduler import WorkScheduler
from ..models import WorkPackage
from ..utils.cleaner import Cleaner
from ..utils.singleton import Singleton
from ..worker.worker import Worker
from ..worker.worker_collector import WorkerCollector


class _WorkCollector(Cleaner, metaclass=Singleton):
    _CLEANING_INTERVAL = 5

    def __init__(self):
        self._worker_collector = WorkerCollector()
        # TODO fill job queue
        self._work_scheduler = WorkScheduler(self._worker_collector, None)
        self._work_packages: Dict[Worker, WorkPackage] = {}
        super().__init__(interval=self._CLEANING_INTERVAL)

    def get_work(self, worker: Worker) -> WorkPackage | None:
        work = self._work_scheduler.schedule_work_for(worker)
        if not work:
            return None

        self._work_packages[worker] = work

    def execute_clean(self):
        for worker in self._work_packages.keys():
            if worker.status == "DEAD":
                # todo mark all work as failed where the worker is not alive anymore
                pass
