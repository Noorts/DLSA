from uuid import uuid4

from master.api_models import Sequence, TargetQueryCombination
from master.job_queue.queued_job import QueuedJob
from master.utils.time import current_ms
from master.work_package._scheduler.scheduled_work_package import InternalWorkPackage, ScheduledWorkPackage
from master.worker.worker import Worker


def estimate_work_in_seconds(target: Sequence, query: Sequence, cups: int) -> float:
    target_length = len(target)
    query_length = len(query)

    return target_length * query_length / cups


def work_packages_from_queries(
    job: QueuedJob, queries: set[TargetQueryCombination], worker: Worker
) -> ScheduledWorkPackage | None:
    if not queries:
        return None

    total_cups = 0
    for comb in queries:
        total_cups += len(job.request.sequences[comb.query]) * len(job.request.sequences[comb.target])
    total_ms = total_cups / worker.resources.benchmark_result * 1000

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
        start_time=current_ms(),
        expected_ms=max(int(total_ms), 1)
    )
