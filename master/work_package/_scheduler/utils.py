from master.api_models import TargetQueryCombination
from master.job_queue.queued_job import QueuedJob


def estimate_work_in_seconds(query: TargetQueryCombination, queued_job: QueuedJob, performance: int) -> float:
    job_request = queued_job.request
    target_length = len(job_request.sequences[query.target])
    query_length = len(job_request.sequences[query.query])

    # TODO calculate the time needed to align the query to the target
    raise NotImplementedError()
    # noinspection PyUnreachableCode
    return 0


def _estimate_string_size(string: str) -> int:
    """
    Calculate the size of the string in MB
    """
    return len(string) * 2 // 1024 // 1024


def get_penalty_of_combination(query: TargetQueryCombination, queued_job: QueuedJob) -> float:
    """
    Calculate the penalty (network overhead) of the given combination
    """
    query_size = _estimate_string_size(queued_job.request.sequences[query.query])
    target_size = _estimate_string_size(queued_job.request.sequences[query.target])
    # TODO calculate the penalty of the given combination
    raise NotImplementedError()
    # noinspection PyUnreachableCode
    return 0


WorkForWorker = dict[QueuedJob, list[TargetQueryCombination]]


def get_best_match_for(unfinished_jobs: list[QueuedJob], performance: int, seconds_of_work: int) -> WorkForWorker:
    """
    We try to do the following things:
    1. Create a package of Queries that is as close as possible to the seconds_of_work
    2. Minimize the number of query strings that have to be sent to the worker.
     By utilizing a sequence twice in WorkForWorker, we can reduce the network overhead, thereby reducing the penalty
    :param unfinished_jobs: All jobs that have unfinished sequences
    :param performance: The performance of the worker
    :param seconds_of_work: The amount of seconds the worker should work
    :return: A dictionary with the job as key and the queries as value
    """
    pass
