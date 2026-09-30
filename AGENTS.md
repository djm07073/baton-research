# Project handoff

Before changing the protocol, paper, or Commonware fork, read:

1. README.md
2. overpass-plan-ordering-outline.md
3. overpass-research-logic.md and overpass-prefix-plan.md
4. Relevant implementation files and local instructions.

Current source of truth: the outline and overpass-prefix-plan.md. Updated 2026-09-30 to score-guided planning with bounded collection. Research design only, not implemented/proved. Hermes is related work, NOT the adopted consensus engine.

Current decisions:

- Autobahn-family dissemination and cut consensus overlap speculative execution.
- Native Multimmit is selected: preserve tip extraction and extension. Exact-order integration remains unimplemented; do not revive the archived fixed-cut design.
- Validators asynchronously report intended block order from a shared cut/parent context. No remote execution history, progress proof or completion claims.
- Leader selects among bounded valid reported candidates and the incumbent using Score(P)=sum_i |LCP(P,R_i)|. This is a scheduling heuristic, not actual work minimization or a quorum proof.
- No mandatory 3f+1 common prefix and no adjustment/support voting round. Prior discovery+adjustment design is archived.
- With n=5f+1, collect 4f+1 distinct valid reports OR until a fixed local deadline, whichever comes first. Report coverage is not agreement on the selected plan.
- Bind reports to epoch/view/cut/parent/rule/collection window; count one per validator identity. Do not mix contexts.
- Start the initial window on first eligible unplanned block; use configurable duration tau. New arrivals never reset/extend the deadline.
- Timeout with fewer reports is allowed; no-report fallback uses a valid incumbent or base ordering rule. Threshold and timeout trigger each window only once.
- Cut must not wait for report count, timer or optimizer completion. Use an already prepared valid candidate/base fallback when cut is ready.
- A late plan cannot change an already sent proposal/vote. Stale computation and parent changes require explicit context checks.
- Compare incumbent/new candidate on the same snapshot and horizon. Prefer incumbent on ties; limit rearrangement and update frequency, suppress unchanged publications.
- Plans guide execution without follow-up approval quorum or irreversible lock. Byzantine reports/leaders can degrade performance.
- Full cut finality must bind chosen exact order; validate execution against exact input/parent/runtime.
- User adopted policy binding: the selected ordering policy is authenticated with the leader block and fixed within that proposal. Advisory plans before proposal remain mutable; no extra plan-approval quorum. Encoding, extension continuation and recovery are not yet implemented/proved.
- User adopted state finalization: full irrevocable ordering plus f+1 valid matching execution signatures from distinct epoch validators, bound to exact ordered input/range, canonical input state, runtime and result. Honest signers directly execute/validate, not echo certificates. Signers need not belong to a particular ordering QC. Durable/read readiness is auxiliary, not implied by result certification.
- Window/encoding, input validity/availability, candidate bounds, churn tuning, stale computation, recovery and consensus integration remain proof/implementation obligations.
- Primary comparisons: Original / Pre-cut execution (no separate leader plan broadcast) / Overpass. Collection and churn policies are ablations; frequent cuts are a separate sensitivity study. Do not restore early proposal as the pre-cut baseline.
- Native leader finality is not automatically completion of global ordering for every referenced block. Primary completion is local verification of full ordering evidence and the matching f+1 execution signatures in the correct canonical context; apply/durability/read readiness are separate events.
- No placement/grouping, state-owner shards, ZK/PAC, receipt bridges or repair lane revival.

Archived originals are in research/archive/2026-09-30-before-scored-plan/INDEX.md and earlier archives linked by README.md. Historical “current/latest” claims do not override this direction.

Commonware, toy models and LaTeX have not been updated. Read commonware/AGENTS.md before editing that subtree and preserve unrelated user work.
