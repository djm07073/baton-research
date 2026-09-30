import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { rankProducers, deliveryTargets, compareOccurrences } from './cut-routing.mjs';

const config = {
  lanes: ['L0', 'L1', 'L2'], seed: 'research-v3',
  scopePositions: { A: 2, B: 2, C: 0, E: 1 }, rescueAfterCuts: 3,
};
const tx1 = { id: 'tx1', access: [{ key: 'A', mode: 'pureD' }, { key: 'B', mode: 'pureD' }, { key: 'C', mode: 'W' }] };
const tx2 = { id: 'tx2', access: [{ key: 'A', mode: 'pureD' }, { key: 'C', mode: 'R' }, { key: 'E', mode: 'RW' }] };

describe('cut-relative declared-access routing', () => {
  for (const row of [
    { name: 'first slot prefers the common C position', tx: tx1, slot: 1, want: ['L0', 'L1', 'L2'] },
    { name: 'multi-state tie follows logical priority', tx: tx2, slot: 1, want: ['L0', 'L1', 'L2'] },
    { name: 'second slot rotates the primary', tx: tx2, slot: 2, want: ['L1', 'L2', 'L0'] },
    { name: 'third slot rotates again', tx: tx1, slot: 3, want: ['L2', 'L0', 'L1'] },
    { name: 'fourth slot wraps without a new seed', tx: tx1, slot: 4, want: ['L0', 'L1', 'L2'] },
    { name: 'repeated scope is not an extra vote', tx: { id: 'dup', access: [{ key: 'C', mode: 'R' }, { key: 'E', mode: 'R' }, { key: 'E', mode: 'W' }] }, slot: 1, want: ['L0', 'L1', 'L2'] },
    { name: 'conditional defer contributes to affinity', tx: { id: 'bounded', access: [{ key: 'E', mode: 'conditionalD' }] }, slot: 2, want: ['L2', 'L1', 'L0'] },
    { name: 'declaration order does not affect routing', tx: { ...tx2, access: [...tx2.access].reverse() }, slot: 2, want: ['L1', 'L2', 'L0'] },
    { name: 'pure defer cannot hide an exact read on the same scope', tx: { id: 'mixed', access: [{ key: 'E', mode: 'R' }, { key: 'E', mode: 'pureD' }] }, slot: 1, want: ['L1', 'L0', 'L2'] },
    { name: 'reversing mixed modes preserves the read weight', tx: { id: 'mixed', access: [{ key: 'E', mode: 'pureD' }, { key: 'E', mode: 'R' }] }, slot: 1, want: ['L1', 'L0', 'L2'] },
    { name: 'scope hash golden vector prefers logical position two', tx: { id: 'unmapped', access: [{ key: 'unmapped', mode: 'W' }] }, slot: 1, want: ['L2', 'L0', 'L1'] },
    { name: 'zero-score hash golden vector orders positions zero two one', tx: { id: 'pure', access: [{ key: 'A', mode: 'pureD' }] }, slot: 1, want: ['L0', 'L2', 'L1'] },
  ]) it(row.name, () => assert.deepEqual(rankProducers(row.tx, config, row.slot), row.want));

  for (const row of [
    { name: 'one lane remains routable', lanes: ['only'], positions: { C: 0 }, slot: 7, want: ['only'] },
    { name: 'four lanes preserve full-list rotation', lanes: ['A', 'B', 'C', 'D'], positions: { C: 2 }, slot: 4, want: ['B', 'D', 'A', 'C'] },
    { name: 'large safe slot retains modular rank', lanes: ['A', 'B', 'C', 'D'], positions: { C: 2 }, slot: 9007199254740991, want: ['A', 'C', 'D', 'B'] },
  ]) it(row.name, () => assert.deepEqual(rankProducers(
    { id: 'single', access: [{ key: 'C', mode: 'W' }] }, { ...config, lanes: row.lanes, scopePositions: row.positions }, row.slot,
  ), row.want));

  it('zero-affinity fallback rotates logical positions, not physical hashes', () => {
    const tx = { id: 'pure', access: [{ key: 'A', mode: 'pureD' }] };
    const routes = [1, 2, 3, 4].map(slot => rankProducers(tx, config, slot));
    assert.equal(new Set(routes[0]).size, 3);
    assert.equal(new Set(routes.slice(0, 3).map(route => route[0])).size, 3);
    assert.deepEqual(routes[3], routes[0]);
    for (let i = 0; i < 3; i++) assert.equal(routes[1][i], config.lanes[(config.lanes.indexOf(routes[0][i]) + 1) % 3]);
  });

  it('unknown scopes use a stable hash position across slots', () => {
    const tx = { id: 'unmapped', access: [{ key: 'unmapped', mode: 'RW' }] };
    const routes = [1, 2, 3].map(slot => rankProducers(tx, config, slot));
    assert.equal(new Set(routes.map(route => route[0])).size, 3);
    assert.deepEqual(rankProducers(tx, { ...config, localQueueLength: 999 }, 1), routes[0]);
  });

  for (const row of [
    { name: 'slot zero is invalid', tx: tx1, cfg: config, slot: 0 },
    { name: 'duplicate producer identity is invalid', tx: tx1, cfg: { ...config, lanes: ['L0', 'L0'] }, slot: 1 },
    { name: 'unsupported mode cannot bypass weighting', tx: { id: 'bad', access: [{ key: 'C', mode: 'anything' }] }, cfg: config, slot: 1 },
    { name: 'scope position must exist in the lane range', tx: tx1, cfg: { ...config, scopePositions: { C: 7 } }, slot: 1 },
  ]) it(row.name, () => assert.throws(() => rankProducers(row.tx, row.cfg, row.slot)));
});

