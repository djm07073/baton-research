# Review of the current canonical reuse documentation

Research date: 2026-10-04. Independent source review of four canonical pages after the first-wave findings were integrated. No canonical page was edited. This is a documentation/source assessment, not a compatible build, executed protocol trace or completion claim.

## Reviewed byte snapshots

The pages were fully read and their hashes checked again after review; these four hashes remained unchanged during the read window. Findings apply to these bytes. Concurrent later changes require a new comparison.

| Page | Bytes | SHA-256 |
|---|---:|---|
| `docs/tx/README.md` | 10311 | `e057daffe07852faab661ab9081ca23f355d61a7206ca4dfe2438c06b0b9baad` |
| `docs/consensus/block-body.md` | 19743 | `77c48a86ca68f83de85572a5fe53d19c04662deef23f43320920e2694f24af21` |
| `docs/reference/integration.md` | 21064 | `a6e5ae6fe29cece60e5324c44e5cf4a5ba73f7238fac52c0ee414e99433a2fd3` |
| `docs/overview/rust-interfaces.md` | 22779 | `9be5eef602cece2310c17c53dbe7bd21a4dc9274c271f8db278e0c0b6ef2aa93` |

Evidence includes the pinned sources retained by `block-wave1/sources/`, `pool-wave1/queries/`, and this directory's first-wave source receipts/native comparisons. Additional source details are recorded in [the pool cross-review](POOL_CROSS_REVIEW.md) and [the block cross-review](BLOCK_CROSS_REVIEW.md).

## Assessment

The reviewed pages satisfy the central reuse goals. They now explain actual Tempo, Alto and Constantinople assemblies, name upstream handles/callbacks, and state which connections remain proposed. They do not imply that a pool, body service or rootless state engine exists merely because a library inventory includes networking/storage crates. No blocking source contradiction was found in the four snapshots.

| Requirement | Result in reviewed snapshots |
|---|---|
| Actual chain recipes beyond crate inventory | Integration lines 5–43 and body lines 11–30 explain construction/startup/ownership and exact version boundaries |
| Whole-pool compatibility and private extraction | Tx lines 9–28 distinguish fixed chain types, private kernel, destructive selection, differing dependency pin and conditional EVM reuse |
| Minimal BlockService | Body lines 5–9 and Rust interfaces lines 77–110 implement existing callbacks directly; no additional `pub trait BlockService` |
| No duplicate generic engines | Body lines 26, 81–103 reuse buffer/resolver/archive; tx lines 36–38 retain only the missing inventory/admission bridge |
| Latest execution/storage ownership | Interfaces lines 213–346 and integration line 33 place changes/selection/certification/peer orchestration in Executor, root/apply/durability in Storage |
| Root deferral with honest limits | Interfaces lines 288–340 distinguish upstream unmerkleized batches and optional effects/read adapter; sealed-parent `fork_batches` remains explicit |
| Open static/router/Bank policies | Tx decision cells remain empty and payload-only analysis remains explicit; integration line 98 prescribes no Bank module |

## Source-backed strengths

