"""Finite dependency-graph model; consensus decisions are external assumptions.

This does not authenticate votes, implement view change, or prove network liveness.
An edge B -> A means B lists A as a dependency, not an irrevocable pairwise order
inside a cycle. Node labels provide the common tie-break within a closed cycle.
"""


def supported_dependencies(reports, committee_size, faults, mandatory=frozenset()):
    if (faults < 0 or committee_size != 5 * faults + 1
            or len(reports) < committee_size - faults
            or not set(reports) <= set(range(committee_size))):
        raise ValueError("requires n=5f+1 and at least n-f distinct member reports")
    counts = {}
    for dependencies in reports.values():
        for node in set(dependencies):
            counts[node] = counts.get(node, 0) + 1
    return frozenset(mandatory) | frozenset(node for node, count in counts.items()
                                          if count >= faults + 1)


def ready_batches(dependencies, committed, executed=frozenset()):
    committed, executed = set(committed), set(executed)
    if not is_closed_cut(dependencies, committed, executed):
        raise ValueError("executed set must be committed and dependency-closed")

    reachable = {}
    for node in committed - executed:
        seen, pending = set(), [node]
        while pending:
            current = pending.pop()
            if current in seen or current in executed:
                continue
            seen.add(current)
            if current not in committed or current not in dependencies:
                break
            pending.extend(dependencies[current] - seen - executed)
        else:
            reachable[node] = seen

    remaining = set(reachable)
    groups = []
    while remaining:
        node = min(remaining)
        group = {other for other in remaining
                 if other in reachable[node] and node in reachable[other]}
        groups.append(tuple(sorted(group)))
        remaining -= group

    batches, done = [], set(executed)
    while groups:
        ready = [group for group in groups
                 if all(dependencies[node] <= done.union(group) for node in group)]
        if not ready:
            raise AssertionError("closed SCC condensation must have a ready batch")
        group = min(ready)
        batches.append(group)
        done.update(group)
        groups.remove(group)
    return tuple(batches)


def is_closed_cut(dependencies, committed, selected, previous=frozenset()):
    selected = set(selected)
    return (set(previous) <= selected <= set(committed)
            and all(node in dependencies and dependencies[node] <= selected
                    for node in selected))
