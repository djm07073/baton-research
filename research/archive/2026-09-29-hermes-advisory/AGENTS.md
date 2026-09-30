# Project handoff

Before changing the protocol, paper, or Commonware fork, read:

1. README.md
2. overpass-plan-ordering-outline.md
3. overpass-research-logic.md
4. Relevant implementation files and local instructions.

The current source of truth is overpass-plan-ordering-outline.md. It is a research outline, not an implemented or proved protocol. Updated 2026-09-29 after the user's clarification and Hermes review.

Current direction:

- Autobahn-style parallel dissemination with continuous speculative execution.
- Advance ordering plans use known blocks/tips, valid parent context and the common ordering rule to announce admissible execution order early.
- Hermes is the initial reference consensus; planning does not introduce an independent binding quorum.
- No 3f+1 plan certificate and no waiting for a final plan certificate before ordering proceeds.
- Do not use remote execution histories, progress/completion reports, claimed reuse or execution proofs as planning inputs. Local execution validation and offline benchmark instrumentation remain required but do not feed plan selection.
- Preserve Hermes parent/justification, proposal, vote, and finalization rules. A late plan cannot rewrite an existing vote or proposal.
- Use the common canonical rule for candidate ordering and remaining blocks, within Hermes's admissible value space. Its fixed interleaving/block-skip representation does not support arbitrary permutation.
- Finalized ordering prefix, not the plan or its whole candidate, determines canonical execution input.
- Validate reused work against exact prefix/parent/runtime. A common plan does not imply equal state inputs, complete data or completed execution.
- Separately evaluate moving recovery before finality and reducing total re-execution, including planning overhead in E2E latency.
- Plan publication/revision and its alignment with actual proposals, hook compatibility, resource isolation, inclusion/liveness and performance remain open. Compare against simply disseminating a valid normal proposal earlier.
- Producer placement/grouping, state-owner shards, ZK/PAC, receipt bridges and repair lanes remain out of scope.

The prior execution-history-based version is in research/archive/2026-09-29-execution-history-plan/INDEX.md. Historical binding-plan documents are in research/archive/2026-09-29-binding-plan/INDEX.md. Earlier placement and proof designs are catalogued in research/archive/2026-09-29-before-plan-ordering/README.md. Historical “current/latest” statements do not override this direction.

Commonware, prior toy models and the LaTeX manuscript have not been updated to this design. Do not claim Hermes is already implemented in the fork. Read commonware/AGENTS.md before editing that subtree and preserve unrelated user work.
