import logging
import math
from uuid import uuid4

from master.worker.worker import Worker
from .scheduled_work_package import ScheduledWorkPackage, InternalWorkPackage
from .utils import work_packages_from_queries
from .work_scheduler import WorkPackageScheduler
from ...api_models import TargetQueryCombination
from ...job_queue.queued_job import QueuedJob

logger = logging.getLogger(__name__)


class ProportionalWorkScheduler(WorkPackageScheduler):
    MIN_SEQUENCES_PER_WORKER = 20

    def schedule_work_for(self, worker: Worker) -> None | ScheduledWorkPackage:
        unfinished_jobs = self._job_queue.jobs_with_unassigned_sequences()
        if not unfinished_jobs:
            return None

        # Get the first unfinished job
        job = unfinished_jobs.pop(0)
        queries = _get_proportional_work_packages(job, worker, self._worker_collector.idle_workers())

        return work_packages_from_queries(job, queries, worker)


def _get_proportional_work_packages(
    job: QueuedJob, worker: Worker, idle_workers: list[Worker]
) -> list[TargetQueryCombination]:
    # Get all missing sequences for the job
    queries = job.missing_sequences()
    if len(queries) == 0:
        logger.error(f"Job {job.id} has no sequences to schedule")
        return []

    # Get all workers that are currently NOT working on a job (this includes the worker requesting work)
    total_processing_power = sum([worker.resources.benchmark_result for worker in idle_workers])

    # Calculate the processing power of the current worker compared to all other workers
    worker_processing_power = worker.resources.benchmark_result
    # Just in case something went wrong and the worker itself is not in the list of available workers
    # (should not happen), but better safe than sorry
    proportional_processing_power = worker_processing_power / max(total_processing_power, worker_processing_power)

    # Calculate the number of queries that should be assigned to the current worker
    # (at least one query should be assigned)
    amount_of_sequences = math.ceil(proportional_processing_power * len(queries))
    amount_of_sequences = max(amount_of_sequences, ProportionalWorkScheduler.MIN_SEQUENCES_PER_WORKER)
    amount_of_sequences = min(amount_of_sequences, len(queries))

    # Assign the queries to the current worker
    return queries[:amount_of_sequences]
