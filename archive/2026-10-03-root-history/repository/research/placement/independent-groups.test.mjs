import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { planIndependentGroups, routeSingleHome, simulateBlockArrivals } from './independent-groups.mjs';

const tx = (id, reads = [], writes = [], cost = 1) => ({ id, reads, writes, cost });
const groups = plan => plan.groups.map(g => g.ids).sort((a, b) => a[0].localeCompare(b[0]));
const blocks = (...rows) => rows.map(([lane, height, ids]) => ({ id: `${lane}:${height}`, lane, height, ids }));

describe('closed-set conflict components and whole-transaction placement', () => {
  for (const row of [
    { name: 'read-read sharing does not merge', input: [tx('a', ['x']), tx('b', ['x'])], want: [['a'], ['b']] },
    { name: 'writer-reader sharing merges', input: [tx('a', [], ['x']), tx('b', ['x'])], want: [['a', 'b']] },
    { name: 'reader-writer sharing merges', input: [tx('a', ['x']), tx('b', [], ['x'])], want: [['a', 'b']] },
    { name: 'blind writers merge conservatively', input: [tx('a', [], ['x']), tx('b', [], ['x'])], want: [['a', 'b']] },
    { name: 'multi-state transaction joins the full transitive closure', input: [tx('a', [], ['x']), tx('b', ['x'], ['y']), tx('c', ['y']), tx('d', [], ['z'])], want: [['a', 'b', 'c'], ['d']] },
    { name: 'a late writer connects previously independent readers', input: [tx('a', ['x']), tx('b', ['x']), tx('c', [], ['x'])], want: [['a', 'b', 'c']] },
    { name: 'fee payer is a real dependency', input: [tx('a', [], ['x', 'fee']), tx('b', [], ['y', 'fee'])], want: [['a', 'b']] },
    { name: 'no accesses remain independent', input: [tx('a'), tx('b')], want: [['a'], ['b']] },
    { name: 'empty workload is valid', input: [], want: [] },
  ]) it(row.name, () => assert.deepEqual(groups(planIndependentGroups(row.input, 3)), row.want));

  it('balances indivisible groups without cutting a dependency', () => {
    const p = planIndependentGroups([tx('a', [], ['x'], 3), tx('b', ['x'], [], 2), tx('c', [], ['z'], 3), tx('d', [], ['q'], 2)], 2, 2);
    assert.deepEqual(p.assignment, { a: 0, b: 0, c: 1, d: 1 });
    assert.deepEqual(p.loads, [5, 5]);
    assert.deepEqual(p.blocks, blocks([0, 1, ['a', 'b']], [1, 1, ['c', 'd']]));
    assert.equal(p.loadLowerBound, 5);
  });

  it('reports an oversized component rather than splitting it to meet a target', () => {
    const p = planIndependentGroups([tx('a', [], ['x']), tx('b', ['x']), tx('c', [], ['x'])], 3);
    assert.deepEqual(p.loads, [3, 0, 0]);
    assert.equal(p.loadLowerBound, 3);
  });

  it('group IDs and assignments do not depend on declaration or input enumeration order', () => {
    const input = [tx('a', ['x', 'x'], ['y']), tx('b', ['y']), tx('c', [], ['z'])];
    const a = planIndependentGroups(input, 2);
    const b = planIndependentGroups([...input].reverse(), 2);
    assert.deepEqual(a.assignment, b.assignment);
    assert.deepEqual(groups(a), groups(b));
  });

  for (const row of [
    { name: 'duplicate transaction ID', input: [tx('a'), tx('a')], lanes: 2 },
    { name: 'invalid cost', input: [tx('a', [], [], 0)], lanes: 2 },
    { name: 'unknown access schema', input: [{ id: 'a', access: ['x'] }], lanes: 2 },
    { name: 'no producers', input: [], lanes: 0 },
    { name: 'non-string scope', input: [tx('a', [3])], lanes: 2 },
  ]) it(`rejects ${row.name}`, () => assert.throws(() => planIndependentGroups(row.input, row.lanes)));
});

describe('fixed-interval admission never merges already exposed groups', () => {
  const map = { x: 0, y: 1, z: 0 };
  for (const row of [
    { name: 'single-home multi-state access', transaction: tx('a', ['x'], ['z']), want: { kind: 'admit', producer: 0 } },
    { name: 'cross-home access cannot enter the independent stream', transaction: tx('a', ['x'], ['y']), want: { kind: 'defer', reason: 'multiple-homes' } },
    { name: 'unknown state is not silently assigned from a private view', transaction: tx('a', [], ['new']), want: { kind: 'defer', reason: 'unmapped-scope' } },
    { name: 'no state access has a deterministic default', transaction: tx('a'), want: { kind: 'admit', producer: 0 } },
    { name: 'read-only across mutable homes is conservatively deferred', transaction: tx('a', ['x', 'y']), want: { kind: 'defer', reason: 'multiple-homes' } },
  ]) it(row.name, () => assert.deepEqual(routeSingleHome(row.transaction, map, 2), row.want));
  it('rejects unauthorized producer positions', () => assert.throws(() => routeSingleHome(tx('a', ['x']), { x: 9 }, 2)));
});

