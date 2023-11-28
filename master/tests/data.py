from uuid import UUID

from master.api_models import (
    JobRequest,
    WorkResult,
    Alignment,
    TargetQueryCombination,
    JobResultCombination,
    WorkResultCombination,
    JobResult,
)

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

WORK_RESULT_COMPLETE = WorkResult(
    alignments=[
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
    ]
)

WORK_RESULT_PART_1 = WorkResult(
    alignments=[
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
    ]
)

WORK_RESULT_PART_2 = WorkResult(
    alignments=[
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABCD", length=4, score=4),
        ),
    ]
)
WORK_RESULT_PART_2_DIFFERENT_ALIGNMENT = WorkResult(
    alignments=[
        WorkResultCombination(
            combination=TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            alignment=Alignment(alignment="ABC", length=3, score=3),
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

_tmp = JOB_RESULT_COMPLETE.model_dump(mode="json")
_tmp["alignments"][-1]["alignments"].append(
    WORK_RESULT_PART_2_DIFFERENT_ALIGNMENT.model_dump(mode="json")["alignments"][0]["alignment"]
)
JOB_RESULT_COMPLETE_WITH_DIFFERENT_ALIGNMENT = JobResult(**_tmp)
