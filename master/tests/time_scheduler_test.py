from uuid import UUID, uuid4

from master.api_models import JobRequest, TargetQueryCombination, WorkerResources
from master.job_queue.queued_job import QueuedJob
from master.work_package._scheduler.time_work_scheduler import _get_n_seconds_of_work
from master.worker.worker import Worker

job = QueuedJob(
    request=JobRequest(
        match_score=1,
        mismatch_penalty=-1,
        gap_penalty=-1,
        sequences={
            UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "00000",
            UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "000",
            UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "00",
            UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "0",
            UUID("4e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "00000000",
            UUID("5e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "00000000",
            UUID("6e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "00000000",
            UUID("7e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "00000000",
            UUID("8e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "00000000",
            UUID("9e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "00000000",
        },
        queries=[
            # cost: 15
            TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
                query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            ),
            # cost: 10
            TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
                query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            ),
            # cost: 2
            TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
                query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            ),
        ],
    ),
    completed_sequences={},
    sequences_in_progress=set(),
    id=uuid4(),
    match_score=1,
    mismatch_penalty=2,
    gap_penalty=3,
)

dummy_worker = Worker(
    worker_id=uuid4(), resources=WorkerResources(benchmark_result=1), last_seen_alive=0, status="IDLE"
)


def test_scheduler():
    assert len(job.missing_sequences()) == 3
    assert len(job.completed_sequences) == 0
    assert len(job.sequences_in_progress) == 0

    work = _get_n_seconds_of_work(job, 3, dummy_worker)
    assert work == [
        TargetQueryCombination(
            target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
        ),
    ]

    work = _get_n_seconds_of_work(job, 5, dummy_worker)
    assert work == [
        TargetQueryCombination(
            target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
        ),
    ]

    work = _get_n_seconds_of_work(job, 13, dummy_worker)
    assert set(work) == {
        TargetQueryCombination(
            target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
        ),
        TargetQueryCombination(
            target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
        ),
    }

    work = _get_n_seconds_of_work(job, 27, dummy_worker)
    assert set(work) == {
        TargetQueryCombination(
            target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
        ),
        TargetQueryCombination(
            target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
        ),
        TargetQueryCombination(
            target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
        ),
    }
