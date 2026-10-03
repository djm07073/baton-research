# Independent reader/API review of wave4 canonical additions

Reviewed the eight requested current pages at **2026-10-03T21:27:06.244023+00:00**, with exact page hashes below and in [docs-review-receipts.json](docs-review-receipts.json). This applies to that snapshot; root may continue adding lifecycle prose independently. No canonical file was edited by this reviewer.

**The pool/compatibility assembly and certificate additions pass.** No backend/default policy, application trait/signature, native quorum or custody/ACK behavior was adopted or changed. The new reuse paths distinguish public existing APIs from application/source adaptation.

## Resolved precision corrections

1. **docs/tx/interfaces.md, backend mapping `admit` row:** “`try_submit` waits for eventual batch status” sounds like the method blocks. It is a nonblocking `try_send` returning `Option<oneshot::Receiver<TxStatus>>`; the returned receiver resolves eventual status. Use “`try_submit` returns a receiver for eventual batch status.” This also makes clear why awaiting that receiver cannot implement immediate admission. [Exact public method](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/mailbox.rs#L107).
2. **docs/consensus/block-body.md, second paragraph under Select transactions and build a block:** “preserve required dependency order when a filter or capacity exclusion removes a transaction” should explicitly cover omission of predecessors, not just relative order. If nonce k is omitted while k+1 stays selected, ordering the remaining txs correctly does not repair the gap. Add “exclude or re-evaluate dependent successors when a required predecessor is omitted.” The selected policy stays open; source supports the dependency obligation. [Nunchi contiguous selection](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L157), [Reth iterator dependency invalidation](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L1117).

Root applied both corrections, and this reviewer verified the final wording. No remaining actionable correction found. These are narrow clarity fixes, not a new API or backend requirement.

## Source and contract checks

- All five application Rust declaration blocks are **byte-for-byte unchanged from HEAD**, including comments/signatures: TxPool, Orderer, Baton, Executor, Storage. Existing callback excerpts remain distinct from these application declarations. The generated export therefore has no new application source change to carry from this prose-only patch.
- All prior headings and external source URL sets are preserved in each reviewed page. The Tx open-decision table is unchanged, with its decisions blank. New pool-mapping and certificate-recipe fragments point to headings present in the current canonical files. The startup target `startup-prepare-custody-before-native-recovery` and newly added lifecycle target `own-service-lifetimes-and-durable-shutdown` exist; no pending-heading link found in these additions. This review covers pool/compatibility/certificate prose; the lifecycle source/completion audit remains with its assigned independent reviewer.
- Nunchi whole-actor reuse is conditional **source adaptation**, not a selected backend or ready-made native crate import. Fixed SHA-256/unit config, native versus registry package identities, peer ingress bypass of external wrapper hooks and direct/transitive package reconciliation are accurate. These were checked against this review's own fresh sources and prior [independent compatibility cross-review](COMPATIBILITY_CROSS_REVIEW.md).
- Nunchi public submit returns admission; pending clones count-limited nonce-ready runs; public finalized is lossy with no processed ACK/watermark; its Pool module is private. The docs explicitly leave on_commit completion as a defined recoverable handoff or processed boundary with reconciliation. They do not equate lossy send with processing or put a pool ACK on cut/direction/Orderer delivery.
- Static Features/Decision remain payload-derived. Canonical nonce snapshots, actual runtime outcomes and provider state remain maintained/execution inputs. Built-in peer admission does not silently acquire external analyze/classify. Admission routing versus packing filtering remains open.
- Selection is now an ordered candidate sequence where dependencies matter. Packing stays bounded under attachment-owned per-build IDs/bytes and native producer Context. Same-nonce replacement cannot mutate previously retained body bytes. Non-destructive refills do not imply draining new candidates; destructive selection still requires its own lifecycle reconciliation. The corrected text makes predecessor exclusion fully explicit.
- Reth origins, dependency iterator/no_updates, canonical maintenance and graceful local backup are existing APIs. no_updates is qualified as not freezing provider state, backup as not per-admission/crash durability, and Tempo's additional two-dimensional maintenance as conditional whole-extension composition. No EVM/Stateful execution-dependent builder is adopted for rootless body construction.
- Body custody still requires retained exact bytes and covering durability before digest/verdict completion. Cancellation does not roll back native custody or imply canonical retirement. Missing expected bodies stay pending; callback completion and native signing authority are unchanged. Durable Executor outcomes, including applicable certified imports, feed TxPool independently from body publication/native ordering/Reporter observation. TxPool outcomes do not replace the existing Executor→Orderer durable ACK.

## Certificate additions checked separately

Read the native certificate trait file and concrete Ed25519/BLS scheme implementations plus Faults/ordered helpers; independently rehashed six decisive files against the certification audit's source receipts. Subject, Attestation, Scheme, Signers and certificate::Verifier are actual public APIs. Scheme sign/attestation verification/assembly and Verifier certificate verification are correctly named. Scheme requires duplicate-free caller input; assembly does not replace signature validation; signer bitmap construction can panic for invalid/duplicate indices; peer decode needs roster bounds. These are correctly stated as integration requirements.

The result threshold remains **f+1 distinct eligible epoch identities** for the same full authenticated execution statement. Generic built-in N5f1 quorum delegation is n-f and gives 4f+1 at n=5f+1; an unchanged consensus scheme cannot implement this result threshold. The docs explicitly require a result-quorum adapter or lower-level reuse rather than changing native quorum or assuming one primitive verification also validates exact input/base/runtime/provenance. BLS PoP and non-attributable threshold-signature limitations remain conditional; no key/scheme/format is selected. Rootless effects→selected Storage commitment→own direct statement/signature ordering and imported provenance remain intact.

## Snapshot hashes

| Canonical page | SHA-256 |
|---|---|
| docs/execution/README.md | `0827e8c86b8b04788cced1062efea579eb46298aeb2792cdb67ae30294c7c5f2` |
| docs/execution/interfaces.md | `eae0d3a439353ed7d463ae0850e99d0ca3b234b0d92c7a827b64576c6c93b088` |
| docs/overview/rust-interfaces.md | `b93993c06103578bc129bc8b259c462b986a3ad645cbd03e6cbeb55875ecb49a` |
| docs/reference/integration.md | `33db4673933e1a34bb02f1fa28a10f21edf4f1cc47fbeefdd95c59330abc9b27` |
| docs/tx/README.md | `d9ccd7b04fecc5a1a61d7a709e0ef6a05539000113a9f057cd71532ffc4fbe92` |
| docs/tx/interfaces.md | `5de73fea82efdeb9c68396a246a5219fce727f0d541070a8dac77dabac7f31d2` |
| docs/consensus/block-body.md | `099084ff74c6910b4147febf3bcca5435bc9d8e80fe8140ab1d8d7555b64e6a3` |
| docs/e2e/block-body.md | `e2ab8a122245fff340403dc0a3157945b1036986aad43ac05d328d6141ebd04b` |

No protocol build, benchmark, trace or end-to-end compatibility claim follows from this documentation/source review.
