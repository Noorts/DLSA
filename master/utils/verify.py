from master.api_models import WorkResultCombination


def verify_result(package, result: WorkResultCombination):
    return verify_exists(
        total_sequence=package.sequences[result.combination.query],
        aligned_sequence=result.alignment.query_alignment,
        end_index=result.alignment.maxX
    ) and verify_exists(
        total_sequence=package.sequences[result.combination.target],
        aligned_sequence=result.alignment.target_alignment,
        end_index=result.alignment.maxY
    ) and verify_score(
        query_align=result.alignment.query_alignment,
        target_align=result.alignment.target_alignment,
        length=result.alignment.length,
        expected=result.alignment.score,
        match=package.match_score,
        mismatch=package.mismatch_penalty,
        gap=package.gap_penalty
    )


def verify_score(query_align: str, target_align: str, length: int, expected: int, match: int, mismatch: int, gap: int):
    if len(query_align) != len(target_align) or len(query_align) != length:
        return False
    score = 0
    for i in range(length):
        if query_align[i] == '-' or target_align[i] == '-':
            score -= gap
        elif query_align[i] == target_align[i]:
            score += match
        else:
            score -= mismatch
    return score == expected


def verify_exists(total_sequence, aligned_sequence, end_index):
    try:
        for i in range(len(aligned_sequence)):
            if aligned_sequence[-1 - i] == '-':
                continue
            if total_sequence[end_index] != aligned_sequence[-1 - i]:
                return False
            end_index -= 1
    except IndexError:
        return False
    return True
