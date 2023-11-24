from uuid import UUID

from master.api_models import JobRequest, WorkResult, Alignment

JOB_REQUEST = JobRequest(
    queries={
        UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("4e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
    },
    targets={
        UUID("5e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("6e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("7e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("8e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("9e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
    },
    sequences=[
        (UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
        (UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
        (UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
    ],
)


JOB_RESULT_COMPLETE = WorkResult(
    alignments=[
        (
            (UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
            Alignment(alignment="ABCD", length=4, score=4),
        ),
        (
            (UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
            Alignment(alignment="ABCD", length=4, score=4),
        ),
        (
            (UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
            Alignment(alignment="ABCD", length=4, score=4),
        ),
    ]
)

JOB_RESULT_PART_1 = WorkResult(
    alignments=[
        (
            (UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
            Alignment(alignment="ABCD", length=4, score=4),
        ),
        (
            (UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
            Alignment(alignment="ABCD", length=4, score=4),
        ),
    ]
)

JOB_RESULT_PART_2 = WorkResult(
    alignments=[
        (
            (UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
            Alignment(alignment="ABCD", length=4, score=4),
        ),
    ]
)
