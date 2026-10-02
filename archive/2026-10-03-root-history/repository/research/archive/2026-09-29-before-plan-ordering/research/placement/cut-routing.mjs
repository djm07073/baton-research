import { createHash } from 'node:crypto';

function integer(value, minimum = 0) {
  if (!Number.isSafeInteger(value) || value < minimum) throw new Error('Invalid bounded integer');
  return value;
}

function laneCount(config) {
  if (!Array.isArray(config.lanes) || config.lanes.length === 0 ||
      config.lanes.some(lane => typeof lane !== 'string' || lane.length === 0) ||
      new Set(config.lanes).size !== config.lanes.length) throw new Error('Invalid lane configuration');
  return config.lanes.length;
}

function digest(...fields) {
  const hash = createHash('sha256');
  for (const field of fields) {
    const bytes = Buffer.isBuffer(field) ? field : Buffer.from(field, 'utf8');
    const length = Buffer.alloc(4);
    length.writeUInt32BE(bytes.length);
    hash.update(length).update(bytes);
  }
  return hash.digest('hex');
}

function encodedPosition(position) {
  const bytes = Buffer.alloc(8);
  bytes.writeBigUInt64BE(BigInt(position));
  return bytes;
}

export function rankProducers(tx, config, slot) {
  const m = laneCount(config);
  integer(slot, 1);
  if (typeof config.seed !== 'string' || typeof tx.id !== 'string' || !Array.isArray(tx.access)) throw new Error('Invalid routing input');
  const weights = new Map();
  const allowed = new Set(['R', 'W', 'RW', 'pureD', 'conditionalD']);
  for (const { key, mode } of tx.access) {
    if (typeof key !== 'string' || key.length === 0 || !allowed.has(mode)) throw new Error('Invalid normalized access');
    weights.set(key, Math.max(weights.get(key) ?? 0, mode === 'pureD' ? 0 : 1));
  }
  const scores = Array(m).fill(0);
  for (const [key, weight] of weights) {
    const position = Object.hasOwn(config.scopePositions ?? {}, key)
      ? config.scopePositions[key]
      : Number(BigInt(`0x${digest('scope-v3', config.seed, key)}`) % BigInt(m));
    integer(position);
    if (position >= m) throw new Error('Scope position outside lane range');
    scores[position] += weight;
  }
  const positions = Array.from({ length: m }, (_, i) => i);
  if (scores.every(score => score === 0)) {
    const hashes = positions.map(i => digest('zero-v3', config.seed, tx.id, encodedPosition(i)));
    positions.sort((a, b) => hashes[a] < hashes[b] ? -1 : hashes[a] > hashes[b] ? 1 : a - b);
  } else {
    positions.sort((a, b) => scores[b] - scores[a] || a - b);
  }
  const rotation = (slot - 1) % m;
  return positions.map(position => config.lanes[(position + rotation) % m]);
}

export function deliveryTargets(tx, config, { anchor, finalized, ordered = false }) {
  laneCount(config);
  integer(config.rescueAfterCuts, 1);
  integer(anchor);
  integer(finalized);
  if (finalized < anchor) throw new Error('Anchor not in the synchronized prefix');
  if (ordered) return [];
  const route = rankProducers(tx, config, integer(finalized + 1, 1));
  return finalized - anchor >= config.rescueAfterCuts ? [...config.lanes] : [route[0]];
}

export function compareOccurrences(left, right, config, slot, anchors = {}) {
  const m = laneCount(config);
  integer(slot, 1);
  const rank = occurrence => {
    const laneIndex = config.lanes.indexOf(occurrence.lane);
    if (laneIndex < 0) throw new Error('Unknown lane');
    const height = integer(occurrence.height, 1);
    const anchor = integer(Object.hasOwn(anchors, occurrence.lane) ? anchors[occurrence.lane] : 0);
    if (height <= anchor) throw new Error('Occurrence is already ordered');
    return [height - anchor, (laneIndex - (slot - 1) % m + m) % m, integer(occurrence.index)];
  };
  const a = rank(left);
  const b = rank(right);
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
  return 0;
}
