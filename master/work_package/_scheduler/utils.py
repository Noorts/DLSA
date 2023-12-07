from master.api_models import Sequence


def estimate_work_in_seconds(target: Sequence, query: Sequence, cups: int) -> int:
    target_length = len(target)
    query_length = len(query)

    return target_length * query_length // cups
