def _missing(x) -> bool:
    return x is None or x != x


def trimmed_flags(scores: list[float | None]) -> tuple[list[bool], float | None]:
    """Flag the single lowest and single highest mark as struck; return the trimmed mean."""
    present = [i for i, s in enumerate(scores) if s is not None and s == s]
    flags = [False] * len(scores)
    if len(present) < 3:
        return flags, None
    lo = min(present, key=lambda i: (scores[i], i))
    hi = max((i for i in present if i != lo), key=lambda i: (scores[i], -i))
    # With ties the first max must differ from lo; otherwise pick the first max among the rest.
    flags[lo] = flags[hi] = True
    kept = [scores[i] for i in present if not flags[i]]
    return flags, sum(kept) / len(kept)


def rank_label(rank: int | None, size: int | None) -> str:
    """'rank / size' text; just the rank when the size is unknown, '' when the rank is."""
    if _missing(rank):
        return ""
    if _missing(size):
        return str(int(rank))
    return f"{int(rank)} / {int(size)}"
