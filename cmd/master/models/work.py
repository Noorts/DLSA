from typing import Literal, List, Tuple, Dict

from pydantic import BaseModel

from .job import Sequence, SequenceId, TargetQueryCombination, Alignment

WorkerStatus = Literal["READY", "WORKING", "GONE"]


class WorkerId(BaseModel):
    id: str


class WorkerResources(BaseModel):
    ram_mb: int
    # determined using benchmarking/cpu_cores, ...
    cpu_resources: int


class WorkPackage(BaseModel):
    # work package id
    id: str
    targets: Dict[SequenceId, Sequence]
    queries: Dict[SequenceId, Sequence]

    sequences: List[TargetQueryCombination]


class WorkStatus(BaseModel):
    # work package id
    id: str
    percentage_done: float


class WorkResult(BaseModel):
    work_id: str
    alignments: List[Tuple[TargetQueryCombination, Alignment]]
