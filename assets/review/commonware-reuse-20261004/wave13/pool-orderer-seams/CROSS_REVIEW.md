# Wave13 independent execution/body seam cross-review

**Both peer reports pass. The concrete receipt-ownership clarification is adequate; body seams need no reader change.** This is independent semantic/source-fit review, not integration execution or engineering/proof closure.

## Exact reviewed bytes

- `assets/review/commonware-reuse-20261004/wave13/body-seams/REPORT.md` — SHA-256 `8f9183ac887c4b8ed66c112db7648d1c3a0b0e071535cabe73822cec2610a253`.
- `assets/review/commonware-reuse-20261004/wave13/body-seams/READER_DELTA.md` — SHA-256 `725df7a178157005bbfba252c1a7c16b9fe7ddbc418edabad5dd63f708067491`.
- `assets/review/commonware-reuse-20261004/wave13/execution-seams/REPORT.md` — SHA-256 `c4280a6e683e4904dd32b4d04329c13415c7549436f8c9cf07c9a9ce6ce1ea3e`.
- `assets/review/commonware-reuse-20261004/wave13/execution-seams/READER_DELTA.md` — SHA-256 `71977ab39e80ea8dadc87f9f7b733bd486f1c13605bf6ad889b6440385dfb044`.

`cross-review-receipt.json` binds 88 actual current tracked docs, of which 86 equal published baseline `78d5f2eca347b0fc04b7f7d31ff858cc2a69bee4`; root concurrently adopted only the proposed tx lead and overview receipt paragraph. Eleven decisive native files were independently reread and rehashed against this reviewer's retained complete pinned native tree. These retained checks are not fresh wave13 source downloads. No unresolved API uncertainty required a new catalog/refetch.

## Execution ownership: valid narrow delta

Actual TxPool::on_commit, Orderer::acknowledge and optional Baton::on_commit take Self::CommitResult by value. The associated-type table equates their types with Executor/Storage, but its explicit bounds only require Send (Baton has no explicit bound). PreparedResult alone explicitly requires Clone. Type equality does not permit moving the same owned receipt sequentially to multiple consumers. The report correctly avoids diagnosing a compiled/executed generic bug: concrete associated types may already be cloneable, contain shared immutable receipt handles, or be reconstructed from retained exact durable records. No new public Clone bound, actor, receipt schema, layout or generic dispatcher is needed.

The frozen exact delta is adequate:

> `CommitResult` is passed by value: use concrete cloneable receipt handles or recover copies of the same immutable receipt for multiple consumers; type equality and `Send` do not duplicate an owned value.

Existing surrounding contracts still require exact range/result/context validation, recoverable state/output/cursor/provenance linkage before receipt issuance, and matching durable receipt redelivery on recovery. Recovering the same receipt does not permit substituting root equality or different outcomes. Application receipt handles differ from upstream Exact completion tokens: all cloned Exact handles must acknowledge, the token carries no durable receipt, and optional Baton observation remains outside that completion condition.

The native source supports the peer's adapter limits: DatabaseSet::finalize supplies a Barrier, while sync completion reconstructs, verifies and persists the selected DB. Neither creates the application CommitResult or atomically processes multiple consumers. The clarification does not make a lossy Nunchi notification processed completion or add any cut/direction wait.

## Body seams: no omitted owner

Current tx/body/interface/E2E pages maintain selected stable bytes, body commitment, full authenticated native producer header, ArtifactId and execution-parent correspondence separately. Native header identity covers chain context; ArtifactId additionally hashes domain/kind and exact signed artifact encoding. Producer ancestry alone cannot supply the execution predecessor.

Decisive source confirms Activity is idempotent non-authoritative telemetry, dispatch ignores Reporter feedback, and replay clears newly-ready notices. Candidate intake may therefore lose speculative opportunity without defining empty slots, authorizing dense order or gating native verify. Current direct Orderer→Executor delivery has its separate recoverable exact witness/history/policy export and unresolved-slot stopping contract; sparse native finality/serve notices do not automatically implement it.

Buffered arrival wakes subscribers before cache eligibility; resolver delivers matched bytes to Consumer instead of automatically populating that cache. Immutable Archive ignores occupied indices, and sync covers Freezer/Ordinal before its checkpoint. Current exact-content/presence/parent/covering-durability checks are consequently necessary and correctly owned by the existing custody attachment. Cache arrival, fetch response and put success are not independently custody success. Local cancellation does not release native custody/recovery/serving references.

The no-delta body finding is accurate. It does not imply another parent/body/witness/delivery framework, adopt codec/backend/budget policy, or assert implemented private extraction/export.

## Result and scope

No actionable correction to either frozen report/delta remains. The adopted tx lead correctly names TxPool's durable Executor-outcome connection to the existing selected actor and excludes the scheduling Baton module from canonical relay. This is consistent with public Nunchi finalized/Message processing and the existing lossy-notification/completion caveat; it does not select that backend or add a callback.

Engineering choices for concrete receipt representation, pool processing readiness, custody retention and dense owner export stay open outside the documentation-research completion gate. Original assembly/actual-chain explanations, repeated independent review through **01:29:14 UTC**, verified publication and synchronization remain required. This review does not publish or complete the goal early. No canonical modification, implementation, compile/native test, dependency/default choice or additional inventory by this reviewer.
