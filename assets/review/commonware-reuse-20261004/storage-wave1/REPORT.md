# Execution and storage reuse: first source review

This review follows the latest conversation boundary: Executor computes transaction effects and orchestrates certification and normal-path state sync; Storage computes/manages commitments and applies/persists state. Baton selects direction. It does not adopt `commonware_glue::stateful::Application`, change dependencies, implement a protocol, or choose the open root/batch/signing policies.

## Main finding

QMDB already supports execution before Merkleization. A caller can accumulate writes in `UnmerkleizedBatch`, read them through `get`/`get_many`, or retain a staged read set and compute final values in its own execution overlay. Hashing is a separate call. Therefore root calculation need not occur after every transaction or every abandoned execution attempt.

The existing QMDB pending-parent tree is a **Merkleized-parent tree**. Both reviewed versions expose `DatabaseSet::fork_batches(&Merkleized)`; Any's internal `Base::Child` contains an `Arc<MerkleizedBatch>`. Neither reviewed API supplies an unsealed-parent fork. Root-deferred execution across several blocks is possible in an application overlay, but the resulting tree and its materialization into QMDB need a custom adapter. This is an integration gap, not a general impossibility of speculative execution.

## Evidence and version boundaries

MCP queries explicitly requested `v2026.9.0`. JSON receipts `00` through `24` preserve returned source; accompanying `.txt` files preserve readable line-numbered extracts. `query-index.json`, the recorded action manifests, and `native-pin-comparison.json` identify the requests. Native pin raw source snapshots and diffs compare the existing pin `534af0ede48affd35b2111522527547b4cc9bf72` with the indexed release.

The database lifecycle changed between these sources. Do not cite a native-pin URL for the release-only split API.

| Stage | Existing native pin: reusable without dependency migration | Indexed v2026.9.0: separate API recipe, requires compatibility decision |
|---|---|---|
| Applied-state batch | `dbs.new_batches().await` | Same call |
| Pending-parent batch | `D::fork_batches(&parent_merkleized)` | Same call; unsealed parent is unsupported |
| Compute effects | Concrete unmerkleized `get`/`get_many`/`write`, or `stage`/`expand` with retained indexed writes | Same API family; exact implementation differs |
| Calculate commitment | Concrete `Unmerkleized::merkleize()` or staged `merkleize(updates, upserts)` | Same family; per-database tuple needs explicit adapter dispatch |
| Apply and start durability at DatabaseSet level | `let barrier = dbs.finalize(merkleized).await;` | `dbs.apply(merkleized).await; let barrier = dbs.finalize().await;` |
| Underlying ManagedDb recipe | `finalize(self, merkleized) -> Result<(Self, Handle<()>), Error>` | `apply(self, merkleized) -> Result<Self, Error>`, then `finalize(self) -> Result<(Self, Handle<()>), Error>` |
| Observe durability | `barrier.durable().await` | Same call |
| Later canonical batches | Native finalize starts a flush for each supplied batch; preserve/observe required handles | Several applies may precede one finalize; later applies may proceed while its returned barrier is pending, but require a later barrier |
| Prune | Target must already be durable; later barriers may remain pending and pruning must coordinate with them | Active barrier must resolve before prune; apply/finalize/prune/rewind method bodies must not overlap |
| Recover | `committed_targets`, `rewind_to_targets`; target alone does not establish durable completion | Same family; independently rewindable apply checkpoint is explicit in this release |

The release's non-overlap rule concerns database mutation calls, not a prohibition on applying a later batch while an already returned flush handle remains pending. Neither recipe proves crash-atomic application state, outputs, cursor, and provenance across several databases.

