from typing import Literal

from pydantic_settings import BaseSettings

SchedulerType = Literal["primitive", "proportional", "time"]


class _Settings(BaseSettings):
    scheduler_type: SchedulerType = "primitive"
    work_package_cleaning_interval: int = 5
    worker_cleaning_interval: int = 5
    worker_timout: int = 10
    work_package_time_split_in_seconds: int = 60 * 3
    enable_job_deletion: bool = True


SETTINGS = _Settings()
