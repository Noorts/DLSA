from .scheduler.work_scheduler import WorkScheduler
from ..api_models import WorkPackage
from ..utils.cleaner import Cleaner
from ..utils.singleton import Singleton
from ..worker.worker import Worker
from ..worker.worker_collector import WorkerCollector


class WorkCollector(Cleaner, Singleton):
    _CLEANING_INTERVAL = 5 * 1000

    def __init__(self):
        self._worker_collector = WorkerCollector()
        self._work_scheduler = WorkScheduler.create()
        self._work_packages: dict[Worker, WorkPackage] = {}
        super().__init__(interval=self._CLEANING_INTERVAL)

    def get_work(self, worker: Worker) -> WorkPackage | None:
        work = self._work_scheduler.schedule_work_for(worker)
        if not work:
            return None

        self._work_packages[worker] = work
        return work

    def execute_clean(self):
        for worker in self._work_packages.keys():
            if worker.status == "DEAD":
                # todo mark all work as failed where the worker is not alive anymore -> return it into the job_queue
                pass
