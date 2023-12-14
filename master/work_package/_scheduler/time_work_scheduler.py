import logging
import random

from master.worker.worker import Worker
from .scheduled_work_package import ScheduledWorkPackage
from .utils import estimate_work_in_seconds, work_packages_from_queries
from .work_scheduler import WorkPackageScheduler
from ...api_models import TargetQueryCombination
from ...job_queue.queued_job import QueuedJob
from ...settings import SETTINGS

logger = logging.getLogger(__name__)

WorkForWorker = tuple[QueuedJob, list[TargetQueryCombination]]


class TimeWorkScheduler(WorkPackageScheduler):
    def schedule_work_for(self, worker: Worker) -> None | ScheduledWorkPackage:
        unfinished_jobs = self._job_queue.jobs_with_unassigned_sequences()
        if not unfinished_jobs:
            return None

        # Get the first unfinished job
        job = unfinished_jobs.pop(0)

        queries = _get_n_seconds_of_work(job, SETTINGS.work_package_time_split_in_seconds, worker)
        return work_packages_from_queries(job, queries, worker)


def _get_n_seconds_of_work(
    job: QueuedJob,
    seconds: int,
    worker: Worker,
) -> list[TargetQueryCombination]:
    unfinished_queries = job.missing_sequences()
    # Shuffle the unfinished queries to get a more even distribution
    random.shuffle(unfinished_queries)

    total_time = 0
    queries: list[TargetQueryCombination] = []

    for query in unfinished_queries:
        query_time = estimate_work_in_seconds(
            target=job.request.sequences[query.target],
            query=job.request.sequences[query.query],
            cups=worker.resources.benchmark_result,
        )

        if total_time + query_time > seconds:
            continue

        total_time += query_time
        queries.append(query)

        # If we are in 10% of the time limit, we can stop
        if total_time > seconds * 0.9:
            break

    return queries
