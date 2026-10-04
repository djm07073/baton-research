# Wave 10 — independent final reader acknowledgement

**Pass: the three root-authored lead changes preserve the adopted roles and introduce no source/API claim.** Reviewed current bytes against baseline `01cf73b41dedd81614237977e4edf150c7d19a81` and the unchanged central Rust interfaces, body assembly prose and corresponding sequences.

| Current page | SHA-256 |
|---|---|
| `docs/e2e/normal.md` | `da22c9d489975d03e96ca58ac9ede56c97e1391041182d7f8f67c4cfc2bf4e8c` |
| `docs/e2e/canonical.md` | `fc5ca24ed8010cd3aa9f873ead571a85da423b39132e53de3f827fb738f351e0` |
| `docs/overview/architecture.md` | `e21a290167bcf338ed6649fe444f7c84e9a450c0c9a1c68795739677a309531a` |

Architecture now states Executor computes changes and Storage prepares roots/durably applies canonical state; the detailed role table and diagram already carry those responsibilities. Normal E2E likewise names existing body primitives, Executor computation and Storage application/persistence; its sequence already used those handles and role boundaries. Canonical E2E now explicitly names Executor as the delivery ACK sender after Storage has made canonical state, outputs, cursor and provenance recoverably durable. This resolves the ambiguous “It” without making Storage send the ACK or adding a fresh barrier.

The changes leave Executor::commit control, certification/state-sync ownership, certificate-and-material-before-switch, direct/imported provenance, native no-wait behavior and open proof/policy boundaries intact. No headings, source URLs, signatures or diagrams changed. All five public traits remain byte-identical to baseline; all 18 diagrams still match their canonical inline sources; all 39 undecided policy cells remain blank, with 31 reader pages. The body audit recommends no additional edit.

Snapshot/byte and invariant receipt: `docs-receipts.json`. This is independent reader/source review, not local build, protocol execution, GitBook publication or six-hour completion.
