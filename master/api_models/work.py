from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from .job import TargetQueryCombination, Alignment

WorkerStatus = Literal["IDLE", "WORKING", "DEAD"]


class WorkerId(BaseModel):
    id: UUID


class WorkerResources(BaseModel):
    ram_mb: int
    # determined using benchmarking/cpu_cores, ...
    cpu_resources: int
    # determined using benchmarking/gpu_cores, ...
    gpu_resources: int


class WorkPackage(BaseModel):
    # work package id
    id: UUID
    job_id: UUID
    sequences: list[TargetQueryCombination]


class WorkStatus(BaseModel):
    percentage_done: float


class WorkResult(BaseModel):
    work_id: UUID
    alignments: list[tuple[TargetQueryCombination, Alignment]]
