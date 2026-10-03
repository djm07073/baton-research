# Reuse cross-review: block and storage first-wave reports

Reviewed: `block-wave1/REPORT.md`, `storage-wave1/REPORT.md`, current `docs/tx/README.md`, current `docs/overview/rust-interfaces.md` and the storage interface sketch. Source verification used fresh GitHub fetches at the native pin and explicit release tag; no compilation, protocol execution or central document changes occurred. The findings refer to the central pages as read during this turn; the root agent may be updating them concurrently.

## Assessment

Both first-wave reports correctly distinguish **real-chain composition** from **Native Multimmit-compatible attachment APIs**. Their major positive reuse conclusions are supported: generic buffered broadcast, generic resolver and archive services can be reused without importing Simplex Marshal; QMDB supports delayed Merkleization within a batch and sealed speculative parent trees. Neither report establishes a rootless QMDB parent fork or a buildable unchanged pool/storage/body stack for Baton.

The reports are suitable review inputs with the qualifications below. The most important edits are to the central documentation: state the storage preparation/signing handoff, make Constantinople’s actual lifecycle/type mismatches visible, and preserve the boundary between native retry authority and application custody.

## Independently confirmed source boundaries

| Boundary | Fresh source check | Result |
|---|---|---|
| Marshal is not a generic consensus adapter | Native `consensus/src/marshal/mod.rs` lines 61–66 | Explicitly Simplex-only, at most one notarization per view |
| Deferred is not a drop-in durable Multimmit body service | Native `marshal/standard/deferred.rs` lines 471–500 | Uses Simplex Context; staged digest precedes durability; certification waits on its gate |
| Marshal resolver’s handler is not an external consumer loop | Native `marshal/resolver/handler.rs` lines 128–132 | `recv` and `try_recv` are `pub(crate)` |
| Ordinary archive put is not sufficient custody evidence | Native immutable lines 6–25; prunable lines 32–40, 97–100 | Occupied-index no-op; same key can name multiple entries; prunable floor can satisfy put without storing; sync metadata determines recoverable content |
| Native recovery invokes application custody verification | Native `multimmit/engine.rs` lines 265–303 | Recovered requirements call `Automaton::verify(Context, commitment)`; only `Ok(true)` succeeds |
| Both QMDB versions require sealed pending parents | Native db mod lines 548–551; release lines 567–570; Any Base::Child in both | `fork_batches(&Merkleized)`; Child stores `Arc<MerkleizedBatch>` |
| Single-batch root deferral exists | Native Any batch lines 1303–1308, 1706–1737 | Mutable last-write-wins pending mutations and read-your-writes; separate Merkleization |
| Storage lifecycle APIs differ | Native db mod lines 386–397, 559–567; release lines 390–408, 578–591 | Native finalize consumes a sealed batch and starts flush; release splits apply and finalize |
| A returned durability handle may coexist with later apply | Release db mod lines 402–407, 587–590 | Later dirty suffix needs another finalize; observe prior barrier before finalizing again |
| QMDB sync does not authenticate the chosen target | Release sync engine lines 97–135 | Config receives caller-trusted target; target updates must strictly advance |
| Collector count is not validated execution-signature count | Native collector engine response branch lines 207–230; release collector traits | First decoded requested-peer response consumes its slot before Monitor; no execution subject/signature verification in the engine |

