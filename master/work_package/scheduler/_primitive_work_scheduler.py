from uuid import uuid4

from master.worker.worker import Worker
from .scheduled_work_package import ScheduledWorkPackage, InternalWorkPackage
from .work_scheduler import WorkPackageScheduler


class PrimitiveWorkPackageScheduler(WorkPackageScheduler):
    def schedule_work_for(self, worker: Worker) -> None | ScheduledWorkPackage:
        unfinished_job = self._job_queue.unfinished_jobs()
        if not unfinished_job:
            return None
        job = unfinished_job.pop(0)
        package = InternalWorkPackage(
            id=uuid4(),
            job=job,
            sequences=job.missing_sequences(),
        )

        job.sequences_in_progress += package.sequences

        return ScheduledWorkPackage(
            package=package,
            worker=worker,
        )