describe('exhaustive small-state independence audit', () => {
  it('matches independently computed conflict closure for all 4096 three-transaction two-key footprints', () => {
    for (let encoded = 0; encoded < 4096; encoded++) {
      const input = [0, 1, 2].map(i => {
        const mask = (encoded >> (4 * i)) & 15;
        return tx(String(i), ['x', 'y'].filter((_, k) => mask & (1 << (2 * k))), ['x', 'y'].filter((_, k) => mask & (2 << (2 * k))));
      });
      const connected = input.map((a, i) => input.map((b, j) => i === j ||
        a.writes.some(k => b.reads.includes(k) || b.writes.includes(k)) || b.writes.some(k => a.reads.includes(k))));
      for (let k = 0; k < 3; k++) for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) connected[i][j] ||= connected[i][k] && connected[k][j];
      const plan = planIndependentGroups(input, 3);
      for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
        const same = plan.groups.some(g => g.ids.includes(String(i)) && g.ids.includes(String(j)));
        assert.equal(same, connected[i][j], `closure ${encoded}: ${i},${j}`);
      }
      for (const arrival of permutations(plan.blocks.map(b => b.id))) {
        assert.equal(simulateBlockArrivals(input, plan.blocks, arrival).reruns, 0, `schedule ${encoded}: ${arrival}`);
      }
    }
  });

  it('preserves actual conditional values and per-tx outputs across all lane-preserving execution orders', () => {
    const input = [tx('a', ['x'], ['x']), tx('b', ['x'], ['y']), tx('c', ['z'], ['z'])];
    const plan = planIndependentGroups(input, 2);
    const execute = order => {
      const state = { x: 5, y: 0, z: 8 }, outputs = {};
      for (const id of order) {
        if (id === 'a') { state.x += 2; outputs.a = state.x; }
        if (id === 'b') { state.y = state.x >= 7 ? 100 : -1; outputs.b = state.y; }
        if (id === 'c') { state.z -= 3; outputs.c = state.z; }
      }
      return { state, outputs };
    };
    assert.equal(plan.assignment.a, plan.assignment.b);
    assert.notEqual(plan.assignment.a, plan.assignment.c);
    for (const order of permutations(['a', 'b', 'c'])) if (order.indexOf('a') < order.indexOf('b')) {
      assert.deepEqual(execute(order), { state: { x: 7, y: 100, z: 5 }, outputs: { a: 7, b: 100, c: 5 } });
    }
    assert.equal(execute(['b', 'a', 'c']).outputs.b, -1);
  });
});

describe('symbolic read-version replay under block arrival permutations', () => {
  const b = blocks([0, 1, ['a']], [1, 1, ['b']]);
  for (const row of [
    { name: 'independent writes survive the reversed arrival order', input: [tx('a', [], ['x']), tx('b', [], ['y'])], reruns: 0 },
    { name: 'late predecessor invalidates a prior read', input: [tx('a', [], ['x']), tx('b', ['x'], ['y'])], reruns: 1 },
    { name: 'conflict count is not reexecution count for blind writes', input: [tx('a', [], ['x']), tx('b', [], ['x'])], reruns: 0 },
  ]) it(row.name, () => {
    const result = simulateBlockArrivals(row.input, b, ['1:1', '0:1']);
    assert.equal(result.reruns, row.reruns);
    assert.equal(result.executions, row.input.length + row.reruns);
    assert.deepEqual(result.state, simulateBlockArrivals(row.input, b, ['0:1', '1:1']).state);
  });

  it('waits for the same-lane predecessor instead of speculating across a gap', () => {
    const input = [tx('a', [], ['x']), tx('b', ['x'], ['y'])];
    const result = simulateBlockArrivals(input, blocks([0, 1, ['a']], [0, 2, ['b']]), ['0:2', '0:1']);
    assert.equal(result.reruns, 0);
    assert.equal(result.prefixWaitEvents, 1);
  });

  it('preserves a dependency chain across every block-arrival permutation after placement', () => {
    const input = [tx('a', [], ['x']), tx('b', ['x'], ['y']), tx('c', ['y']), tx('d', [], ['z'])];
    const plan = planIndependentGroups(input, 3);
    const canonical = [...plan.blocks].sort((a, b) => a.height - b.height || a.lane - b.lane).map(b => b.id);
    const expected = simulateBlockArrivals(input, plan.blocks, canonical);
    for (const arrival of permutations(canonical)) {
      const got = simulateBlockArrivals(input, plan.blocks, arrival);
      assert.equal(got.reruns, 0, JSON.stringify(arrival));
      assert.deepEqual(got.state, expected.state);
      assert.deepEqual(got.outputs, expected.outputs);
    }
  });

  for (const row of [
    { name: 'missing selected block', b, arrival: ['0:1'] },
    { name: 'repeated arrival', b, arrival: ['0:1', '0:1'] },
    { name: 'same transaction appears twice', b: blocks([0, 1, ['a']], [1, 1, ['a']]), arrival: ['0:1', '1:1'] },
    { name: 'gap in selected lane prefix', b: blocks([0, 2, ['a']], [1, 1, ['b']]), arrival: ['0:2', '1:1'] },
  ]) it(`rejects ${row.name}`, () => assert.throws(() => simulateBlockArrivals([tx('a'), tx('b')], row.b, row.arrival)));
});

function* permutations(xs) {
  if (xs.length === 0) { yield []; return; }
  for (let i = 0; i < xs.length; i++) for (const tail of permutations(xs.filter((_, j) => i !== j))) yield [xs[i], ...tail];
}
