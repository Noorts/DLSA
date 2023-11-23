from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal
from ...models import WorkPackage, WorkPackageIdType
from ...queue.job_queue import JobQueue
from ...worker.worker import Worker
from ...worker.worker_collector import WorkerCollector

SchedulerType = Literal["primitive"]


@dataclass
class WorkPackageStatus:
    percentage_done: float


@dataclass
class ScheduledWorkPackage:
    package: WorkPackage
    worker: Worker
    status: WorkPackageStatus


class WorkScheduler(ABC):
    _created_scheduler: WorkScheduler | None = None
    _created_scheduler_type: SchedulerType | None = None

    def __init__(self, worker_collector: WorkerCollector, job_queue: JobQueue):
        self._packages_in_process: dict[WorkPackageIdType, ScheduledWorkPackage] = {}
        self._worker_collector = worker_collector
        self._job_queue = job_queue

    @abstractmethod
    def schedule_work_for(self, worker: Worker) -> None | WorkPackage:
        """Schedules work for a worker if possible and return the work package"""

    @abstractmethod
    def abort_work_package(self, work_package: WorkPackageIdType):
        """Aborts a work package"""

    @staticmethod
    def create(scheduler_type: SchedulerType = "primitive") -> WorkScheduler:
        from ._primitive_work_scheduler import PrimitiveWorkScheduler

        worker_collector = WorkerCollector()
        job_queue = JobQueue()

        # Return the already created scheduler if it exists
        if WorkScheduler._created_scheduler:
            if WorkScheduler._created_scheduler_type != scheduler_type:
                raise RuntimeError("Cannot create multiple different work schedulers")
            return WorkScheduler._created_scheduler

        scheduler: WorkScheduler
        if scheduler_type == "primitive":
            WorkScheduler._created_scheduler = PrimitiveWorkScheduler(worker_collector, job_queue)
        else:
            raise NotImplementedError()

        return WorkScheduler._created_scheduler
