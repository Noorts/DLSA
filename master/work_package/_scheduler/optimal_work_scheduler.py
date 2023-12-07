import logging
from uuid import uuid4

from master.worker.worker import Worker
from .scheduled_work_package import ScheduledWorkPackage, InternalWorkPackage
from .utils import get_best_match_for
from .work_scheduler import WorkPackageScheduler

logger = logging.getLogger(__name__)


class OptimalWorkScheduler(WorkPackageScheduler):
    def schedule_work_for(self, worker: Worker) -> None | ScheduledWorkPackage:
        unfinished_jobs = self._job_queue.jobs_with_unassigned_sequences()
        if not unfinished_jobs:
            return None

        matches = get_best_match_for(unfinished_jobs, worker.resources.benchmark_result, 3 * 60)

        scheduled_packages = []

        for job, queries in matches.items():
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
                match_score=job.request.match_score,
                mismatch_penalty=job.request.mismatch_penalty,
                gap_penalty=job.request.gap_penalty,
            )

            job.sequences_in_progress += package.queries
            scheduled_packages.append(
                ScheduledWorkPackage(
                    package=package,
                    worker=worker,
                )
            )
        # TODO in this case we would have to return a list of ScheduledWorkPackages
        return scheduled_packages
