import logging
import sys
from uuid import uuid4

from master.worker.worker import Worker
from .scheduled_work_package import ScheduledWorkPackage, InternalWorkPackage
from .utils import estimate_work_in_seconds
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

        job, queries = get_best_match_for(
            unfinished_jobs, worker.resources.benchmark_result, SETTINGS.work_package_time_split_in_seconds
        )

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
        return ScheduledWorkPackage(
            package=package,
            worker=worker,
        )


def _calculate_score_of(
    unfinished_job: QueuedJob, performance: int, seconds_of_work: int
) -> tuple[int, list[TargetQueryCombination]]:
    query_time_lookup: dict[TargetQueryCombination, int] = {}
    missing = unfinished_job.missing_sequences()

    for query in missing:
        query_time_lookup[query] = estimate_work_in_seconds(
            unfinished_job.request.sequences[query.target],
            unfinished_job.request.sequences[query.query],
            performance,
        )

    # Dynamic programming approach
    dp = [sys.maxsize] * (seconds_of_work + 1)
    dp[0] = 0
    selected_queries: list[TargetQueryCombination | None] = [None] * (seconds_of_work + 1)

    for query, time in query_time_lookup.items():
        for i in range(seconds_of_work - time, -1, -1):
            if dp[i] != sys.maxsize and dp[i] + time < dp[i + time]:
                dp[i + time] = dp[i] + time
                selected_queries[i + time] = query

    # Reconstruct the selected queries
    result: list[TargetQueryCombination] = []
    remaining_time = seconds_of_work
    while remaining_time > 0 and selected_queries[remaining_time] is not None:
        result.append(selected_queries[remaining_time])
        remaining_time -= query_time_lookup[selected_queries[remaining_time]]

    # If the result is empty, return the query target combination with the lowest work in seconds
    if not result:
        sequence = min(query_time_lookup, key=lambda k: query_time_lookup[k])
        time = query_time_lookup[sequence]
        return time, [sequence]

    return dp[seconds_of_work], result


def get_best_match_for(unfinished_jobs: list[QueuedJob], performance: int, seconds_of_work: int) -> WorkForWorker:
    """
    We try to do the following thing: Create a package of Queries that is as close as possible to the seconds_of_work
    :param unfinished_jobs: All jobs that have unfinished sequences
    :param performance: The performance of the worker
    :param seconds_of_work: The amount of seconds the worker should work
    :return: A dictionary with the job as a key and the queries as value
    """

    best_solution = None
    best_score = sys.maxsize

    for job in unfinished_jobs:
        score, sequences = _calculate_score_of(job, performance, seconds_of_work)
        if score < best_score:
            best_solution = job, sequences
            best_score = score

    return best_solution
