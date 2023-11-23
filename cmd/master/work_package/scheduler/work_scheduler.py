from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from settings import SETTINGS
from ...api_models import WorkPackage
from ...job_queue.job_queue import JobQueue
from ...worker.worker import Worker
from ...worker.worker_collector import WorkerCollector


@dataclass
class WorkPackageStatus:
    percentage_done: float


@dataclass
class ScheduledWorkPackage:
    package: WorkPackage
    worker: Worker
    status: WorkPackageStatus


class WorkPackageScheduler(ABC):
    _created_scheduler: WorkPackageScheduler | None = None

    def __init__(self, worker_collector: WorkerCollector, job_queue: JobQueue):
        self._packages_in_process: dict[UUID, ScheduledWorkPackage] = {}
        self._worker_collector = worker_collector
        self._job_queue = job_queue

    @abstractmethod
    def schedule_work_for(self, worker: Worker) -> None | WorkPackage:
        """Schedules work for a worker if possible and return the work package"""

    @abstractmethod
    def abort_work_package(self, work_package: UUID):
        """Aborts a work package"""

    @staticmethod
    def create() -> WorkPackageScheduler:
        from ._primitive_work_scheduler import PrimitiveWorkPackageScheduler

        # Return the already created scheduler if it exists
        if WorkPackageScheduler._created_scheduler:
            return WorkPackageScheduler._created_scheduler

        worker_collector = WorkerCollector()
        job_queue = JobQueue()

        match SETTINGS.scheduler_type:
            case "primitive":
                WorkPackageScheduler._created_scheduler = PrimitiveWorkPackageScheduler(worker_collector, job_queue)
            case _:
                raise NotImplementedError()

        return WorkPackageScheduler._created_scheduler
