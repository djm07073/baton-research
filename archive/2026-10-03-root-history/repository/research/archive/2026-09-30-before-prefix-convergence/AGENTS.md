# Project handoff

Before changing the protocol, paper, or Commonware fork, read:

1. README.md
2. overpass-plan-ordering-outline.md
3. overpass-research-logic.md
4. Relevant implementation files and local instructions.

The current source of truth is overpass-plan-ordering-outline.md. This is a research outline, not an implemented or proved protocol. Updated 2026-09-29 following the user's correction: Hermes is related work, NOT the adopted consensus engine.

Current direction:

- Autobahn-family parallel dissemination with continuous speculative execution.
- Leader proposes advance ordering plans from known blocks/tips, valid parent context and ordering rules.
- Accepted plans and producer tips jointly determine final cut ordering. Do not reduce plans to execution-only advisory hints.
- Do not use remote execution histories, progress/completion reports, claimed reuse or execution proofs as planning inputs. Local validation and offline instrumentation remain required.
- Plan proposal, protocol acceptance and full ordering finality are distinct events.
- Plan acceptance/quorum, conflict prevention, preservation scope, cut closure, late-plan handling and leader-change recovery remain explicit design/proof obligations.
- Do not automatically restore historical 3f+1 plan certificates or mandatory waiting for the last plan; do not import Hermes thresholds or fixed interleaving.
- Plans may affect the default canonical order; define their admissible scope and deterministic composition. Order the unconstrained remainder by the common canonical rule.
- Production and speculative execution continue alongside planning. Cut liveness without plan-induced blocking must be proved, not inferred from pipeline concurrency.
- Canonical adoption requires actual finalized cut/order and exact parent/runtime execution validation. Common plan/order does not imply complete data or completed execution.
- Separately evaluate moving recovery before finality and reducing total re-execution, including planning and consensus costs in E2E latency.
- Compare with unguided speculation, early ordinary proposals and more frequent cuts.
- Producer placement/grouping, state-owner shards, ZK/PAC, receipt bridges and repair lanes remain out of scope.

The mistakenly Hermes-advisory version is preserved in research/archive/2026-09-29-hermes-advisory/INDEX.md. Other historical versions are catalogued in README.md. Archived “current/latest” statements do not override the current direction.

Commonware, prior toy models and the LaTeX manuscript have not been updated to this design. Read commonware/AGENTS.md before editing that subtree and preserve unrelated user work.
