"""Block-view synthesis model, not a consensus engine or cryptographic verifier.

Input denotes an already authenticated, immutable ordering descriptor. Signer
authentication, DA retention, canonical cut extraction and cross-view locking
are adapter obligations. Reports affect scheduling only; execution uses local
state and a trusted local cache. No report is a validity proof.

select raises NeedData for missing committed bytes, and InvalidInput for a
descriptor outside the adapter contract. Invalid individual reports are ignored.
Search parameters are protocol constants, never per-validator preferences.
execute rebuilds an overlay from the exact base; it does not mutate canonical
state, authenticate remote results, or wait for an ordering/result certificate.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from itertools import combinations


class InvalidInput(ValueError):
    pass


class NeedData(Exception):
    pass


def digest(value):
    def encode(obj):
        if is_dataclass(obj):
            return asdict(obj)
        raise TypeError(type(obj).__name__)
    return hashlib.sha256(json.dumps(value, default=encode, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class Context:
    epoch: str
    base_id: str
    base_root: str
    tips: tuple
    lanes: tuple
    committee: tuple
    faults: int
    workers: int = 2
    max_blocks: int = 64


@dataclass(frozen=True)
class Block:
    id: str
    lane: str
    height: int
    parent: str | None
    ops: tuple = ()


@dataclass(frozen=True)
class View:
    signer: int
    sequence: int
    base_id: str
    known: tuple
    edges: tuple
    executed: tuple


@dataclass(frozen=True)
class ViewRef:
    signer: int
    sequence: int
    digest: str


@dataclass(frozen=True)
class Input:
    context: Context
    nodes: tuple
    views: tuple = ()
    evidence: tuple = ()


@dataclass(frozen=True)
class Plan:
    nodes: tuple
    edges: tuple
    root: str
    input_root: str
    accepted_signers: tuple
    score: tuple
    expanded: int


@dataclass(frozen=True)
class Record:
    fingerprint: str
    program_root: str
    observations: tuple
    writes: tuple
    status: tuple


@dataclass(frozen=True)
class Execution:
    state: dict
    records: dict
    reused: tuple
    ran: tuple
    result_root: str


def quorum(ctx):
    n, f = len(ctx.committee), ctx.faults
    q = (n + f) // 2 + 1
    if f < 0 or q > n - f or len(set(ctx.committee)) != n or ctx.workers < 1:
        raise InvalidInput("invalid committee or fault bound")
    return q


def rank(ctx, block):
    tips = dict(ctx.tips)
    if block.lane not in tips or block.lane not in ctx.lanes:
        raise InvalidInput("unregistered lane")
    depth = block.height - tips[block.lane]
    if depth <= 0:
        raise InvalidInput("block precedes ordering anchor")
    return depth, ctx.lanes.index(block.lane)


def footprint(block):
    reads, writes = set(), set()
    for op in block.ops:
        kind = op[0]
        if kind == "set" and len(op) == 3:
            writes.add(op[1])
        elif kind == "add" and len(op) == 3:
            reads.add(op[1])
            writes.add(op[1])
        elif kind == "copy" and len(op) == 3:
            reads.add(op[2])
            writes.add(op[1])
        elif kind == "transfer" and len(op) == 4 and op[3] >= 0:
            reads.update(op[1:3])
            writes.update(op[1:3])
        else:
            raise InvalidInput("operation outside static model language")
    return reads, writes


def conflicts(a, b):
    ar, aw = footprint(a)
    br, bw = footprint(b)
    return bool(aw & (br | bw) or bw & ar)


def input_from_tips(ctx, anchor_ids, tips, block_store, views=(), evidence=()):
    """Expand an authenticated, closed per-lane selection into exact membership.

    anchor_ids contains (lane, block_id); tips contains (lane, height, block_id).
    The adapter must bind anchor_ids to ctx.base_id and uniquely agree the whole
    tips/view/evidence snapshot. Raw local L-QC tips are NOT sufficient. This
    function checks ancestry, not signatures, native extraction or settledness.
    An unchanged lane repeats its anchor; an absent slot is never guessed empty.
    None denotes a genesis anchor, never an unknown positive-height block.
    """
    quorum(ctx)
    lanes, starts = set(ctx.lanes), dict(ctx.tips)
    anchors = dict(anchor_ids)
    ends = {lane: (height, name) for lane, height, name in tips}
    if (len(lanes) != len(ctx.lanes) or len(ctx.tips) != len(lanes) or
            len(anchor_ids) != len(lanes) or len(tips) != len(lanes) or
            set(starts) != lanes or set(anchors) != lanes or set(ends) != lanes):
        raise InvalidInput("every lane needs one explicit anchor and selected tip")
    count = 0
    for lane in ctx.lanes:
        height, name = ends[lane]
        base_height, base_name = starts[lane], anchors[lane]
        for h, block_id in ((base_height, base_name), (height, name)):
            if (type(h) is not int or h < 0 or
                    not (isinstance(block_id, str) and block_id or
                         block_id is None and h == 0)):
                raise InvalidInput("invalid height or unknown tip identity")
        if height < base_height or height == base_height and name != base_name:
            raise InvalidInput("selected tip regresses or replaces the anchor")
        count += height - base_height
    # Bound authenticated fetch work before touching the local store.
    if (ctx.max_blocks < 1 or count > ctx.max_blocks or
            len(evidence) > ctx.max_blocks or len(views) > 2 * len(ctx.committee)):
        raise InvalidInput("tip selection exceeds fixed application window bounds")
    nodes = []
    for lane in ctx.lanes:
        height, name = ends[lane]
        while height > starts[lane]:
            if not isinstance(name, str) or not name:
                raise InvalidInput("selected ancestry ends before its anchor")
            if name not in block_store:
                raise NeedData((name,))
            block = block_store[name]
            if (block.id, block.lane, block.height) != (name, lane, height):
                raise InvalidInput("selected ancestry has a wrong identity, lane or height")
            nodes.append(name)
            name, height = block.parent, height - 1
        if name != anchors[lane]:
            raise InvalidInput("selected ancestry does not extend the exact anchor")
    return Input(ctx, tuple(sorted(nodes)), tuple(views), tuple(evidence))


def lane_edges(blocks):
    lanes = {}
    for block in blocks.values():
        lanes.setdefault(block.lane, []).append(block)
    edges = set()
    for lane in lanes.values():
        lane.sort(key=lambda b: (b.height, b.id))
        if len({b.height for b in lane}) != len(lane):
            raise InvalidInput("two selected blocks occupy one lane position")
        edges.update((a.id, b.id) for a, b in zip(lane, lane[1:]))
    return edges


def topological(nodes, edges, blocks, ctx, preference=()):
    pending = set(nodes)
    predecessors = {n: set() for n in nodes}
    for a, b in edges:
        if a not in pending or b not in pending or a == b:
            raise InvalidInput("invalid graph endpoint")
        predecessors[b].add(a)
    preferred = {b: i for i, b in enumerate(preference)}
    order = []
    while pending:
        ready = [b for b in pending if not predecessors[b] & pending]
        if not ready:
            raise InvalidInput("dependency cycle")
        chosen = min(ready, key=lambda b: (preferred.get(b, len(preferred)),
                                           rank(ctx, blocks[b]), b))
        order.append(chosen)
        pending.remove(chosen)
    return tuple(order)


def edges_for_order(blocks, order):
    if set(order) != set(blocks) or len(order) != len(blocks):
        raise InvalidInput("order must contain every block exactly once")
    positions = {n: i for i, n in enumerate(order)}
    hard = lane_edges(blocks)
    if any(positions[a] >= positions[b] for a, b in hard):
        raise InvalidInput("lane order reversal")
    edges = set(hard)
    for a, b in combinations(order, 2):
        if conflicts(blocks[a], blocks[b]):
            edges.add((a, b))
    return tuple(sorted(edges))


def fingerprints(ctx, blocks, order):
    edges_for_order(blocks, order)
    result, writers = {}, {}
    for name in order:
        reads, writes = footprint(blocks[name])
        # Keep all possible writers: a statically declared write may fail/no-op.
        parents = [(key, tuple(writers.get(key, ()))) for key in sorted(reads)]
        result[name] = digest((ctx.epoch, ctx.base_id, ctx.base_root,
                               blocks[name], parents))
        for key in writes:
            writers.setdefault(key, []).append((name, result[name]))
    return result


def _normalize_view(ctx, view, store):
    if view.base_id != ctx.base_id or view.sequence < 0:
        raise InvalidInput("stale report context")
    if len(set(view.known)) != len(view.known):
        raise InvalidInput("duplicate block in report")
    if len(view.edges) > len(view.known) * (len(view.known) - 1) // 2:
        raise InvalidInput("oversized or redundant dependency report")
    if not set(view.executed) <= set(view.known):
        raise InvalidInput("execution claim outside report")
    if not set(view.known) <= store.keys():
        raise InvalidInput("reference outside the committed evidence universe")
    blocks = {b: store[b] for b in view.known}
    # Local views may be partial, but their claimed lane order cannot reverse.
    hard = lane_edges(blocks)
    order = topological(view.known, set(view.edges) | hard, blocks, ctx)
    successors = {b: set() for b in blocks}
    for a, b in set(view.edges) | hard:
        successors[a].add(b)
    reach = {}
    for a in reversed(order):
        reach[a] = set(successors[a])
        for b in successors[a]:
            reach[a].update(reach[b])
    for a, b in combinations(sorted(blocks), 2):
        if conflicts(blocks[a], blocks[b]) and b not in reach[a] and a not in reach[b]:
            raise InvalidInput("report omits conflict orientation")
    edges = edges_for_order(blocks, order)
    executed = set(view.executed)
    if any(b in executed and a not in executed for a, b in edges):
        raise InvalidInput("executed region is not predecessor closed")
    fp = fingerprints(ctx, blocks, order)
    return {"view": view, "order": order, "edges": edges,
            "cache": {b: fp[b] for b in executed}}


def _resolve(inp, block_store, view_store):
    ctx = inp.context
    quorum(ctx)
    if (ctx.max_blocks < 1 or len(inp.nodes) > ctx.max_blocks or
            len(inp.evidence) > ctx.max_blocks or len(inp.views) > 2 * len(ctx.committee)):
        raise InvalidInput("ordering descriptor exceeds fixed application window bounds")
    if len(set(ctx.lanes)) != len(ctx.lanes) or set(ctx.lanes) != set(dict(ctx.tips)):
        raise InvalidInput("invalid lane roster")
    if len(set(inp.nodes)) != len(inp.nodes):
        raise InvalidInput("duplicate cut occurrence")
    universe = set(inp.nodes) | set(inp.evidence)
    missing = universe - block_store.keys()
    if missing:
        raise NeedData(tuple(sorted(missing)))
    blocks = {b: block_store[b] for b in inp.nodes}
    evidence = {b: block_store[b] for b in universe}
    for name, b in evidence.items():
        if name != b.id:
            raise InvalidInput("evidence identity mismatch")
        rank(ctx, b)
        footprint(b)
    for name, b in blocks.items():
        if name != b.id:
            raise InvalidInput("block identity mismatch")
        depth, _ = rank(ctx, b)
        footprint(b)
        if depth > 1:
            previous = [p for p in blocks.values()
                        if p.lane == b.lane and p.height == b.height - 1]
            if len(previous) != 1 or b.parent != previous[0].id:
                raise InvalidInput("selected lane suffix has a gap or wrong branch")
    lane_edges(blocks)
    refs = sorted(set(inp.views), key=lambda r: (r.signer, r.sequence, r.digest))
    normalized, rejected = {}, set()
    # All committed bytes are fetched first. A local timeout is not invalidity.
    for ref in refs:
        if ref.digest not in view_store:
            raise NeedData(ref.digest)
        if digest(view_store[ref.digest]) != ref.digest:
            raise NeedData(ref.digest)
    for signer in sorted(set(r.signer for r in refs) & set(ctx.committee)):
        group = [r for r in refs if r.signer == signer]
        sequence = max(r.sequence for r in group)
        latest = [r for r in group if r.sequence == sequence]
        if len({r.digest for r in latest}) != 1:
            rejected.add(signer)
            continue
        ref = latest[0]
        view = view_store[ref.digest]
        if view.signer != signer or view.sequence != sequence:
            rejected.add(signer)
            continue
        try:
            normalized[signer] = _normalize_view(ctx, view, evidence)
        except InvalidInput:
            rejected.add(signer)
    input_root = digest((ctx, sorted(inp.nodes),
                         sorted((b, digest(evidence[b])) for b in evidence), refs))
    return blocks, normalized, input_root


def _repair_cost(ctx, nodes, edges, dirty):
    dirty = set(dirty)
    if not dirty <= set(nodes):
        raise InvalidInput("repair outside selected blocks")
    pending, depths = set(nodes), {}
    while pending:
        ready = sorted(b for b in pending if all(a in depths for a, c in edges if c == b))
        if not ready:
            raise InvalidInput("cyclic repair graph")
        for b in ready:
            depths[b] = int(b in dirty) + max((depths[a] for a, c in edges if c == b),
                                             default=0)
            pending.remove(b)
    work = len(dirty)
    # This is a unit-work lower bound, not an achievable wall-clock prediction.
    latency = max(max(depths.values(), default=0), (work + ctx.workers - 1) // ctx.workers)
    return latency, work


def repair_cost(ctx, plan, dirty):
    return _repair_cost(ctx, plan.nodes, plan.edges, dirty)


def _score(ctx, blocks, order, reports):
    chosen = {b: blocks[b] for b in order}
    edges = edges_for_order(chosen, order)
    fp = fingerprints(ctx, chosen, order)
    costs, links = [], []
    edge_set = set(edges)
    for signer in ctx.committee:
        report = reports.get(signer)
        cache = report["cache"] if report else {}
        # Unit block weights avoid claimed runtime/gas and duplicated reports.
        dirty = [b for b in order if cache.get(b) != fp[b]]
        costs.append(_repair_cost(ctx, order, edges, dirty))
        links.append(sum((b, a) in edge_set for a, b in report["edges"])
                     if report else 0)
    costs.sort()
    q = quorum(ctx)
    return (costs[q + ctx.faults - 1], costs[q - 1], sum(c[0] for c in costs),
            sum(c[1] for c in costs), sum(links),
            tuple(rank(ctx, blocks[b]) for b in order))


def _orders(ctx, blocks, hard, reports, exact_limit, beam_width):
    n = len(blocks)
    beam, expanded = [()], 0
    for _ in range(n):
        following = []
        for prefix in beam:
            done = set(prefix)
            ready = [b for b in blocks if b not in done and
                     all(a in done for a, c in hard if c == b)]
            for b in sorted(ready, key=lambda x: (rank(ctx, blocks[x]), x)):
                following.append(prefix + (b,))
                expanded += 1
        following.sort(key=lambda order: (_score(ctx, blocks, order, reports), order))
        beam = following if n <= exact_limit else following[:beam_width]
    return beam, expanded


def select(inp, block_store, view_store, exact_limit=6, beam_width=16):
    if exact_limit < 0 or beam_width <= 0:
        raise InvalidInput("invalid deterministic search bounds")
    blocks, reports, input_root = _resolve(inp, block_store, view_store)
    ctx = inp.context
    hard = lane_edges(blocks)
    fallback = topological(blocks, hard, blocks, ctx)
    candidates = {fallback}
    prepared = sum(bool(set(report["cache"]) & blocks.keys()) for report in reports.values())
    expanded = 0
    # This checks the closed snapshot; it never waits for another report.
    if prepared > ctx.faults:
        for report in reports.values():
            proposed = {(a, b) for a, b in report["edges"] if a in blocks and b in blocks}
            try:
                candidates.add(topological(blocks, hard | proposed, blocks, ctx))
            except InvalidInput:
                pass  # A projected preference never removes a selected block.
        searched, expanded = _orders(ctx, blocks, hard, reports, exact_limit, beam_width)
        candidates.update(searched)
    winner = min(candidates, key=lambda order: (_score(ctx, blocks, order, reports), order))
    edges = edges_for_order(blocks, winner)
    nodes = tuple(sorted(blocks))
    score = _score(ctx, blocks, winner, reports)
    root = digest(("block-selection/v1", input_root, exact_limit, beam_width, nodes, edges))
    return Plan(nodes, edges, root, input_root, tuple(sorted(reports)), score, expanded)


def verify_proposal(inp, block_store, view_store, proposed, exact_limit=6, beam_width=16):
    expected = select(inp, block_store, view_store, exact_limit, beam_width)
    return (proposed.nodes, proposed.edges, proposed.root, proposed.input_root) == (
        expected.nodes, expected.edges, expected.root, expected.input_root)


def execute(ctx, plan, blocks, base, cache=None, order=None, remote_result=None):
    if remote_result is not None:
        raise InvalidInput("unverified remote reports cannot supply execution state")
    if digest(base) != ctx.base_root:
        raise InvalidInput("wrong base state")
    selected = {b: blocks[b] for b in plan.nodes}
    order = order or topological(plan.nodes, plan.edges, blocks, ctx)
    if len(order) != len(selected) or set(order) != set(selected):
        raise InvalidInput("execution missing a block")
    positions = {b: i for i, b in enumerate(order)}
    if any(positions[a] >= positions[b] for a, b in plan.edges):
        raise InvalidInput("worker schedule violates SelectedView")
    if edges_for_order(selected, order) != plan.edges:
        raise InvalidInput("incomplete or extraneous selected dependencies")
    fp = fingerprints(ctx, selected, order)
    state, records, reused, ran = dict(base), {}, [], []
    for name in order:
        block = blocks[name]
        reads, _ = footprint(block)
        observations = tuple((key, state.get(key)) for key in sorted(reads))
        program_root = digest((ctx.epoch, ctx.base_id, ctx.base_root, block))
        previous = cache.records.get(name) if cache else None
        if previous and previous.program_root == program_root and previous.observations == observations:
            # A changed predecessor graph need not change the values actually read.
            record = Record(fp[name], program_root, observations, previous.writes, previous.status)
            reused.append(name)
        else:
            local, touched, status = dict(state), set(), []
            for op in block.ops:
                kind = op[0]
                ok = True
                if kind == "set":
                    local[op[1]] = op[2]
                    touched.add(op[1])
                elif kind == "add":
                    local[op[1]] = local.get(op[1], 0) + op[2]
                    touched.add(op[1])
                elif kind == "copy":
                    local[op[1]] = local.get(op[2], 0)
                    touched.add(op[1])
                elif kind == "transfer":
                    _, src, dst, amount = op
                    ok = local.get(src, 0) >= amount
                    if ok:
                        local[src] = local.get(src, 0) - amount
                        local[dst] = local.get(dst, 0) + amount
                        touched.update((src, dst))
                else:
                    raise InvalidInput("unsupported operation")
                status.append(ok)
            record = Record(fp[name], program_root, observations,
                            tuple((k, local[k]) for k in sorted(touched)), tuple(status))
            ran.append(name)
        state.update(dict(record.writes))
        records[name] = record
    effects = [(b, records[b].status, records[b].writes) for b in sorted(records)]
    return Execution(state, records, tuple(reused), tuple(ran),
                     digest((plan.root, state, effects)))


def certified(ctx, subject, result, authenticated_votes):
    signers = {signer for signer, s, r in authenticated_votes
               if s == subject and r == result and signer in ctx.committee}
    return len(signers) >= quorum(ctx)
