"""Scheduling model with externally agreed prefixes, not a consensus engine.

Block references are (producer, height). Unique authenticated producer chains,
DA eligibility, full BFT decisions and a fixed execution context are assumptions.
CounterExecution is only a deterministic one-increment-per-block application.
"""


def extend_round_robin(prefix, tips, priority):
    prefix, priority = tuple(prefix), tuple(priority)
    boundaries = _boundaries(prefix, priority)
    if set(tips) != set(priority) or any(
            type(tips[p]) is not int or tips[p] < boundaries[p] for p in priority):
        raise ValueError("tips must cover every producer and extend its agreed boundary")
    width = max((tips[p] - boundaries[p] for p in priority), default=0)
    suffix = tuple((p, boundaries[p] + offset)
                   for offset in range(1, width + 1) for p in priority
                   if boundaries[p] + offset <= tips[p])
    return prefix + suffix


def speculate(prefix, received, priority):
    prefix, priority = tuple(prefix), tuple(priority)
    tips = _boundaries(prefix, priority)
    received = set(received)
    for p in priority:
        while (p, tips[p] + 1) in received:
            tips[p] += 1
    return extend_round_robin(prefix, tips, priority)


def negative_excludes_quorum(n, faults, positive, negative):
    # Only for statements an honest signer cannot issue together in the SAME context.
    return positive + negative > n + faults


def _boundaries(prefix, priority):
    if len(set(priority)) != len(priority):
        raise ValueError("priority must list each producer once")
    boundaries = dict.fromkeys(priority, 0)
    for p, height in prefix:
        if p not in boundaries or type(height) is not int or height != boundaries[p] + 1:
            raise ValueError("prefix must contain contiguous, unique producer blocks")
        boundaries[p] = height
    return boundaries


class CounterExecution:
    def __init__(self, keys):
        self._keys = dict(keys)
        self._cache = {}

    def run(self, order):
        state, executed, reused = {}, [], []
        for block in order:
            key = self._keys[block]
            before = state.get(key, 0)
            cached = self._cache.get(block)
            if cached is not None and cached[0] == before:
                after = cached[1]
                reused.append(block)
            else:
                after = before + 1
                self._cache[block] = (before, after)
                executed.append(block)
            state[key] = after
        return state, tuple(executed), tuple(reused)
