from __future__ import annotations

from abc import ABC, abstractmethod

from master.job_queue.job_queue import JobQueue
from master.settings import SETTINGS
from master.worker.worker import Worker
from master.worker.worker_collector import WorkerCollector
from .scheduled_work_package import ScheduledWorkPackage


class WorkPackageScheduler(ABC):
    _created_scheduler: WorkPackageScheduler | None = None

    def __init__(self, worker_collector: WorkerCollector, job_queue: JobQueue):
        self._worker_collector = worker_collector
        self._job_queue = job_queue

    @staticmethod
    def create() -> WorkPackageScheduler:
        from ._primitive_work_scheduler import PrimitiveWorkPackageScheduler

        # Return the already created _scheduler if it exists
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

    @abstractmethod
    def schedule_work_for(self, worker: Worker) -> None | ScheduledWorkPackage:
        """Schedules work for a worker if possible and return the work package"""

    # noinspection PyMethodMayBeStatic
    def abort_work_package(self, work_package: ScheduledWorkPackage) -> None:
        job = work_package.package.job

        for in_progress_sequence in job.sequences_in_progress:
            if in_progress_sequence in work_package.package.queries:
                job.sequences_in_progress.remove(in_progress_sequence)
