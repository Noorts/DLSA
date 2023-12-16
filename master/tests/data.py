from uuid import UUID

from master.api_models import (
    JobRequest,
    WorkResult,
    Alignment,
    WorkAlignment,
    TargetQueryCombination,
    JobResultCombination,
    WorkResultCombination,
    JobResult,
)

JOB_REQUEST = JobRequest(
    match_score=1,
    mismatch_penalty=-1,
    gap_penalty=-1,
    sequences={
        UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("4e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("5e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("6e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("7e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("8e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("9e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
    },
    queries=[
        TargetQueryCombination(
            target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
        ),
        TargetQueryCombination(
            target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
        ),
        TargetQueryCombination(
            target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
        ),
    ],
)

WORK_RESULT_COMPLETE = WorkResult(
    alignments=[
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=WorkAlignment(query_alignment="ABCD", target_alignment="ABCD", length=4, score=4, maxX=3, maxY=3),
        ),
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=WorkAlignment(query_alignment="ABCD", target_alignment="ABCD", length=4, score=4, maxX=3, maxY=3),
        ),
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=WorkAlignment(query_alignment="ABCD", target_alignment="ABCD", length=4, score=4, maxX=3, maxY=3),
        ),
    ]
)

WORK_RESULT_PART_1 = WorkResult(
    alignments=[
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=WorkAlignment(query_alignment="ABCD", target_alignment="ABCD", length=4, score=4, maxX=3, maxY=3),
        ),
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=WorkAlignment(query_alignment="ABCD", target_alignment="ABCD", length=4, score=4, maxX=3, maxY=3),
        ),
    ]
)

WORK_RESULT_PART_2 = WorkResult(
    alignments=[
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=WorkAlignment(query_alignment="ABCD", target_alignment="ABCD", length=4, score=4, maxX=3, maxY=3),
        ),
    ]
)
WORK_RESULT_PART_2_DIFFERENT_ALIGNMENT = WorkResult(
    alignments=[
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=WorkAlignment(query_alignment="ABC", target_alignment="ABC", length=3, score=3, maxX=2, maxY=2),
        ),
    ]
)

JOB_RESULT_COMPLETE = JobResult(
    alignments=[
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignments=[Alignment(alignment="ABCD", length=4, score=4)],
        ),
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignments=[Alignment(alignment="ABCD", length=4, score=4)],
        ),
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignments=[Alignment(alignment="ABCD", length=4, score=4)],
        ),
    ]
)

JOB_RESULT_COMPLETE_WITH_DIFFERENT_ALIGNMENT = JobResult(
    alignments=[
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignments=[Alignment(alignment="ABCD", length=4, score=4)],
        ),
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignments=[Alignment(alignment="ABCD", length=4, score=4)],
        ),
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignments=[
                Alignment(alignment="ABCD", length=4, score=4),
                Alignment(alignment="ABC", length=3, score=3)
            ],
        ),
    ]
)
