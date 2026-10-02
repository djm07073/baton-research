import { createHash } from 'node:crypto';

function compare(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
function integer(n, minimum = 0) {
  if (!Number.isSafeInteger(n) || n < minimum) throw new Error('Invalid bounded integer');
  return n;
}
function nonempty(s) {
  if (typeof s !== 'string' || !s.length) throw new Error('Expected a nonempty identifier');
  return s;
}
function normalize(txs) {
  if (!Array.isArray(txs)) throw new Error('Expected a transaction array');
  const seen = new Set();
  return txs.map(t => {
    nonempty(t.id);
    if (seen.has(t.id)) throw new Error('Duplicate transaction ID');
    seen.add(t.id);
    if (!Array.isArray(t.reads) || !Array.isArray(t.writes)) throw new Error('Explicit reads and writes required');
    return {
      id: t.id,
      reads: [...new Set(t.reads.map(nonempty))].sort(compare),
      writes: [...new Set(t.writes.map(nonempty))].sort(compare),
      cost: integer(t.cost ?? 1, 1),
    };
  });
}

/** Closed, complete footprint set only. Groups are indivisible; no balance guarantee
 * overrides independence. Input order is retained within each producer's blocks.
 * Cost is a declared integer proxy, not a measured execution time.
 */
export function planIndependentGroups(transactions, producers, blockSize = 1) {
  integer(producers, 1);
  integer(blockSize, 1);
  const txs = normalize(transactions);
  const parents = txs.map((_, i) => i);
  const ranks = txs.map(() => 0);
  function root(i) {
    while (parents[i] !== i) {
      parents[i] = parents[parents[i]];
      i = parents[i];
    }
    return i;
  }
  function union(a, b) {
    a = root(a); b = root(b);
    if (a === b) return;
    if (ranks[a] < ranks[b]) [a, b] = [b, a];
    parents[b] = a;
    if (ranks[a] === ranks[b]) ranks[a]++;
  }
  const scopes = new Map();
  txs.forEach((t, i) => {
    for (const key of new Set([...t.reads, ...t.writes])) {
      if (!scopes.has(key)) scopes.set(key, { users: [], writer: undefined });
      scopes.get(key).users.push(i);
    }
    for (const key of t.writes) scopes.get(key).writer = i;
  });
  // A writer connects all users of its key; read-only sharing creates no edge.
  // This obtains the same components without materializing a quadratic clique.
  for (const { users, writer } of scopes.values()) if (writer !== undefined) {
    for (const i of users) union(writer, i);
  }
  const members = new Map();
  txs.forEach((t, i) => {
    const r = root(i);
    if (!members.has(r)) members.set(r, { ids: [], cost: 0 });
    const group = members.get(r);
    group.ids.push(t.id);
    group.cost = integer(group.cost + t.cost, 1);
  });
  const groups = [...members.values()];
  for (const group of groups) group.ids.sort(compare);
  groups.sort((a, b) => b.cost - a.cost || compare(a.ids[0], b.ids[0]));
  const loads = Array(producers).fill(0);
  const routes = new Map();
  for (const group of groups) {
    let producer = 0;
    for (let i = 1; i < producers; i++) if (loads[i] < loads[producer]) producer = i;
    group.producer = producer;
    loads[producer] = integer(loads[producer] + group.cost);
    for (const id of group.ids) routes.set(id, producer);
  }
  const blocks = [];
  for (let lane = 0; lane < producers; lane++) {
    const ids = txs.filter(t => routes.get(t.id) === lane).map(t => t.id);
    for (let start = 0; start < ids.length; start += blockSize) {
      const height = start / blockSize + 1;
      blocks.push({ id: `${lane}:${height}`, lane, height, ids: ids.slice(start, start + blockSize) });
    }
  }
  const total = loads.reduce((sum, n) => integer(sum + n), 0);
  return {
    groups, blocks, loads,
    assignment: Object.fromEntries([...routes].sort((a, b) => compare(a[0], b[0]))),
    loadLowerBound: Math.max(total / producers, ...groups.map(g => g.cost), 0),
  };
}

/** Guard for an already authorized, immutable interval map. A defer result is
 * NOT a retry/failover protocol. Cross-home work cannot enter this fast stream.
 */
export function routeSingleHome(transaction, map, producers) {
  integer(producers, 1);
  const [t] = normalize([transaction]);
  const homes = new Set();
  for (const key of new Set([...t.reads, ...t.writes])) {
    if (!Object.hasOwn(map, key)) return { kind: 'defer', reason: 'unmapped-scope' };
    const home = integer(map[key]);
    if (home >= producers) throw new Error('Invalid producer position');
    homes.add(home);
  }
  return homes.size > 1
    ? { kind: 'defer', reason: 'multiple-homes' }
    : { kind: 'admit', producer: homes.size ? [...homes][0] : 0 };
}

function hash(value) { return createHash('sha256').update(JSON.stringify(value)).digest('hex'); }

/** Fixed-footprint SYMBOLIC model. Replays known zipped blocks on each arrival,
 * reusing a transaction only when its symbolic read observations still match.
 * Writes depend on ID and all reads; this is not an EVM or STM performance model.
 * All selected blocks eventually arrive, parent is fixed, forks are unsupported.
 */
export function simulateBlockArrivals(transactions, blocks, arrival) {
  const txs = normalize(transactions);
  const byTx = new Map(txs.map(t => [t.id, t]));
  const byBlock = new Map();
  const lanes = new Map();
  const occurrences = new Set();
  for (const b of blocks) {
    nonempty(b.id); integer(b.lane); integer(b.height, 1);
    if (byBlock.has(b.id) || !Array.isArray(b.ids) || !b.ids.length) throw new Error('Invalid block');
    byBlock.set(b.id, b);
    if (!lanes.has(b.lane)) lanes.set(b.lane, new Map());
    if (lanes.get(b.lane).has(b.height)) throw new Error('Equivocating lane position');
    lanes.get(b.lane).set(b.height, b);
    for (const id of b.ids) {
      if (!byTx.has(id) || occurrences.has(id)) throw new Error('Missing or duplicate transaction');
      occurrences.add(id);
    }
  }
  if (occurrences.size !== txs.length) throw new Error('Incomplete workload');
  for (const heights of lanes.values()) for (let h = 1; h <= heights.size; h++) {
    if (!heights.has(h)) throw new Error('Missing lane prefix');
  }
  if (arrival.length !== blocks.length || new Set(arrival).size !== blocks.length || arrival.some(id => !byBlock.has(id))) {
    throw new Error('Arrival must be a permutation of the selected blocks');
  }
  const received = new Set(), available = new Set(), cache = new Map();
  const frontier = new Map([...lanes.keys()].map(lane => [lane, 0]));
  let executions = 0, reruns = 0, rerunCost = 0, prefixWaitEvents = 0;
  let state = new Map(), outputs = [];
  for (const id of arrival) {
    received.add(id);
    const block = byBlock.get(id);
    if (block.height > frontier.get(block.lane) + 1) prefixWaitEvents++;
    for (const [lane, heights] of lanes) {
      let h = frontier.get(lane) + 1;
      while (heights.has(h) && received.has(heights.get(h).id)) available.add(heights.get(h++).id);
      frontier.set(lane, h - 1);
    }
    state = new Map(); outputs = [];
    const order = blocks.filter(b => available.has(b.id)).sort((a, b) => a.height - b.height || a.lane - b.lane);
    for (const b of order) for (const txid of b.ids) {
      const t = byTx.get(txid);
      const reads = t.reads.map(key => [key, state.get(key) ?? `base:${key}`]);
      const fingerprint = hash([t.id, reads]);
      const old = cache.get(t.id);
      if (!old || old.fingerprint !== fingerprint) {
        executions++;
        if (old) { reruns++; rerunCost += t.cost; }
        cache.set(t.id, { fingerprint, writes: t.writes.map(key => [key, hash([fingerprint, key])]) });
      }
      for (const [key, value] of cache.get(t.id).writes) state.set(key, value);
      outputs.push([t.id, fingerprint]);
    }
  }
  return { executions, reruns, rerunCost, prefixWaitEvents, outputs, state: Object.fromEntries([...state].sort((a, b) => compare(a[0], b[0]))) };
}