describe('soft delivery under contiguous finalized-cut progress', () => {
  for (const row of [
    { name: 'initial preferred producer', anchor: 10, finalized: 10, want: ['L1'] },
    { name: 'next finalized cut rotates pending routing', anchor: 10, finalized: 11, want: ['L2'] },
    { name: 'last ordinary cut before rescue', anchor: 10, finalized: 12, want: ['L0'] },
    { name: 'rescue reaches all producers', anchor: 10, finalized: 13, want: ['L0', 'L1', 'L2'] },
    { name: 'catch-up cannot skip rescue', anchor: 10, finalized: 17, want: ['L0', 'L1', 'L2'] },
    { name: 'ordered occurrence stops new routing', anchor: 10, finalized: 17, ordered: true, want: [] },
  ]) it(row.name, () => assert.deepEqual(deliveryTargets(tx1, config, row), row.want));

  it('a speculative inclusion hint cannot suppress rescue', () => assert.deepEqual(
    deliveryTargets(tx1, config, { anchor: 10, finalized: 13, seenBlock: true }), ['L0', 'L1', 'L2'],
  ));
  for (const row of [
    { name: 'future anchor requires synchronization', cfg: config, state: { anchor: 11, finalized: 10 } },
    { name: 'zero rescue horizon is invalid', cfg: { ...config, rescueAfterCuts: 0 }, state: { anchor: 10, finalized: 10 } },
  ]) it(row.name, () => assert.throws(() => deliveryTargets(tx1, row.cfg, row.state)));
});

describe('execution uses the actual inclusion slot, not the routing target', () => {
  for (const row of [
    { name: 'height precedes lane priority', left: { lane: 'L0', height: 1, index: 0 }, right: { lane: 'L1', height: 2, index: 0 }, anchors: {}, slot: 2, want: -1 },
    { name: 'equal heights follow the actual slot priority', left: { lane: 'L0', height: 1, index: 0, targetSlot: 1 }, right: { lane: 'L1', height: 1, index: 0 }, anchors: {}, slot: 2, want: 1 },
    { name: 'internal transaction order is preserved', left: { lane: 'L1', height: 1, index: 0 }, right: { lane: 'L1', height: 1, index: 1 }, anchors: {}, slot: 2, want: -1 },
    { name: 'provisional anchors prefer L1', left: { lane: 'L0', height: 2, index: 0 }, right: { lane: 'L1', height: 2, index: 0 }, anchors: {}, slot: 2, want: 1 },
    { name: 'canonical anchors can reverse that dependency', left: { lane: 'L0', height: 2, index: 0 }, right: { lane: 'L1', height: 2, index: 0 }, anchors: { L0: 1 }, slot: 2, want: -1 },
    { name: 'unequal absolute heights can have equal relative height', left: { lane: 'L0', height: 9, index: 0 }, right: { lane: 'L1', height: 2, index: 0 }, anchors: { L0: 8, L1: 1 }, slot: 2, want: 1 },
  ]) it(row.name, () => assert.equal(compareOccurrences(row.left, row.right, config, row.slot, row.anchors), row.want));

  for (const row of [
    { name: 'already ordered occurrence is not a new rank', lane: 'L0', height: 1, anchors: { L0: 1 } },
    { name: 'unknown producer is rejected', lane: 'absent', height: 1, anchors: {} },
    { name: 'negative ordering anchor is rejected', lane: 'L0', height: 1, anchors: { L0: -1 } },
  ]) it(row.name, () => assert.throws(() => compareOccurrences(
    { lane: row.lane, height: row.height, index: 0 }, { lane: 'L1', height: 1, index: 0 }, config, 1, row.anchors,
  )));

  for (const lane of ['constructor', 'toString', '__proto__']) it(`lane ${lane} does not inherit an ordering anchor`, () => assert.equal(
    compareOccurrences({ lane, height: 1, index: 0 }, { lane: 'other', height: 1, index: 0 }, { ...config, lanes: [lane, 'other'] }, 1), -1,
  ));
});
