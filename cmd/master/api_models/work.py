from dataclasses import dataclass as py_dataclass
from typing import Literal
from uuid import UUID

from pydantic.dataclasses import dataclass

from .job import TargetQueryCombination, Alignment

WorkerStatus = Literal["IDLE", "WORKING", "DEAD"]


@dataclass
@py_dataclass
class WorkerId:
    id: UUID


@dataclass
@py_dataclass
class WorkerResources:
    ram_mb: int
    # determined using benchmarking/cpu_cores, ...
    cpu_resources: int


@dataclass
@py_dataclass
class WorkPackage:
    # work package id
    id: UUID
    job_id: UUID
    sequences: list[TargetQueryCombination]


@dataclass
@py_dataclass
class WorkStatus:
    percentage_done: float


@dataclass
@py_dataclass
class WorkResult:
    work_id: UUID
    alignments: list[tuple[TargetQueryCombination, Alignment]]
