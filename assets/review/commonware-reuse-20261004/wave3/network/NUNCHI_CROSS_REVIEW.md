# Independent Nunchi mempool P2P/admission review

Reviewed `nunchi-labs/sdk` at immutable `eea35ced709f68c15d6fbc8bcc754696a7e44374` as a newly discovered reuse candidate. Nine relevant Rust/TOML files were independently downloaded and checked against the pinned complete tree's blob SHA-1, with SHA-256 receipts in [nunchi-cross-review-manifest.json](nunchi-cross-review-manifest.json). No implementation, compile, benchmark, dependency, policy selection or external mutation performed.

## Candidate verdict

**Retain as a concrete generic pool candidate, conditional on nonce/identity/replacement semantics and lifecycle adaptation.** This supplies substantially more real reusable pool functionality than a generic queue: `PoolTransaction`, signature/size admission, digest dedup, nonce lanes, replacement, bounded per-account/global counts, non-destructive gap-free selection, expiry/status, canonical nonce/digest notifications and actual direct Commonware P2P broadcast. Do not call it an upstream Commonware primitive or an already complete Baton mempool. Its package depends on Nunchi common/crypto and Commonware release 2026.9.0, and its `PoolTransaction::digest` is specifically SHA-256. [trait](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/tx.rs#L32), [workspace dependencies](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/Cargo.toml#L52).

Its stateful nonce admission and same-nonce last-write replacement are existing package policies. Reuse must not silently adopt these policies in Baton's undecided tx/static-filtering cells. A custom transaction can implement `PoolTransaction`, but the implementation must supply trustworthy content digest, nonce key, byte size and signature subject. [admission](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L96).

## Actual P2P connections

`Mempool::start_p2p(context, (Sender, Receiver))` directly accepts the existing Commonware authenticated channel pair. Its bounds are `S: Sender`, `R: Receiver<PublicKey=S::PublicKey>`, and `T: Encode + Read<Cfg=()>`; no second transport is required. [entry point](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L292).

RPC `submit`/`submit_many` stateless-check outside the actor, enqueue verified transactions, then the actor performs pool dedup/nonce/capacity admission. Successful local admissions call `sender.send(Recipients::All, tx.encode(), false)` once before responding to RPC. Incoming transactions are decoded, stateless-checked and admitted on the actor itself and **not re-broadcast**. [RPC](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L64), [outbound gossip](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L433), [inbound](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L473).

This is direct broadcast to currently connected/allowed peers, not multi-hop epidemic gossip or anti-entropy. No inventory, fetch/resolver, retransmission, offline-peer replay or remote admission ACK appears in this implementation. If sender's attempted-recipient list is empty, the actor logs and returns the local admission result anyway; a nonempty list also does not mean receipt. If the P2P receiver closes, the actor explicitly continues as node-local pool without restarting gossip. These behaviors are useful concrete boundaries when comparing candidates rather than claims that all transaction dissemination is solved.

## Nunchi P1 — raw decoding precedes pool byte/resource admission

Inbound `handle_network` calls `T::read_cfg(&mut bytes, &())`, then `Pool::check_stateless`, and only then `admit_verified`. The pool's `max_tx_bytes` is checked on `tx.encoded_size()` **after decode and signature verification**. [decode call](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L478), [stateless order](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L81).

Consequences for adaptation:

- The transport bounds raw frame size, but the package does not apply `PoolConfig::max_tx_bytes` to the incoming raw buffer before decoding.
- `Read<Cfg=()>` prevents supplying a per-start dynamic tx decode budget through this API. A selected transaction decoder can enforce intrinsic bounds, but those bounds must actually be inspected; the trait alone supplies no universal nested-object/allocation/CPU limit.
- The selected generic `T::read_cfg` is not followed by a buffer-exhaustion check. If T reads one transaction and leaves trailing bytes, this entry point accepts the prefix transaction. It is not equivalent to Commonware's complete-frame `Decode::decode_cfg`. This is a source-level parser acceptance fact, not a tested exploit or claim about every operation type.
- Verification on incoming P2P traffic runs on the one pool actor before dedup/capacity rejection, so flood CPU and decode/verification work require the application's existing ingress budget review; mailbox count is not that bound.

Nunchi's concrete Transaction decoder already bounds multisig signature count, checks tagged authorization and signer/curve compatibility, and operation types define their own `Read<Cfg=()>`. Preserve those useful checks; do not claim its decoder is wholly unbounded. [authorization decoder](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/common/src/transaction.rs#L197), [operation trait](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/common/src/transaction.rs#L11), [Transaction decoder](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/common/src/transaction.rs#L303). A strict bounded full-frame ingress bridge or a compatible package adaptation is required before calling the P2P parser reusable unchanged.

## Nunchi P2 — pool tx max and network payload max are not connected

Local gossip calls `gossip.encode()` directly into the configured Commonware Sender. The pool's `max_tx_bytes` is an application-configured limit and not derived from the chosen network's `max_message_size`. Custom PoolTransaction implementations can also report an `encoded_size` inconsistent with their Encode implementation unless the adapter enforces agreement. A locally admitted tx can therefore exceed the transport payload limit and trigger the native channel assertion; admission success does not guarantee publishability. [send call](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L444), [config distinction](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/config.rs#L8).

For a reuse candidate, ensure the **actual encoded gossip frame** fits selected transport limits and preserves identity/size alignment. This does not choose numbers or require a second P2P stack. Selection `pending(limit)` limits **transaction count**, not block bytes, and returns clones without removal; the selected BlockBuilder must still pack/check complete body size. [non-destructive selection](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L160).

## Nunchi P3 — dropped canonical updates do not generally self-heal on the next report

`MempoolHandle::finalized` uses `try_send` and drops a canonical update on mailbox failure, without returning an admission receipt or retry handle. Its comment says a dropped report self-heals on the next one. The chain's actual caller sends only digests and nonce lanes touched by that block. Pool finalize advances only lanes present in the delivered update. [drop behavior](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L190), [pool finalize](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L211), [chain touched lanes](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/chain/src/application.rs#L903).

A minimal source-derived counterexample is:

1. Pool has lane A's transaction nonce 0 ready and committed nonce snapshot 0.
2. Canonical block h includes it, advancing canonical lane A nonce to 1, but its pool `Finalized` message is dropped.
3. Block h+1 includes only lane B transactions. Its delivered update contains no lane A entry.
4. Pool's lane A snapshot remains 0 and pending still returns A's finalized tx. The next report did not heal A.

This is analytical source reasoning, not an executed trace. A later block touching A can update it, and TTL may eventually drop old pending bytes, but neither guarantees the next-report claim. TTL removal does not itself repair the lane's committed nonce, so a replay can be re-admitted under a stale snapshot. Pool status is bounded in-memory history and does not substitute for canonical nonce initialization. [default unknown nonce](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L304), [TTL and retained state](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L267), [status](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/status.rs#L10).

Baton must preserve its existing outcome/committed-state handoff contract if choosing this backend: explicitly evaluate reliable/replayable canonical updates or complete snapshot refresh and restart nonce initialization. Do not describe the unchanged fire-and-forget handle as that contract, and do not make native cut wait on pool delivery. The exact adapter choice remains open. Nunchi's finite TTL/default values are not adopted.

## Additional resource/lifecycle precision

Per-tx/global/per-lane pool counts and status-cache counts are real existing limits. They do not bound one `submit_many(Vec<T>)` message's aggregate input, concurrent pre-actor verification, the total pending bytes represented by an oversized configured pool, or the committed-nonce HashMap accumulated through finalization. RPC batch admission has no aggregate vector cap in the inspected handle. It verifies the entire supplied vector and allocates result/verified vectors before enqueuing one message. [batch handling](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L94). Treat these as integration/admission scope rather than build another parallel pool.

`pending` is non-destructive and can be reused repeatedly across simultaneous producer proposals; that matches a concrete reselection requirement better than destructive dequeue. It does not reserve nonce transactions across speculative branches or reason from Multimmit producer-parent state. Canonical ledger execution still decides outcomes. Only native canonical exact-order state may refresh the pool nonce snapshot.

## Documentation recommendation

Add Nunchi to the comparison beside Constantinople and Tempo/Reth as a real generic tx pool **candidate** with direct Commonware `start_p2p`, non-destructive `pending`, and committed-nonce cleanup. Include compact qualification that it brings nonce/replacement/SHA-256 and Nunchi deps, raw `Read<Cfg=()>` ingress/full-frame checks, best-effort one-shot local broadcast, count-based selection and lossy canonical update semantics. Those are evidence-backed compatibility points, not reasons to ignore useful existing pool code.

No generic buffering/fetch engine needs to be invented merely because the candidate has one-shot dissemination. If future requirements actually need tx fetch/retry, separately assess existing Commonware buffer/resolver adapters under the selected tx identity/lifecycle policy; no inventory/fetch format is selected here.
