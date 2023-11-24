from typing import Literal, Annotated
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field

Sequence = str
SequenceId = UUID
JobState = Literal["IN_QUEUE", "IN_PROGRESS", "DONE"]
TargetQueryCombination = tuple[SequenceId, SequenceId]


class JobRequest(BaseModel):
    sequences: dict[SequenceId, Sequence]
    queries: list[TargetQueryCombination]


class JobId(BaseModel):
    id: UUID


class JobStatus(BaseModel):
    state: JobState
    # the progress as percentage [0-1]
    progress: Annotated[float, Field(strict=True, ge=0, le=1)]


class Alignment(BaseModel):
    # ABDAABDABDAC
    alignment: str
    length: int
    score: int


# the result returned to the client, ordered by length
class JobResult(BaseModel):
    alignments: list[tuple[TargetQueryCombination, Alignment]]
