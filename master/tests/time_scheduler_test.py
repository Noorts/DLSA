from uuid import UUID, uuid4

from master.api_models import JobRequest, TargetQueryCombination
from master.job_queue.queued_job import QueuedJob
from master.work_package._scheduler.time_work_scheduler import _calculate_score_of
from master.work_package._scheduler.utils import estimate_work_in_seconds

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
            # cost: 8
            TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
                query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            ),
            # cost: 7
            TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
                query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            ),
            # cost: 3
            TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
                query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            ),
        ],
    ),
    completed_sequences={},
    sequences_in_progress=[],
    id=uuid4(),
    match_score=1,
    mismatch_penalty=2,
    gap_penalty=3,
)


def test_scheduler():
    score, sequences = _calculate_score_of(
        job,
        10,
        10,
    )

    assert score == 10
    assert len(sequences) == 2
    cost = 0
    for sequence in sequences:
        target = job.request.sequences[sequence.target]
        query = job.request.sequences[sequence.query]
        cost += estimate_work_in_seconds(target, query, 10)

    assert cost == 10

    assert sequences == [
        TargetQueryCombination(
            target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
        ),
        TargetQueryCombination(
            target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
            query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"),
        ),
    ]
