# Baton project handoff

Before changing the research, paper, specification, or any external Commonware checkout, read:

1. README.md and BATON_HANDOFF.md.
2. baton-paper.md and IMPLEMENTATION_SPEC.md. The earlier implementation snapshot is preserved under archive/2026-10-03-root-history/repository/research/archive/2026-10-03-implementation-outline/.
3. Relevant cited historical reviews and applicable local instructions.

The latest user decisions are authoritative. IMPLEMENTATION_SPEC.md is the single current implementation document as of 2026-10-03. Its four-layer architecture excludes Bank semantics for now and keeps undecided policy cells empty. Source-grounded existing APIs and proposed integration contracts must stay distinct. Linked Google Docs remain research/source references; do not overwrite the latest user architecture with an older snapshot. The research paper and archived earlier implementation file derive from manual 2026-09-30 snapshots of the verified native documents; the current implementation architecture was rewritten from the latest user outline. Compare revisions before synchronizing; preserve concurrent edits. Old Overpass files and archived “current/latest” claims are historical sources, not current instructions. The archived SESSION_HANDOFF.md preserves earlier session history.

Current adopted requirements:

- Project name: Baton; paper title: “Baton: Execution-Aware Ordering for Autobahn”. Keep the repository name, source URLs, historical citations and archive filenames unchanged. Use direction in current prose.
- Base: Native Multimmit, n=5f+1. Preserve tip extraction and extension; the concrete direction-preserving adaptation is unimplemented/unproved. Hermes is related work, not the adopted engine.
- Reports are authenticated intended orders, not execution history, progress proofs, execution completion or approval votes. Bind exact epoch/view/history/canonical parent/rule/window/frontier; count one identity once and preserve raw support through completion.
- Within a fixed admissible bounded full-candidate set whose evaluation has finished, maximize the length of a valid nonempty ENTIRE prefix supported by at least 2f+1 distinct same-context original reports. Otherwise use sum-LCP; without reports/prepared valid candidates use actual-parent valid base policy. Do not claim exhaustive longest selection from unfinished search.
- Close the local report snapshot once at first 4f+1 valid distinct admissions or the fixed deadline, whichever event is processed first. Exclude excess/later reports; m<=4f+1. Arrivals do not extend the deadline.
- Cut does not wait for reports, timer or optimizer. Separate report-window closure from the still-unspecified point where a prefix becomes protected. After authenticated adoption, dropping/reinterpreting that prefix as fallback is forbidden.
- Leader must construct a cut proposal that includes the selected valid prefix AND preserves its exact leading execution sequence for the same canonical input state/runtime after the immutable frontier. Validators must verify preservation. Membership alone is insufficient. Adoption/availability, native sufficiency, cross-lane continuation and view recovery are open proof obligations, not implemented guarantees.
- Freeze selected prefix/policy/rule in the authenticated proposal subject bound to its actual parent/frontier. Late reports, optimizer completion and growing native pools do not change that proposal's policy. Pre-proposal advisory direction remains mutable.
- Primary state finalization requires irrevocable exact order plus f+1 valid matching signatures of distinct epoch validators over the same input/range, canonical input state, runtime and result. Honest signers directly execute/validate; they need not belong to a particular ordering QC. Durable/read readiness is separate.
- Executor owns state finalization and validator state sync as a normal-path option. Executors exchange execution signatures, certificates and change sets directly over Commonware P2P; ResultService is an internal Executor helper. Baton controls speculative scheduling/report/direction only and must not relay or gate result certification, state sync or canonical apply. Deliver exact ordered input directly from Orderer to Executor; Executor returns durable delivery ACK to Orderer and outcomes to TxPool. Baton applied-progress notification is optional and needs no approval. Stop unfinished execution only after the certificate and applicable material are verified, preserve direct-vs-imported signing provenance, and share the canonical writer/fencing/recovery contract. Concrete switching/codec/storage contracts and integration proofs remain open.
- Preserve emitted order and authenticated segment interpretation through recovery; unresolved slots stop emission, authenticated included slots emit and irrevocably-empty slots skip. Terminal states/identity cannot be reversed. Sparse native certificates do not implement external marshal recovery or dense delivery.
- Per-block signing, incumbent-first tail, inline policy bytes, and finite-prefix permutation are UNADOPTED proposals. Do not make them defaults through editorial edits or implementation. The exact continuation and prefix-adoption bridge remain unresolved.
- Keep Original / Pre-cut execution / Baton as the three primary comparisons with the same backend/resources/endpoint. Pre-cut has no separate direction broadcast; early proposal is not that baseline. Frequent cuts are a sensitivity study. Benefits remain hypotheses.

Evidence and scope:

- Reviewed native source is pinned to 534af0ede48affd35b2111522527547b4cc9bf72. Final position is the 3f+1-th GREATEST position. Distinguish ordinary payload positions, certified anchors, extension support and settlement facts.
- The conditional [1,0,0,0,0] example is analytical source reasoning under stated availability/report-admissibility assumptions; it is not an executed trace, a permanent-exclusion result or a completed Baton counterexample.
- 2f+1 support guarantees f+1 honest intentions under the shared fault budget. Execution reuse additionally requires preserved exact context/order and valid executed work/checkpoints. Reports do not prove this progress.
- Existing archives, toy models, historical test counts, microbenchmarks and LaTeX do not validate Baton. Do not compile/run them merely to claim documentation validation.
- Draft PR1 remains an older unmerged validation plan. Reuse useful fixtures/gates with explicit current assumptions; do not silently merge, close or promote its candidate encoding.
- No protocol implementation, benchmarks, spending or external review-thread edits are authorized by a documentation synchronization request. Honor any subsequent explicit user authorization without asking again.
- Preserve user changes and Git history. Do not force push or reconfigure credentials. Read an external checkout's AGENTS.md before changing it.
- Do not revive historical fixed-cut extension removal, a 3f+1 direction plan-lock, execution-history reports, placement/grouping, state-owner sharding, ZK/PAC, receipt bridges or repair lanes.
