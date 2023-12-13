import logging
from typing import Literal

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

SchedulerType = Literal["primitive", "proportional", "time"]


class _Settings(BaseSettings):
    scheduler_type: SchedulerType = "proportional"
    work_package_cleaning_interval: int = 5
    worker_cleaning_interval: int = 5
    worker_timeout: int = 10
    work_package_time_split_in_seconds: int = 60 * 3
    enable_job_deletion: bool = True


SETTINGS = _Settings()

logger.info(f"Settings: {SETTINGS.model_dump(mode='json')}")
