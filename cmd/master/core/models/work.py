from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from .job import Sequence, SequenceId, TargetQueryCombination, Alignment

WorkerStatus = Literal["IDLE", "WORKING", "DEAD"]


class WorkerId(BaseModel):
    id: UUID


class WorkerResources(BaseModel):
    ram_mb: int
    # determined using benchmarking/cpu_cores, ...
    cpu_resources: int


class WorkPackage(BaseModel):
    # work package id
    id: UUID
    targets: dict[SequenceId, Sequence]
    queries: dict[SequenceId, Sequence]

    sequences: list[TargetQueryCombination]


class WorkStatus(BaseModel):
    # work package id
    id: UUID
    percentage_done: float


class WorkResult(BaseModel):
    work_id: UUID
    alignments: list[tuple[TargetQueryCombination, Alignment]]
