from uuid import uuid4

from master.worker.worker import Worker
from .scheduled_work_package import ScheduledWorkPackage, InternalWorkPackage
from .work_scheduler import WorkPackageScheduler


class PrimitiveWorkPackageScheduler(WorkPackageScheduler):
    def schedule_work_for(self, worker: Worker) -> None | ScheduledWorkPackage:
        unfinished_jobs = self._job_queue.jobs_with_unassigned_sequences()
        if not unfinished_jobs:
            return None
        job = unfinished_jobs.pop(0)
        queries = job.missing_sequences()
        package = InternalWorkPackage(
            id=uuid4(),
            job=job,
            queries=queries,
            sequences={
                # Query
                **{sequence.query: job.request.sequences[sequence.query] for sequence in queries},
                # Target
                **{sequence.target: job.request.sequences[sequence.target] for sequence in queries},
            },
        )

        job.sequences_in_progress += package.queries

        return ScheduledWorkPackage(
            package=package,
            worker=worker,
        )
