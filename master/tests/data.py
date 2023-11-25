from uuid import UUID

from master.api_models import JobRequest, WorkResult, Alignment, TargetQueryCombination, JobResultCombination

JOB_REQUEST = JobRequest(
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

JOB_RESULT_COMPLETE = WorkResult(
    alignments=[
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
    ]
)

JOB_RESULT_PART_1 = WorkResult(
    alignments=[
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
    ]
)

JOB_RESULT_PART_2 = WorkResult(
    alignments=[
        JobResultCombination(
            combination=TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
    ]
)
