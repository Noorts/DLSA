from uuid import uuid4, UUID

from .scheduled_work_package import ScheduledWorkPackage, InternalWorkPackage
from .work_scheduler import WorkPackageScheduler


class PrimitiveWorkPackageScheduler(WorkPackageScheduler):
    def schedule_work_for(self, worker_id: UUID) -> None | ScheduledWorkPackage:
        job = self._job_queue.unfinished_jobs().pop()
        if not job:
            return None

        package = InternalWorkPackage(
            id=uuid4(),
            job=job,
            sequences=job.missing_sequences(),
        )

        job.sequences_in_progress += package.sequences
        worker = self._worker_collector.get_worker_by_id(worker_id)

        return ScheduledWorkPackage(
            package=package,
            worker=worker,
        )
