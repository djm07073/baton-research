import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { planIndependentGroups, simulateBlockArrivals } from './independent-groups.mjs';

function digest(id) { return createHash('sha256').update(id).digest('hex'); }
function assignedBlocks(txs, assignment, producers, blockSize) {
  const blocks = [];
  for (let lane = 0; lane < producers; lane++) {
    const ids = txs.filter(t => assignment[t.id] === lane).map(t => t.id);
    for (let i = 0; i < ids.length; i += blockSize) {
      const height = i / blockSize + 1;
      blocks.push({ id: `${lane}:${height}`, lane, height, ids: ids.slice(i, i + blockSize) });
    }
  }
  return blocks;
}
function summarize(txs, assignment, blocks, producers, runSimulation) {
  const loads = Array(producers).fill(0);
  for (const t of txs) loads[assignment[t.id]] += t.cost ?? 1;
  let crossProducerConflictPairs = 0;
  for (let i = 0; i < txs.length; i++) for (let j = i + 1; j < txs.length; j++) {
    const a = txs[i], b = txs[j];
    if (assignment[a.id] !== assignment[b.id] &&
      (a.writes.some(k => b.reads.includes(k) || b.writes.includes(k)) || b.writes.some(k => a.reads.includes(k)))) crossProducerConflictPairs++;
  }
  const mean = loads.reduce((a, b) => a + b, 0) / producers;
  const report = { loads, loadImbalance: mean ? Math.max(...loads) / mean : 0, crossProducerConflictPairs };
  if (runSimulation) {
    const canonical = [...blocks].sort((a, b) => a.height - b.height || a.lane - b.lane).map(b => b.id);
    const arrivals = [canonical, [...canonical].reverse()];
    for (let seed = 1; seed <= 6; seed++) {
      const order = [...canonical];
      let random = seed;
      for (let i = order.length - 1; i > 0; i--) {
        random = (Math.imul(random, 1664525) + 1013904223) >>> 0;
        const j = random % (i + 1);
        [order[i], order[j]] = [order[j], order[i]];
      }
      arrivals.push(order);
    }
    const results = arrivals.map(arrival => simulateBlockArrivals(txs, blocks, arrival));
    const oracle = JSON.stringify([results[0].state, results[0].outputs]);
    if (results.some(r => JSON.stringify([r.state, r.outputs]) !== oracle)) throw new Error('Serial-equivalence check failed');
    report.simulation = {
      rerunsByScenario: results.map(r => r.reruns),
      maxReruns: Math.max(...results.map(r => r.reruns)),
      maxRerunCost: Math.max(...results.map(r => r.rerunCost)),
      prefixWaitEventsByScenario: results.map(r => r.prefixWaitEvents),
      serialEquivalentInModel: true,
    };
  }
  return report;
}

/** Analysis of a supplied closed window. Accesses observed after Ethereum execution
 * are oracle inputs, not prospective declarations. No wall-clock latency is inferred.
 */
export function analyze(txs, producers = 6, blockSize = 1, runSimulation = false) {
  if (!Array.isArray(txs) || txs.length > 2000) throw new Error('Pilot limit: at most 2000 transactions per window');
  const plan = planIndependentGroups(txs, producers, blockSize);
  const hashAssignment = Object.fromEntries(txs.map(t => [t.id, Number(BigInt(`0x${digest(t.id)}`) % BigInt(producers))]));
  const hashBlocks = assignedBlocks(txs, hashAssignment, producers, blockSize);
  const total = plan.loads.reduce((a, b) => a + b, 0);
  const byId = new Map(txs.map(t => [t.id, t]));
  const groupDemand = plan.groups.map(g => ({
    id: g.ids[0],
    transactions: g.ids.length,
    distinctStateKeys: new Set(g.ids.flatMap(id => [...byId.get(id).reads, ...byId.get(id).writes])).size,
    meanExecutionCost: g.cost / g.ids.length,
    executionWork: g.cost,
    producer: g.producer,
  }));
  return {
    evidence: 'fixed-footprint closed-window symbolic model; not Ethereum execution or measured latency',
    transactions: txs.length, producers, blockSize, scenarioCount: runSimulation ? 8 : 0,
    componentCount: plan.groups.length,
    groupDemand,
    largestComponentWorkFraction: total ? Math.max(...plan.groups.map(g => g.cost)) / total : 0,
    loadLowerBound: plan.loadLowerBound,
    loadToLowerBoundRatio: plan.loadLowerBound ? Math.max(...plan.loads) / plan.loadLowerBound : 0,
    componentPlacement: summarize(txs, plan.assignment, plan.blocks, producers, runSimulation),
    txHashPlacement: summarize(txs, hashAssignment, hashBlocks, producers, runSimulation),
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    let input = 0, producers = 6, blockSize = 1, simulation = false;
    const args = process.argv.slice(2);
    for (let i = 0; i < args.length; i++) {
      if (args[i] === '--input' && args[i + 1]) input = args[++i];
      else if (args[i] === '--producers' && args[i + 1]) producers = Number(args[++i]);
      else if (args[i] === '--block-size' && args[i + 1]) blockSize = Number(args[++i]);
      else if (args[i] === '--simulate') simulation = true;
      else throw new Error('Usage: --input FILE(optional; otherwise stdin) --producers N --block-size N --simulate(optional)');
    }
    const raw = readFileSync(input, 'utf8');
    if (Buffer.byteLength(raw) > 16 * 1024 * 1024) throw new Error('Pilot limit: 16 MiB of normalized JSONL');
    const txs = raw.split(/\r?\n/).filter(line => line.trim()).map(line => JSON.parse(line));
    process.stdout.write(JSON.stringify(analyze(txs, producers, blockSize, simulation), null, 2) + '\n');
  } catch (error) {
    process.stderr.write(error.message + '\n');
    process.exitCode = 1;
  }
}
