# Independent reader review: ordering evidence, recovery and architecture

Reviewer: `/root/reuse_storage_types_v3`. Baseline `8b61492bbebdbf34dbc10e5d43c3117e19618377`. Scope is the current four-page draft and its wave6 diff, with inherited API paragraphs considered against the corresponding prior wave reviews; it is not a new audit of every unchanged historical citation.

**Pass; no blocking correction required.** The new source-grounded paragraphs and six-row table preserve existing user architecture, exact-source recovery limits and Commonware reuse boundaries. No canonical edit or implementation was made.

| Reviewed page | SHA-256 |
|---|---|
| `docs/consensus/ordered-input.md` | `f760f5b05aae5f3000babdcf1e63a0d988bc72b454169b4434aec315544942d9` |
| `docs/e2e/recovery.md` | `b721fa48c1dfde23c18b8c2724b8bd238ad0af6391e510dd3ba9b0439d89f2a4` |
| `docs/reference/integration.md` | `0cfcc294617e815554166765ec92615a1ad69cdcbaee87c8e4eb4941048bf7ad` |
| `docs/overview/architecture.md` | `1e9a61fc4830cef9ff5e70710416bfd9cc7c5411411e8548d443ba0bbbee41db` |

`reader-page-receipt.json` records snapshots/hashes, all six new primary-source anchor locations and source text. All six are covered by my independently freshly fetched native files and freshly authenticated complete pinned Git trees; zero source/tree blob mismatches. The original unauthenticated rate-limit/fallback receipts remain preserved and the later successful five-tree retrieval is recorded in `authenticated-tree-receipts.json`.

## Findings

- **ordered-input:** Native DurableState actually includes selected local/outbox/forwarded/floor material, so the paragraph correctly reuses retained proofs rather than claiming evidence is wholly absent. The empty ordering snapshot and silent replay support the precise missing history claim. Existing safety store does not persist every authenticated remote vote/source-selection revision or exact external range delivery. `serve(view)` may return a matching retained/covering proof, with no guarantee of exact original source identity. Recoverable exact source/opening retention remains a narrow owner/application bridge, with placement and retention explicitly open.
- **recovery:** Fresh `engine.rs` compaction stores a covering native checkpoint then rolls/prunes sections; fresh `reducer.rs` view retirement removes local/forwarded/exit references under native floor. Neither consults Executor's applied receipt. The new paragraph correctly preserves exported witness/interpretation through a selected recoverable handoff and does not assume native recovery redelivers external history. Existing no-extra-cut-quorum, distinct progress coordinates, lost-ACK idempotence and state/output/cursor/provenance conditions remain intact.
- **integration:** The amended Orderer paragraph removes the implication that a public visibility-only handoff already covers durability. It reuses native verifier/body opening/typed codecs/archive/resolver/journal/Metadata, identifies the missing durable exact-source transition, and retains private extraction and application policy/order bindings. It does not add another general ProofArchive/HistoryResolver engine, select archive schema/retention or claim cross-store transactionality. Native preservation/adoption/availability/liveness obligations remain unresolved rather than being closed by editorial changes.
- **architecture:** Six logical roles map reused infrastructure to new semantics. Logical BlockService still uses upstream callbacks and does not become a sixth public trait. Storage uses QMDB and fitting glue storage wrappers without requiring full Stateful Application; Executor keeps tree/result/sync control and Baton stays outside finalization/apply. “Where selected/fits”, optional Strategy and pool choice preserve open decisions. The color explanation expressly avoids mandating an actor/server/engine per role.

The Rust declaration blocks remain byte-identical to the baseline, retain exactly TxPool/Orderer/Baton/Executor/Storage, and the generated Rust export is byte-identical. These four-page changes make no policy/backend/codec/threshold selection and introduce no public method. This is source-based reader review, not compilation, live protocol/recovery validation, a completed exact-source export, native liveness proof or approval for application writer switching.
