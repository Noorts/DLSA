from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from settings import SETTINGS
from ...api_models import WorkPackage
from ...job_queue.job_queue import JobQueue
from ...worker.worker import Worker
from ...worker.worker_collector import WorkerCollector


@dataclass
class ScheduledWorkPackage:
    package: WorkPackage
    worker: Worker

    @property
    def percentage_done(self) -> float:
        # Get the length of the sequences that should be done in the work package
        sequence_length = len(self.package.sequences)
        completed_sequences = 0

        for sequence in self.package.sequences:
            if sequence in self.package.job.completed_sequences:
                completed_sequences += 1

        return completed_sequences / sequence_length


class WorkPackageScheduler(ABC):
    _created_scheduler: WorkPackageScheduler | None = None

    def __init__(self, worker_collector: WorkerCollector, job_queue: JobQueue):
        self._worker_collector = worker_collector
        self._job_queue = job_queue

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

    @abstractmethod
    def schedule_work_for(self, worker: Worker) -> None | ScheduledWorkPackage:
        """Schedules work for a worker if possible and return the work package"""

    # noinspection PyMethodMayBeStatic
    def abort_work_package(self, work_package: ScheduledWorkPackage) -> None:
        job = work_package.package.job

        for in_progress_sequence in job.sequences_in_progress:
            if in_progress_sequence in work_package.package.sequences:
                job.sequences_in_progress.remove(in_progress_sequence)
