# Project handoff

Before changing the protocol, paper, or Commonware fork, read:

1. README.md
2. overpass-plan-ordering-outline.md
3. overpass-research-logic.md
4. Relevant implementation files and local instructions.

The current source of truth is overpass-plan-ordering-outline.md. It is a research outline, not an implemented or proved protocol. Updated 2026-09-29 after the user's clarification and Hermes review.

Current direction:

- Autobahn-style parallel dissemination with continuous speculative execution.
- Execution-aware advisory plans use shared ordering fragments and progress reports to align admissible candidates and execution early.
- Hermes is the initial reference consensus; planning does not introduce an independent binding quorum.
- No 3f+1 plan certificate and no waiting for a final plan certificate before ordering proceeds.
- Reports are untrusted performance hints, not execution correctness or finality evidence.
- Preserve Hermes parent/justification, proposal, vote, and finalization rules. A late plan cannot rewrite an existing vote or proposal.
- Prefer common fragments with canonical remainder only where admissible. Hermes's fixed interleaving/block-skip representation does not support arbitrary permutation.
- Finalized ordering prefix, not the plan or its whole candidate, determines canonical execution input.
- Validate reused work against exact prefix/parent/runtime. Common fragment does not imply equal state inputs.
- Separately evaluate moving recovery before finality and reducing total re-execution, including planning overhead in E2E latency.
- Actual fragment selection, hook compatibility, resource isolation, inclusion/liveness and performance remain open.
- Producer placement/grouping, state-owner shards, ZK/PAC, receipt bridges and repair lanes remain out of scope.

Historical binding-plan documents are in research/archive/2026-09-29-binding-plan/INDEX.md. Earlier placement and proof designs are catalogued in research/archive/2026-09-29-before-plan-ordering/README.md. Historical “current/latest” statements do not override this direction.

Commonware, prior toy models and the LaTeX manuscript have not been updated to this design. Do not claim Hermes is already implemented in the fork. Read commonware/AGENTS.md before editing that subtree and preserve unrelated user work.
