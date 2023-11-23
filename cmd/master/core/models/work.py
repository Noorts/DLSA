from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from .job import Sequence, SequenceId, TargetQueryCombination, Alignment

WorkerStatus = Literal["IDLE", "WORKING", "DEAD"]

WorkerIdType = UUID
WorkPackageIdType = UUID


class WorkerId(BaseModel):
    id: WorkerIdType


class WorkerResources(BaseModel):
    ram_mb: int
    # determined using benchmarking/cpu_cores, ...
    cpu_resources: int


class WorkPackage(BaseModel):
    # work package id
    id: WorkPackageIdType
    targets: dict[SequenceId, Sequence]
    queries: dict[SequenceId, Sequence]

    sequences: list[TargetQueryCombination]


class WorkStatus(BaseModel):
    # work package id
    id: str
    percentage_done: float


class WorkResult(BaseModel):
    work_id: str
    alignments: list[tuple[TargetQueryCombination, Alignment]]