**Chain composition is concrete.** Tempo's pinned engine constructs the buffered Engine, starts its body channel, initializes Marshal's backfill bridge and starts a separate Executor. Alto constructs the same full-block buffer with codec limits and immutable finalized archives. The docs reuse the generic components while explicitly rejecting unchanged Marshal/Simplex adaptation to native Multimmit. That distinction agrees with the public generic resolver versus crate-private Marshal receiver boundary. [Tempo construction](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/consensus/engine.rs#L207), [Tempo startup](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/consensus/engine.rs#L526), [Alto construction](https://github.com/commonwarexyz/alto/blob/1d87569348b5560699465a72d691d90f18affb9c/chain/src/engine.rs#L177), [native private receiver methods](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/resolver/handler.rs#L118).

**Custody is an application connection over ready storage primitives.** Body lines 91–103 cover occupied-index/below-floor no-op puts, exact retained presence, multi-lane index collisions, covering sync, consumed-handle ownership, subscriber cancellation, peer-key validity versus stale local context, latest-primary outbound fetch restrictions and retention/serving obligations. These correct the main risks of presenting archives/resolver as an automatically complete BlockService. Relay feedback remains local, Reporter observation is opportunistic, and exact durable witness export remains Orderer's separate integration.

**Pool reuse does not silently import chain semantics.** The whole Constantinople package remains conditional on transaction/context/dependency compatibility; private extraction is explicitly new adaptation. Destructive pop and local outstanding-proposal cleanup do not become Baton canonical retirement. Tempo/Reth is conditional on Ethereum-shaped transaction/provider/network assumptions, with base Reth composition distinguished from Tempo extensions. The non-selected Alto/demo examples are characterized by inspected behavior rather than names. [Constantinople pop](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L420-L434), [Reth transaction bound](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L114-L116).

**Storage ownership and version discipline are explicit.** Root preparation precedes full-result signing; a root is not required for every abandoned speculative attempt. Executor owns logical branch pruning and state-sync orchestration; Storage owns QMDB handles, actual canonical mutation, physical retention and recovery. Direct/imported provenance and full-subject f+1 collection are preserved. `Storage::prepare/apply` are labelled proposed contracts, so their method names do not masquerade as native DatabaseSet calls. Integration separates native pin, indexed release and chain dependency graphs and links the exact native/release recipe instead of mixing their different apply/finalize signatures.

The associated types deliberately leave concrete base, ancestry, material and recovery codecs open. They do not establish upstream ability to slice an arbitrary sealed descendant into an earlier prefix or to fork an unmerkleized parent. The retained `fork_batches` limitation and optional adapter qualification are necessary and correctly present. [Native batch/database contracts](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs).

## Remaining precision improvements

These are useful local clarifications, not blocking changes to the architecture:

1. **Add direct source evidence to the ingress warning.** Tx line 38 correctly says `VerifiedTransaction` cannot replace validation, and integration line 31 requires identity alignment. The warning would be easier to audit with the exact alias/public `new_unchecked` and separate caller digest-vector links. Public mailbox admission bypasses the HTTP verification path; its actor dedups transaction `message_digest()` but uses the supplied vector for status watchers. Keep recomputed/validated identity correspondence explicit without choosing message versus envelope identity. [Alias and unchecked constructor](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/primitives/src/transaction.rs#L41-L74), [separate arguments](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/mailbox.rs#L112-L139), [watcher registration](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L767-L796).
2. **State the backend outcome distinction if naming removal/packing APIs later.** Tx currently recommends canonical maintenance without instructing a wrong API call. Preserve that correctness by stating Reth `remove_transactions` means discarded rather than mined; `BestTransactions::mark_invalid` excludes candidates/dependents from the iterator and is not proof of durable canonical retirement. These details are particularly useful when expanding the whole-stack recipe. [Discarded removal](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L496-L504), [iterator contract](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L1117-L1123).
3. **Keep retained-material capacity in the eventual fit spike.** The tx page already requires retention/cancellation reconciliation. Constantinople's queue-byte cap does not cover popped transaction bodies held elsewhere, outstanding status/digest metadata or a new reservation/custody store. This is an integration-check item, not a reason to fill current limit or storage-policy cells. [Queue budget](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L596-L623).

## Separate coherence follow-up

Root is still updating the general overview and E2E pages. Their coherence is a separate pending sweep, not a failed result of this four-page review. Check that they eventually use the same logical BlockService/direct callback recipe, Executor-to-Storage ownership and root-before-sign ordering, durable Executor-to-Orderer/TxPool completion, and direct/imported provenance. Also ensure generated interface export agrees with canonical Rust blocks and does not incorporate upstream `rust,ignore` excerpts.

No policy decision is implied by these follow-ups. Root representation, deterministic batching/normalization, static-analysis schema/placement, router versus packing filter, pool backend, duplicate application effects, limits, persistence and cancellation remain open. No Bank semantics, per-block signing default or complete state-sync implementation is inferred.
