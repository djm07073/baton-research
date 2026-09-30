# Project handoff

Before changing the protocol, paper, or Commonware fork, read:

1. README.md
2. overpass-plan-ordering-outline.md
3. overpass-research-logic.md and overpass-prefix-plan.md
4. Relevant implementation files and local instructions.

Current source of truth: overpass-plan-ordering-outline.md and the detailed decision in overpass-prefix-plan.md. Updated 2026-09-30. This is research design, not an implemented or proved protocol. Hermes is related work, NOT the adopted consensus engine.

Current direction:

- Autobahn-family parallel dissemination and cut consensus with continuous speculative execution.
- n=5f+1; target plan support q=3f+1 distinct validator identities, not producer lanes.
- Validators report intended block order from the same cut/canonical parent, not execution history or completion.
- Discovery path: find the longest valid prefix supported from its beginning by q reports. Do not use a middle fragment, subsequence, or a minimum-disagreement order optimizer. Receiving q reports is not enough if no nonempty/new prefix has q support.
- Adjustment path: when no new supported prefix exists, leader proposes one valid fixed candidate. Honest validators may adopt it despite a different previous schedule, send support without awaiting re-execution, and adjust execution concurrently.
- Freeze the candidate within an adjustment round; late blocks go into subsequent extensions. Missing mandatory ancestors cannot be bypassed.
- Count one immutable report/support per identity per context, bind subject/phase/epoch/view/round/parent/rule, and never mix rounds or discovery reports with adjustment endorsements blindly.
- Same-context incompatible-prefix exclusion follows conditionally from 2q-n=f+1 and honest non-equivocation. It does NOT prove cross-round finality, execution completion or leader-change preservation.
- Normal leader policy extends the supported prefix, avoiding insertion ahead of or inside it. This is not an irreversible ordering lock. Existing consensus safety and actual finalized cut take precedence.
- Block production/dissemination/execution continue during reporting/support collection. Do not make unfinished plans an unconditional cut barrier.
- Bind chosen exact order to full cut finality; validate execution against exact cut/parent/runtime. Plan support, ordering finality and result certification are separate.
- Round transitions, equivocation recovery, stale support, data recovery, cut/plan boundary and integration safety/liveness remain design obligations.
- Compare against unguided speculation, discovery-only, early proposals and frequent cuts. Include adjustment/network costs; do not claim no re-execution or automatic novelty.
- No remote execution proofs/history in plan selection; local execution validation and offline metrics remain required.
- Producer placement/grouping, state-owner shards, ZK/PAC, receipt bridges and repair lanes remain out of scope.

Previous documents are archived in research/archive/2026-09-30-before-prefix-convergence/INDEX.md and the archives linked by README.md. Archived “current/latest” claims do not override current decisions.

Commonware, prior toy models and LaTeX have not been updated to this design. Read commonware/AGENTS.md before editing that subtree and preserve unrelated user work.
