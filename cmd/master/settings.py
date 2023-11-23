from typing import Literal

from pydantic_settings import BaseSettings

SchedulerType = Literal["primitive"]


class _Settings(BaseSettings):
    scheduler_type: SchedulerType = "primitive"
    work_package_cleaning_interval: int = 5 * 1000
    worker_cleaning_interval: int = 5 * 1000
    worker_timout: int = 10 * 1000


SETTINGS = _Settings()