Primary source links: [Marshal limitation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/mod.rs#L61-L66), [Deferred types/timing](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/standard/deferred.rs#L471-L500), [handler visibility](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/resolver/handler.rs#L118-L133), [immutable custody](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/archive/immutable/mod.rs#L6-L25), [prunable no-op](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/archive/prunable/mod.rs#L97-L100), [recovery verification](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/engine.rs#L265-L303), [native forks/finalize](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L548-L567), [release forks/apply/finalize](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/mod.rs#L567-L596), [Any sealed child](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L2584-L2611), [sync trusted target](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/sync/engine.rs#L97-L135), [collector response admission](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/collector/src/p2p/engine.rs#L207-L230).

## Findings for current documentation

### 1. Clarify Executor orchestration versus Storage root/apply ownership

Current `rust-interfaces.md` lines 219, 246–257 and 295 still say Executor applies/persists state and supplies the durable canonical writer directly. This reflects the earlier combined Executor/storage narrative. Under the latest Storage ownership correction, use “Executor orchestrates Storage preparation, canonical apply and durable completion”; Storage owns QMDB root computation and physical persistence.

The adopted public trait count need not change just to explain this internal delegation. The optional storage sketch is a design facade, not an instruction to add a sixth public trait or independent actor.

The current `sign_result(Self::ExecutionResult)` method and execution description do not explain whether ExecutionResult is unsealed effects or prepared root-bound result material. If execution now returns unmerkleized work, say exactly where Storage prepares the chosen boundary before the complete signing statement is formed. Either sign_result orchestrates that preparation internally or consumes an explicitly prepared result representation; do not leave the root computation after signatures or assume a root already accompanies every speculative execution. Associated-type naming alone does not settle this flow.

### 2. Whole Constantinople pool reuse is more than a Context conversion

Current `tx/README.md` lines 9–11 accurately mention Header/round/Update and dependency mismatches, but omit three decisive fit checks:

- Pool selection physically pops whole batches and removes queue byte accounting, so an unchanged backend does not meet the current `TxPool::select` retention promise merely because it remembers pending digest statuses.
- Public `Mailbox::try_submit` waits for terminal status; the existing admission-result `try_ingest` is private to the webserver module. An adapter needs an actual admission hook or source adaptation.
- The fixed VerifiedTransaction is a sender/recipient/value/nonce transfer type. Whole-crate reuse imports that chain representation and its surrounding execution/outcome assumptions. It supplies HTTP/relayer ingress, not a ready-made generic Commonware authenticated tx gossip protocol.

These are concrete blockers to advertising a drop-in library pool. They do not negate the value of reusing its actual queue/dedup/byte-packing kernel. See [selection pop](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L402-L457), [public terminal versus private admission API](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/mailbox.rs#L115-L166), [fixed transaction type](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/primitives/src/transaction.rs#L134-L164).

The blank pool, duplicate, lifecycle, routing and packing cells should stay blank. For a generic workload, pool-kernel adaptation is the preference to investigate; whole Reth pool/network/builder is an EVM-specific alternative, with explicit account/fee/provider/transaction bounds and dependency cost. No report has compiled either candidate against the native pin.

### 3. Name the actual services that reduce custom work

Current `tx/README.md` supplies a primitive list, but does not identify buffer and resolver assembly. State that Commonware services can replace duplicate payload caches, keyed peer fetching/retry, authenticated transport and mailbox/task ownership. Preserve the remaining new-tx identity discovery/announcement and pool admission bridge.

Do not translate buffered caching into canonical transaction duplicate suppression. Mailbox get/subscribe require known digests; the buffer does not hand unknown txs to a pool automatically. Its cache eviction is unrelated to canonical cleanup or durable admission. The block report already draws this distinction for body lookup, and the pool report supplies the transaction-specific caveat.

### 4. Keep native retry authority and application body obligations distinct

The current body page correctly labels on_retire as proposed and separates archive release. Preserve that wording when simplifying the facade.

Native Egress retries the native publication bytes until typed durable semantic supersession and invokes Relay before each relevant attempt. Only `Feedback::Closed` defers native transmit. This supports repeated application broadcast scheduling, but it does not prove remote body receipt, automatic durability, or expose a public retire callback. Do not invent a second generic retries-until-retire engine in BlockService; use native repeated Relay requests and existing buffer/resolver machinery, with explicit unresolved attachment retention/custody handoff. [native retry contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/egress.rs#L1-L6), [Relay before transmit](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/actor.rs#L2254-L2296).

## Root deferral and minimal interfaces

The storage report’s three paths are correct and should remain separate. An upstream unsealed batch permits deferred hashing **within that attempt**. An upstream pending-parent tree requires sealed checkpoints. A rootless chain across completed blocks needs retained per-prefix effects, outputs, valid fallback reads and deterministic materialization. A single mutable last-write-wins batch is not a reusable immutable execution-parent node: after ABC, it may no longer contain the intermediate AB values required to commit AB. The report already warns about this and should not be compressed into “QMDB supports rootless trees.”

The Storage sketch’s begin_applied/begin_sealed_child methods wrap upstream new_batches/fork_batches. They are justified only by application binding/writer-fence checks; they should not be described as new branch algorithms. Prepare is justified by exact-range commitment assembly and concrete tuple/staged dispatch. Apply/durable are justified by canonical permits and recoverable output/cursor/provenance linkage beyond the upstream barrier. These can remain internal helpers if no public Storage trait decision exists.

Likewise BlockService fetch is a custody-completion facade over Resolver, not an unnecessary duplicate of Resolver::fetch: upstream fetch returns local scheduling Feedback and delivers through Consumer, while BlockService returns an exact retained body. Publish is only local scheduling over Broadcaster; commitment delegates body Digestible/Codec policy. The facade is useful if these success boundaries are documented, without pretending to be upstream.

## Practical next verification

Source compatibility is established at the **named primitive API** level only. Before any future buildability claim, independently assemble the selected dependency graph and exercise admission, cancellation, body custody, native startup verification, prefix materialization and durable canonical outcome paths. This cross-review does not authorize or perform that implementation. The current documentation can still give a concrete assembly path now, with each application adapter named and unresolved choices left open.

