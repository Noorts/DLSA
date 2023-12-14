import itertools
import logging
import math
from uuid import uuid4

from master.worker.worker import Worker
from .scheduled_work_package import ScheduledWorkPackage, InternalWorkPackage
from .work_scheduler import WorkPackageScheduler

logger = logging.getLogger(__name__)


class ProportionalWorkScheduler(WorkPackageScheduler):
    MIN_SEQUENCES_PER_WORKER = 20

    def schedule_work_for(self, worker: Worker) -> None | ScheduledWorkPackage:
        unfinished_jobs = self._job_queue.jobs_with_unassigned_sequences()
        if not unfinished_jobs:
            return None

        # Get the first unfinished job
        job = unfinished_jobs.pop(0)

        # Get all missing sequences for the job
        queries = job.missing_sequences()
        if len(queries) == 0:
            logger.error(f"Job {job.id} has no sequences to schedule")
            return None

        # Get all workers that are currently NOT working on a job (this includes the worker requesting work)
        available_workers = self._worker_collector.idle_workers()
        total_processing_power = sum([worker.resources.benchmark_result for worker in available_workers])

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
        queries = set(itertools.islice(queries, amount_of_sequences))

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

        job.sequences_in_progress.update(package.queries)

        return ScheduledWorkPackage(
            package=package,
            worker=worker,
        )
