from typing import Literal, Annotated
from uuid import UUID

from pydantic import Field
from pydantic.dataclasses import dataclass
from dataclasses import dataclass as py_dataclass

Sequence = str
SequenceId = UUID
JobState = Literal["IN_QUEUE", "IN_PROGRESS", "DONE"]
TargetQueryCombination = tuple[SequenceId, SequenceId]


@dataclass
@py_dataclass
class JobRequest:
    targets: dict[SequenceId, Sequence]
    queries: dict[SequenceId, Sequence]

    sequences: list[TargetQueryCombination]


@dataclass
@py_dataclass
class JobId:
    id: UUID


@dataclass
@py_dataclass
class JobStatus:
    id: UUID
    state: JobState
    # the progress as percentage [0-1]
    progress: Annotated[float, Field(strict=True, gt=0, lt=1)]


@dataclass
@py_dataclass
class Alignment:
    # ABDAABDABDAC
    alignment: str
    length: int
    score: int


# the result returned to the client, ordered by length
@dataclass
@py_dataclass
class JobResult:
    alignments: list[Alignment]
