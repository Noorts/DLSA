from typing import Literal
from uuid import UUID

from pydantic import BaseModel

Sequence = str
SequenceId = UUID
JobState = Literal["IN_QUEUE", "IN_PROGRESS", "DONE"]
TargetQueryCombination = tuple[SequenceId, SequenceId]


class JobRequest(BaseModel):
    targets: dict[SequenceId, Sequence]
    queries: dict[SequenceId, Sequence]

    sequences: list[TargetQueryCombination]


class JobId(BaseModel):
    id: UUID


class JobStatus(BaseModel):
    id: UUID
    state: JobState
    # the progress as percentage [0-1]
    progress: float


class Alignment(BaseModel):
    # ABDAABDABDAC
    alignment: str
    length: int
    score: int


# the result returned to the client, ordered by length
class JobResult(BaseModel):
    alignments: list[Alignment]
