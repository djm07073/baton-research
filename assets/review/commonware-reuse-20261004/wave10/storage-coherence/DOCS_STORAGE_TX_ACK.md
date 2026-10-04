# Independent final Storage / Tx reader ACK

Reviewer `/root/reuse_storage_types_v3`. **Pass** for all four changed reader pages, bound exact SHA-256:

- `docs/e2e/normal.md`: `da22c9d489975d03e96ca58ac9ede56c97e1391041182d7f8f67c4cfc2bf4e8c`
- `docs/e2e/canonical.md`: `fc5ca24ed8010cd3aa9f873ead571a85da423b39132e53de3f827fb738f351e0`
- `docs/overview/architecture.md`: `e21a290167bcf338ed6649fe444f7c84e9a450c0c9a1c68795739677a309531a`
- `docs/tx/interfaces.md`: `0bd4a0297aefacdb7b4df9d62f4f14e0f78e656883b10cdc511a5d4baf8c0049`

Compared final bytes with canonical baseline01cf73b41dedd81614237977e4edf150c7d19a81. Exactly three introductory ownership sentences and one Nunchi antecedent changed. All code fences, table rows and source URLs on these pages are unchanged. Generated Rust export and all 18 existing diagram source/SVG pairs remain byte-identical. Existing three-page ownership review remains valid; this extends final global reader coverage to the Tx paragraph.

- Executor computes/reuses completed changes and controls logical canonical promotion/certification/normal-path peer sync. Storage computes selected roots and owns physical canonical apply/persistence/recovery. Delivery ACK is explicitly Executor's after complete recoverable state/output/cursor/provenance, with no Baton approval or peer-result cut barrier.
- “For a Nunchi source adaptation” correctly identifies the following private-kernel/Message/oneshot/finalize/nonce-hydration/TTL discussion. It does not select Nunchi, change lifecycle guarantees, turn lossy finalized into processed completion, or apply Nunchi's source modifications to Reth.
- Rootless effects replay/branch access stays conditional, shared writer/fencing and retention remain required, and Application/full Stateful/custom generic storage/body/pool engines remain unnecessary. Exact full execution subjects, direct/imported provenance and certificate-plus-applicable-material-before-stop are intact.
- Five proposed traits, open backend/schema/codec/root/boundary/runtime/sealing/sync policies, n=5f+1/native pin, body/custody adaptation and unimplemented native integration obligations remain unchanged. The prose changes introduce no new upstream API or source capability.

Related independent body/pool/root source fit is recorded in BODY_POOL_CROSS_REVIEW.md with fresh minimal primary/tree/blob receipts. This reader ACK is documentation coherence only: no implementation, tests/build, rendered visual QA, protocol proof or six-hour completion claim.
