# Project handoff

Before changing the protocol, paper, or Commonware fork, read in order:

1. README.md
2. overpass-plan-ordering-outline.md
3. Relevant implementation files and their local instructions.

The user requested a fresh research outline on 2026-09-29. overpass-plan-ordering-outline.md is the current research source of truth, not a completed protocol specification.

Current direction:

- Autobahn-family dissemination/cut agreement with continuous speculative execution.
- Leader-coordinated successive plans protect exact prefixes against late insertion.
- Base ordering is not restricted to relative-height round-robin.
- Execution and production do not await plan certification or cut finality.
- At cut initiation, finish the current final plan, stop proposing new plans for that interval, and propose a cut binding its plan chain, tips, final order, and parent.
- Unfinished plan certification, vote/lock fencing, leader recovery, and plan/cut safety and liveness are explicit proof obligations. Do not silently discard binding votes on timeout.
- Candidate profile: n=5f+1, plan support 3f+1, cut quorum 4f+1. Quorum arithmetic is not a complete protocol proof.
- Speculative results require exact-context validation; plan votes do not certify execution correctness.
- Producer placement/grouping, ZK/PAC, state-owner shards, receipt bridges and repair lanes are not part of the new proposal.

Historical materials are catalogued in research/archive/2026-09-29-before-plan-ordering/README.md. Earlier paper-outline.md, proof-aware protocol/SDK, placement files and research/paper/ manuscript are reference-only, even where their historical text says “current”. Preserve them and unrelated user work.

The commonware/ fork has not been updated to the new design. Read commonware/AGENTS.md before editing that subtree. Existing legacy EC code and toy models are not evidence of an implemented or proved plan/cut protocol.
