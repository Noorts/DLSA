from typing import Literal

from pydantic_settings import BaseSettings

SchedulerType = Literal["primitive"]


class _Settings(BaseSettings):
    scheduler_type: SchedulerType = "primitive"
    work_package_cleaning_interval: int = 5
    worker_cleaning_interval: int = 5
    worker_timout: int = 10
    enable_job_deletion: bool = True


SETTINGS = _Settings()
