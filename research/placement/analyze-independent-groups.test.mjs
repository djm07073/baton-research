import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { spawnSync } from 'node:child_process';
import { analyze } from './analyze-independent-groups.mjs';

const input = [
  { id: 'a', reads: [], writes: ['x'], cost: 3 },
  { id: 'b', reads: ['x'], writes: ['y'], cost: 2 },
  { id: 'c', reads: [], writes: ['z'], cost: 1 },
];

it('reports indivisible load and footprint coverage without claiming wall-clock latency', () => {
  const r = analyze(input, 2, 1, true);
  assert.equal(r.transactions, 3);
  assert.equal(r.componentCount, 2);
  assert.equal(r.largestComponentWorkFraction, 5 / 6);
  assert.deepEqual(r.componentPlacement.loads, [5, 1]);
  assert.equal(r.componentPlacement.crossProducerConflictPairs, 0);
  assert.equal(r.componentPlacement.simulation.maxReruns, 0);
  assert.equal(r.scenarioCount, 8);
  assert.equal(r.evidence, 'fixed-footprint closed-window symbolic model; not Ethereum execution or measured latency');
});

it('supports an empty trace without division by zero', () => {
  const r = analyze([], 2, 1, false);
  assert.equal(r.largestComponentWorkFraction, 0);
  assert.equal(r.componentPlacement.loadImbalance, 0);
  assert.equal(r.loadToLowerBoundRatio, 0);
});

describe('frequency-weighted group demand, not state-key counts', () => {
  const workloads = [
    {
      name: 'many cold keys do not outweigh one frequently used key',
      groups: [
        { id: 'a', calls: 10, keys: 1000, cost: 1 },
        { id: 'b', calls: 100, keys: 1, cost: 1 },
        { id: 'c', calls: 90, keys: 1, cost: 1 },
      ],
      loads: [100, 100], lowerBound: 100,
      demand: [
        { id: 'b-000', transactions: 100, distinctStateKeys: 1, meanExecutionCost: 1, executionWork: 100, producer: 0 },
        { id: 'c-000', transactions: 90, distinctStateKeys: 1, meanExecutionCost: 1, executionWork: 90, producer: 1 },
        { id: 'a-000', transactions: 10, distinctStateKeys: 1000, meanExecutionCost: 1, executionWork: 10, producer: 1 },
      ],
    },
    {
      name: 'expensive infrequent calls can equal frequent cheap calls',
      groups: [{ id: 'a', calls: 2, keys: 1, cost: 50 }, { id: 'b', calls: 100, keys: 1, cost: 1 }],
      loads: [100, 100], lowerBound: 100,
      demand: [
        { id: 'a-000', transactions: 2, distinctStateKeys: 1, meanExecutionCost: 50, executionWork: 100, producer: 0 },
        { id: 'b-000', transactions: 100, distinctStateKeys: 1, meanExecutionCost: 1, executionWork: 100, producer: 1 },
      ],
    },
    {
      name: 'a dominant hot key is indivisible despite unused capacity',
      groups: [{ id: 'a', calls: 190, keys: 1, cost: 1 }, { id: 'b', calls: 10, keys: 1, cost: 1 }],
      loads: [190, 10], lowerBound: 190,
      demand: [
        { id: 'a-000', transactions: 190, distinctStateKeys: 1, meanExecutionCost: 1, executionWork: 190, producer: 0 },
        { id: 'b-000', transactions: 10, distinctStateKeys: 1, meanExecutionCost: 1, executionWork: 10, producer: 1 },
      ],
    },
  ];
  for (const row of workloads) it(row.name, () => {
    const txs = row.groups.flatMap(g => Array.from({ length: g.calls }, (_, i) => ({
      id: `${g.id}-${String(i).padStart(3, '0')}`,
      reads: [`${g.id}:0`],
      writes: Array.from({ length: g.keys }, (_, j) => `${g.id}:${j}`),
      cost: g.cost,
    })));
    const result = analyze(txs, 2, 20, true);
    assert.deepEqual(result.groupDemand, row.demand);
    assert.deepEqual(result.componentPlacement.loads, row.loads);
    assert.equal(result.loadLowerBound, row.lowerBound);
    assert.equal(result.loadToLowerBoundRatio, 1);
    assert.equal(result.componentPlacement.simulation.maxReruns, 0);
  });

  it('counts a multi-key transaction once and averages heterogeneous execution costs', () => {
    const result = analyze([
      { id: 'a', reads: ['x', 'x'], writes: ['x', 'y'], cost: 2 },
      { id: 'b', reads: ['y'], writes: ['z'], cost: 8 },
    ], 2);
    assert.deepEqual(result.groupDemand, [
      { id: 'a', transactions: 2, distinctStateKeys: 3, meanExecutionCost: 5, executionWork: 10, producer: 0 },
    ]);
  });

  it('exposes the greedy gap instead of claiming optimal load balance', () => {
    const result = analyze([3, 3, 2, 2, 2].map((cost, i) => ({
      id: String(i), reads: [], writes: [`key-${i}`], cost,
    })), 2);
    assert.deepEqual(result.componentPlacement.loads, [7, 5]);
    // The disjoint allocations {3,3} and {2,2,2} attain the lower bound of 6.
    assert.equal(result.loadLowerBound, 6);
    assert.equal(result.loadToLowerBoundRatio, 7 / 6);
  });
});

for (const row of [
  { name: 'normalized JSONL from stdin', input: input.map(x => JSON.stringify(x)).join('\n'), status: 0, transactions: 3 },
  { name: 'invalid footprint schema', input: JSON.stringify({ id: 'bad' }), status: 1 },
  { name: 'malformed JSON', input: '{', status: 1 },
]) it(`CLI handles ${row.name}`, () => {
  const r = spawnSync(process.execPath, ['research/placement/analyze-independent-groups.mjs', '--producers', '2'], { input: row.input, encoding: 'utf8' });
  assert.equal(r.status, row.status);
  if (row.status === 0) assert.equal(JSON.parse(r.stdout).transactions, row.transactions);
  else assert.equal(r.stdout, '');
});
