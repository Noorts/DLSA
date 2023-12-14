import logging
from typing import Literal

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

SchedulerType = Literal["primitive", "proportional", "time"]


class _Settings(BaseSettings):
    # Intervals for cleaning up the job queue and the workers
    work_package_cleaning_interval: int = 5
    worker_cleaning_interval: int = 5
    # The amount of seconds a worker can go dark before it is considered dead
    worker_timeout: int = 10

    # Scheduler settings
    scheduler_type: SchedulerType = "proportional"

    # For the time scheduler (how many seconds of work should be assigned to a worker)
    work_package_time_split_in_seconds: int = 60 * 3
    enable_job_deletion: bool = True


SETTINGS = _Settings()

logger.info(f"Settings: {SETTINGS.model_dump(mode='json')}")