Sources: [native DatabaseSet/ManagedDb](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L344), [release DatabaseSet/ManagedDb](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/mod.rs#L344). The collector trait file is identical after ignoring a final blank line; Any batch and database lifecycle are materially different.

Receipts `06`, `11`, and `12` are **invalid source fetches**: nonexistent guessed paths silently returned Commonware homepage HTML inside a Rust code fence with no MCP error. Do not cite them. Directory-list receipts `10`, `16`, `17` led to valid paths `15`, `20`–`24`. Transport success is not source verification.

## What staged and overlay paths actually provide

Any `UnmerkleizedBatch::write` accumulates last-write-wins mutations. Its `get` and `get_many` search local pending mutations, retained ancestor diffs, then applied DB state. This is usable read-your-writes for a single unsealed batch. A caller can delay its `merkleize` call while continuing to compute against that batch.

`stage(keys)` additionally retains resolved operation locations to avoid re-probing and re-reading those keys during Merkleization. `expand(keys)` appends stable staged indices. It does not deduplicate repeated keys and does not make caller-computed staged values visible to future staged reads. Those values are supplied only at `merkleize(updates, upserts)`. An application overlay must supply read-your-writes when using staged execution. Upserts are applied after indexed writes, and overlapping upserts win. This order is a real contract to preserve when preparing a batch.

Sources: [Any structures and branch validity](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/any/batch.rs#L254), [staged expansion](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/any/batch.rs#L1318), [unmerkleized reads and stage](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/any/batch.rs#L1743), [glue Any wrappers](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/any.rs#L50).

Three integration shapes should remain distinct:

1. **Single-attempt deferral:** execute several transactions in one upstream unsealed batch; hash only when a storage commitment is needed. This uses existing primitives directly.
2. **Sealed branch checkpoints:** hash a selected completed execution checkpoint, then use upstream child batches. This gives the existing QMDB tree and ancestry validation; no claim that every speculative block must always be sealed.
3. **Rootless pending-parent overlay:** Executor retains immutable completed effect nodes and a working overlay; Storage reads through that chain to a valid sealed/applied base and later materializes the selected prefix. QMDB remains the indexing, operation-log, proof, Merkle and persistence engine. Rootless tree ownership, reads, exact-prefix extraction and materialization are application adapter responsibilities absent from these reviewed fork APIs.

Deferral and batch coalescing are different. QMDB roots commit to operation history, sizes, commit operations and relevant floors/metadata. Coalescing repeated writes can change the operation log/root even if the final logical key/value map matches. A batch for ABC without an AB boundary cannot be applied wholesale to commit only AB. A rootless overlay can retain AB effects without having hashed AB, then prepare AB later; the adapter must preserve exact execution context and use the chosen deterministic materialization rule. It must not promise automatic reuse of an old sealed ABC descendant after introducing a different AB storage ancestry.

Storage keeps the QMDB `Commitment { size, root }`, `Bounds { base, db, tip, ancestors, inactivity_floor }` distinction. Applicability compares current operation size and root with the recorded DB boundary or a recorded ancestor, and checks commit floors. Equal application state alone is insufficient. [Batch-chain validation](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/batch_chain.rs#L29).

An overlay fallback reader must obey the same live-database access boundary: upstream branch-scoped reads are not immutable historical snapshots. Once canonical apply advances along an incompatible branch, stop/rebase affected fallback reads under the writer fence. Checking a worker generation only when admitting its final result is too late to make its intermediate live-state reads valid. An immutable materialized read snapshot could avoid this particular coupling, but no such arbitrary historical QMDB snapshot API was established here.

## Responsibility split and signing order

| Executor | Storage |
|---|---|
| Validate exact execution input, runtime, execution-parent linkage and completed work; execute transactions and emit effects plus outputs | Provide valid branch read/write or staged handles; manage storage base identities, ancestor retention and applicability |
| Own execution scheduling, logical branch promotion/pruning and stale result adoption fencing | Own QMDB Merkleization/root calculation, deterministic storage preparation, physical retention and database access fencing |
| Verify irrevocable exact order, choose direct or certified-import route, and orchestrate commit | Serialize canonical mutations; apply selected material; observe flushes; recover state/material/checkpoint metadata |
| Sign directly executed/validated results, collect f+1 matching eligible signatures, verify certificates, retain direct/imported provenance | Supply the computed result commitment and material-validation result; never create an execution signature or substitute a root check for a certificate |
| Own Executor↔Executor result/sync control and decide safe switching | Verify operations/proofs against the authorized target and supply usable state; enforce canonical writer/durability contract |
| Return durable ACK to Orderer and canonical outcomes to TxPool once Storage proves recoverable linkage | Produce recoverable state/output/cursor/provenance completion; readable state is earlier than durable completion |

The signing path is: complete direct execution → Storage prepares the exact selected signing range and computes its result root/commitment → Executor builds and verifies the full statement → sign → collect f+1 matching statements. Root calculation cannot be postponed until after signatures/certificate formation, because that would leave the signed result unspecified or change the signed subject later. This does not require hashing every abandoned speculative attempt. Root type, root vector/combination, statement boundary and normalization remain undecided.

Direct canonical application may progress independently of peer collection after exact order and base checks; the primary certification endpoint still needs the full f+1 certificate. Imported application additionally needs that verified certificate and applicable material before stopping unfinished local execution. A certificate alone does not authorize stopping. Storage cannot relabel imported work as direct execution. Baton is outside these certification/apply gates.

## Draft interface shape

`storage-contract.rs.txt` is an English-commented design sketch, not protocol implementation or a compiled API. It keeps upstream `DatabaseSet` associated types at the sealed/unsealed boundary and explicitly distinguishes the optional rootless draft adapter. `Executor::execute` returns completed unsealed work; `Storage::prepare` produces the root and sealed material. `Executor::commit` orchestrates the exact finalized range through Storage. An optional Storage facade does not imply adopting another independent actor or choosing a public trait count.

The binding record needs epoch/validator-set identity, exact canonical history and frontier, exact input/range commitment, application/runtime identity, canonical input commitment(s), execution-parent identity, selected storage boundary/encoding rule, and worker generation. Pending overlay nodes additionally need ordered effects, per-prefix outputs, completed-parent links, a valid sealed/applied fallback base, and retention ownership. These are proposed adapter fields; wire codec/hash choices remain open.

## State sync reuse and limitations

`qmdb::sync::Source` serves operation batches/proofs or a boundary operation with authenticated pinned nodes. `Target<F,D>` is an **ops root plus operation range**, not an execution certificate. The sync engine checks untrusted data against a caller-trusted target, reconstructs state, verifies rebuilt root, and then persists provisional state. It does not select/authenticate native order, runtime, f+1 signatures, or canonical input ancestry. The `finish_rx` and target-update channels can support a live sync session, but strictly advancing same-log targets are required; they are not a generic fork switch.

`glue::stateful::db::p2p::{Actor, Mailbox}` already adapts `Source` to `resolver::p2p`: deduplicated network fetch, serve attached DB operations, feedback and cancellation. Reuse this transport/proof machinery where source-version compatibility is satisfied. `StateSyncDb::sync_db` returns an initialized DB, and `StateSyncSet` coordinates one-time sync with block anchors. Neither is an in-place, repeated certified-delta switch for an active Baton Executor. Fencing/swap, exact base/material validation and normal-path orchestration remain custom.

Current's sync target compares `ops_root` and range; its canonical `root()` is distinct. If Current is selected, Storage and Executor must verify the chosen canonical result commitment in addition to replay sync targets. No variant is selected here.

Sources: [sync target](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/sync/target.rs#L9), [sync engine target contract](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/sync/engine.rs#L97), [sync rebuild contract](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/storage/src/qmdb/sync/database.rs#L47), [P2P resolver](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/p2p/mod.rs), [Current matches target](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/current.rs#L544).

## Collector reuse

Use `collector::p2p::Engine` for requested execution attestations, with `Handler` checking requested full subject before signing and `Monitor` maintaining its own validated-subject map. The engine groups by response commitment, counts requested peer identities once, and invokes Monitor. It does not verify execution signatures, full subject equality or epoch eligibility. Its raw count must never become the f+1 certificate threshold. Counts may include invalid or disagreeing responses.

The first decoded response consumes a peer's seen slot before Monitor validation. A corrected second response is ignored until cancellation/reissue. Requests remain tracked until explicitly canceled. Unsolicited push statements for untracked commitments or unrequested peers are ignored, so direct Executor P2P is still required for push signatures/certificates unless they are routed through an existing request. Request commitment and response commitment must identify the same requested complete result; if an outer nonce/request ID is used, it must map unambiguously to that subject and remain outside the result equality rule. Response signature bytes must not cause each signer to have a different collection commitment.

Sources: [Collector traits](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/collector/src/lib.rs#L20), [engine admission](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/collector/src/p2p/engine.rs#L207). These are primitive-source observations, not an executed Baton collector integration.

## Actual chain evidence

Chain heads were read once and saved in `chain-heads.json`; all source files were fetched by those exact commits. These example chains are evidence for practical primitive assembly, not Baton protocol validation.

**Constantinople**, `3b6c92e76bf582855615844a4175b8304808f6a9`, is the strongest concrete QMDB execution/storage example in this review. It uses an Any fixed account-state DB and a compact keyless transaction-history DB as a DatabaseSet tuple. Its executor maintains working account state, emits staged-index final values, and its consensus DB helper Merkleizes state and history concurrently after computation. Incremental proposal rounds use `stage` then `expand`, preserving an application working overlay until final preparation. This is a real example of separating computation from QMDB hashing. Its account rules and `stateful::Application` use are application choices, not Baton requirements, and it still returns Merkleized work at its consensus-facing block boundary. [DB aliases and preparation](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/application/src/consensus/db.rs#L29), [incremental executor](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/application/src/executor.rs#L396), [execution flow](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/application/src/consensus/execution.rs#L374).

**Alto**, `1d87569348b5560699465a72d691d90f18affb9c`, implements a minimal Commonware consensus application that checks block timestamp/size and proposes random load payloads. The inspected chain Application has no account execution/QMDB branch backend. Alto is useful as a consensus callback/ACK/backfill example; do not describe it as proving the QMDB execution/storage split. [Alto application](https://github.com/commonwarexyz/alto/blob/1d87569348b5560699465a72d691d90f18affb9c/chain/src/application.rs#L51).

**Tempo**, `61c979a524f9af5de9c540a0088c429a44741e4c`, uses Reth execution/provider state. Its inspected parent-state helper reads noncanonical executed parents via `ExecutedState` and a Reth state provider. This supports a separation between consensus and a fork-aware execution backend, but it supplies no QMDB rootless-fork evidence. [Tempo parent state](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/consensus/application/parent_state.rs#L16).

## Open matters retained

No decision was made on Any versus Current or other variants, logical result root versus operation roots, root combination, canonical mutation encoding, coalesced boundaries, per-block versus range signing, overlay persistence, checkpoint granularity, or the canonical state/output/cursor/provenance commit record. Adoption must account for operation-history determinism and signing-root readiness before claiming a delayed-root performance benefit. The Native Multimmit cut/prefix bridge remains outside this storage review and unresolved.

Follow-up review should examine whether an immutable effect-overlay can be materialized at a newly selected exact boundary without transaction reexecution, while keeping already sealed compatible descendants reusable; distinguish direct effect reuse from sealed QMDB batch reuse. Recovery and imported material must reconstruct the same binding records, never reverse terminal order or direct/imported provenance, and share one canonical writer.
