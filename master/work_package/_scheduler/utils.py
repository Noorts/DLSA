from master.api_models import Sequence


def estimate_work_in_seconds(target: Sequence, query: Sequence, performance: int) -> int:
    target_length = len(target)
    query_length = len(query)

    # TODO calculate the time needed to align the query to the target
    return target_length + query_length
