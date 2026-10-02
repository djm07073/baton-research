# Project handoff

Before changing the protocol, paper, or Commonware fork, read these files in order:

1. `README.md`
2. `proof-aware-multimmit-paper.md`
3. `commonware-proof-sdk.md`
4. `paper-outline.md` when working on the paper

`proof-aware-multimmit-paper.md` is the active protocol source of truth. Do not revive the removed EC/DCLP/atomic-commit plan from older notes.

Current baseline:

- Commonware Multimmit extension; Sei is out of scope.
- Keep Multimmit DA certificates and ordering safety core.
- Use state-isolated lanes with application-specific rolling validity proofs.
- Broadcast proof sidecars and form `f+1` Proof Availability Certificates before the cut when possible.
- A proof/PAC is branch-specific readiness evidence, not canonicality; join only the exact prefix selected by the L-QC-derived cut.
- Cross-lane execution uses statically declared lane-local fragments and conflict-scoped `Commit`/`Abort` branch proofs.
- Participant lanes execute fragments immediately on speculative overlays; finalized cut selection is the only canonical admission point.
- All participants use the same cut-relative selector, so a cross-lane operation commits on every lane or aborts on every lane.
- Unselected overlays are discarded; do not introduce canonical rollback, receipts, participant handshake, or a repair lane into the active baseline.
- Static conflict closure limits dual execution/proving to dependent state. Monolithic full dual-fold is only a baseline; the target uses componentized deltas and a disjoint join proof.
- Bound unresolved conflict width, decision horizon, overlay bytes and proof work; overflow falls back only for the affected component.
- Proof readiness must not block Multimmit ordering. A missing proof delays the affected state component and triggers PAC recovery/finalized-cut-count failover.
- Certificate, speculative execution and folding primitives are mechanisms, not standalone novelty claims.

The `commonware/` fork is based on `cl/multimmit` commit `534af0ed`. Its existing EC reducer is legacy PoC code, not the active implementation plan. Read `commonware/AGENTS.md` before editing that subtree and preserve unrelated/untracked user work.
