from abc import ABC, abstractmethod
from typing import Any

from ..work_collector import _WorkCollector
from ...models import WorkerIdType, WorkPackage
from ...worker.worker import Worker
from ...worker.worker_collector import WorkerCollector

JobQueue = Any


class WorkScheduler(ABC):
    def __init__(self, worker_collector: WorkerCollector, job_queue: JobQueue):
        self._worker_collector = worker_collector
        self._job_queue = job_queue

    @abstractmethod
    def schedule_work_for(self, worker: Worker) -> None | WorkPackage:
        pass
