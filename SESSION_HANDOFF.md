> **Historical snapshot — superseded by Baton (2026-09-30).**
> Current research: [Baton paper](baton-paper.md), [implementation specification](baton-implementation-spec.md), and [current handoff](BATON_HANDOFF.md).
> The body below is preserved as research/citation history. Its sum-only selection, plan/advisory descriptions, incumbent preferences and “current/latest/source of truth” claims do not override 2f+1-prefix-first selection or the adopted direction-preserving cut requirement. The four proposed implementation defaults remain unadopted; native integration and performance remain unproved.

# Overpass — agent session handoff

Updated: 2026-09-30 (Asia/Seoul).

This is a portable task-state summary, not a full conversation export. It contains user decisions, inspected evidence, unresolved questions and continuation guidance. It does not contain credentials or private model reasoning. Re-check the current files/code before acting; later explicit user decisions supersede this snapshot.

## 1. Start here

Read in this order:

1. This handoff and [AGENTS.md](AGENTS.md).
2. [README.md](README.md).
3. [Current outline](overpass-plan-ordering-outline.md) and [plan policy](overpass-prefix-plan.md): the protocol source of truth.
4. [Research logic](overpass-research-logic.md).
5. [Condensed review / next decisions](overpass-review-next-decisions.md).
6. Relevant sections of [detailed review](overpass-submission-readiness-review.md), especially §§11, 20–25.

Do not reconstruct the current design by merging all files. Many documents intentionally preserve rejected proposals. `paper-outline.md`, `research/paper/`, placement documents and archived “current/latest” statements do not override the current outline and plan policy.

## 2. User objective and positioning

The research goal is to reduce application state-finalization latency in Autobahn-family systems, with EuroSys / OSDI submission quality as the aspiration. The user wants critical, evidence-backed feedback, not automatic agreement or unsupported novelty claims.

Current positioning:

> Overpass is an execution-aware ordering extension for Autobahn-family consensus. It uses validators' intended orders to select ordering candidates favorable to preserving speculative execution, without a separate plan-approval phase or making cut consensus wait for planning.

The contribution under investigation is feedback from distributed intended orders into the final ordering policy. Pre-cut execution alone is not the claimed novelty. Neither universal re-execution minimization nor a new consensus safety protocol is claimed. Actual benefit remains unmeasured.

Communicate compactly in Korean; keep technical terms in English. Paper-facing prose may be English. Explain the problem before introducing mechanisms, minimize invented terminology, and clearly separate adopted decisions from suggestions.

## 3. Decisions already made — do not ask again

| Topic | Adopted decision |
|---|---|
| Implementation target | Native Multimmit; preserve tip extraction and extension |
| Reports | Intended block order, not execution history, progress proof, completion or remote state-root reports |
| Context | Bind epoch/view/base cut/parent/rule/window; one counted report per validator identity |
| Candidate selection | Bounded valid reported candidates plus incumbent; `Score(P)=sum_i |LCP(P,R_i)|` |
| Score meaning | Scheduling proxy, not actual work saved, execution agreement or safety proof |
| Collection | With n=5f+1: 4f+1 distinct valid reports OR fixed leader-local deadline, whichever first |
| Window | Start on first eligible unplanned block; arrivals cannot reset or extend deadline; one close trigger |
| Fallback | Fewer/no reports permitted at timeout; cut never waits for collection, timer or optimizer |
| Churn | Same snapshot/horizon comparison; incumbent wins ties; bounded rearrangement/update rate; suppress unchanged publication |
| Plan approval | No support/ACK quorum and no mandatory 3f+1 common prefix |
| Policy authentication | Selected ordering policy is bound to the leader block and fixed within that proposal |
| Before proposal | Advisory plans may change; they are not finality or permanent locks |
| State finalization | Full irrevocable exact ordering AND f+1 valid matching execution-result signatures |
| Execution signers | Distinct validators of the relevant epoch; not restricted to a particular ordering-QC voter subset |
| Honest execution signature | Direct execution/validation of exact input/range, canonical input state, runtime and result; no certificate echo |
| Read readiness | Durable apply/read availability is separate from result certification |

The user explicitly approved both policy binding and the completion endpoint with “둘다 좋아”. These choices do not establish implementation correctness. The f+1 argument assumes at most f Byzantine identities, authenticated membership, unforgeable signatures and deterministic execution. It does not replace any ordering-consensus phase or quorum.

Do not revive placement/grouping/Multilevel, state-owner sharding, ZK/PAC, receipt bridges, repair lanes, the fixed-cut removal of native extensions, execution-history reports, or discovery-plus-adjustment voting. Hermes is related work, not the adopted engine.

## 4. Most recent technical answer: can this fit Multimmit?

Assessment: plausible, but not merely an execution hook. No impossibility was established, and no completed safety proof or integration exists.

- Pre-cut execution can run outside admission/DA acknowledgement. Do not make block execution completion an admission prerequisite.
- An advisory-only plan can guide speculation without deciding canonical order, but would not realize the full proposed feedback mechanism.
- To influence final order, authenticate the policy in the leader block, including encoding, validity, availability, persistence and recovery.
- Native finality is progressive. Growing vote pools can advance finalized tips. First leader finality is not necessarily completion of the global ordering of every referenced block.
- A canonical emitted prefix must never be reordered by a later extension. A speculative prefix may be corrected/re-executed. Do not silently remove extensions to simplify this.
- The inspected checkout leaves dense `Ord/Emit`, body retrieval and durable ordered delivery to an external marshal. This is a real implementation obligation, not an already available application callback.
- No-wait planning does not remove native settledness, data-availability or application-dependency waits.

First integration gate: with a fixed authenticated policy, prove/test prefix-compatible delivery across different valid vote pools, late extensions and recovery. Then add report selection and evaluate its benefit.

## 5. Code provenance and where to inspect

Reviewed Commonware base: [`534af0ede48affd35b2111522527547b4cc9bf72`](https://github.com/commonwarexyz/monorepo/tree/534af0ede48affd35b2111522527547b4cc9bf72).

The original local checkout is dirty. A clean checkout at that commit does NOT include all local historical artifacts. Reinspect rather than treating the commit link as a complete snapshot of that workspace.

| Path under Commonware | Relevance |
|---|---|
| `consensus/src/multimmit/docs/STATE_MACHINE.md` | Ownership, application-custody fence, external marshal, finality and recovery contracts |
| `consensus/src/multimmit/docs/PROPERTIES.md` | What current tests cover and explicitly leave out |
| `consensus/src/multimmit/types/block.rs` | `LeaderBlock`: round, parent, history, proposals; no ordering-policy field |
| `consensus/src/multimmit/types/vote.rs` | `VoteBody::for_leader` binds the canonical leader-block digest |
| `consensus/src/multimmit/machine/view.rs` | Proposal parent selection and `finish_proposal_request` |
| `consensus/src/multimmit/machine/algebra/tips.rs` | `PoolExtractor::final_tips`, extension and settledness |
| `consensus/src/multimmit/machine/durability.rs` | Frozen signing/publication requests and persistence obligations |

Important inspected facts:

- Consensus owns authenticated protocol facts, not application bodies or execution. `Automaton::verify` is an application validity/availability fence, not an execution-finalization interface.
- `Reporter` notifications are lossy hints; they cannot be the durable authoritative ordered-delivery stream.
- Finality pools reach n−f=4f+1; finalized position uses the 3f+1-th greatest position; native extension and settledness rules remain in force. These numbers are not planner approval thresholds.
- Policy context must match the actual selected proposal parent. Relative offsets from an earlier parent can designate different blocks. DA anchors and ordering-parent tips are not interchangeable.
- Growing pools must not trigger a new policy for an already authenticated proposal.

Original local dirty paths included aggregation code, utils fault code, Cargo files and historical `glue/src/multimmit.rs` / `glue/benches/` artifacts. Preserve user changes. Read that checkout's `AGENTS.md` before editing it. No Commonware source is bundled in this research repository.

## 6. Unresolved design obligations, not yet adopted solutions

1. **Report generation:** Specify how actual block arrivals, base ordering and incumbent plans produce intended orders. Do not inject arbitrary report permutations and call them a network-derived workload.
2. **Window notification:** Define how validators learn the window/context and include communication cost. A local timer does not make the remote context automatically known.
3. **Policy representation:** Exact encoding, candidate completeness, bounded size/validation and treatment of unplanned extension slots.
4. **Native integration:** Authentication, compatible ordered prefixes, actual parent changes, view recovery, missing history/body retrieval and durable delivery cursor.
5. **Execution statements:** Common signing ranges, exact-context identity, collection/retention/recovery. Always signing only each node's latest different prefix can prevent matching signatures from accumulating.
6. **Execution pipeline:** Dependency validation, selective repair, speculative-state retention and bounded resources without stalling consensus.

Review §24 proposes a finite valid prefix `D` followed by the base sweep excluding slots in `D`. It is a candidate, NOT an adopted or implemented encoding. Review §25 considers pre-order execution signatures; that timing policy is also not adopted. Early signatures never make speculative state canonical without full ordering and exact-context checks.

Review §23.6 has a conditional prefix-compatibility lemma for a fixed sweep and compatible completions. It does not prove that the entire modified native protocol supplies those assumptions through view changes and recovery.

## 7. Evaluation contract

Keep three primary configurations:

1. **Original:** Execute after the input's irrevocable ordering, not merely the first leader-finality event.
2. **Pre-cut execution:** Execute received blocks under the base rule; validate/repair final order; no separate leader-plan broadcast.
3. **Overpass:** Same backend and speculation path plus intended-order planning.

Early proposal is not the baseline. Frequent cuts are an optional sensitivity study. Timer-only, strict 4f+1 and hybrid collection are ablations. Use the same resources, signature machinery and completion conditions. If early execution-signature propagation is adopted, give it to Pre-cut execution as well.

Primary completion is when a designated observer verifies full ordering evidence and f+1 matching execution signatures with the correct canonical parent/runtime. Measure with that observer's monotonic clock. Separate leader finality, irrevocable ordered delivery, body readiness, result certification, durable apply and read readiness.

Required evidence chain:

```text
actual arrivals → reports → chosen/final order → validated reuse/repair
               → residual work + planning/communication/certification costs
               → state-finalization latency, ingress latency and backlog
```

Do not claim improvement merely because:

- LCP increases (intended order is not execution progress).
- Reordered suffix length decreases (independent work can be reused).
- Cut→state shrinks while ordering is delayed and ingress→state worsens.
- Only completed requests look faster while backlog or failed transactions increase.
- Final ordering chooses cheaper application branches. Even identical success counts and final state can have different inherent work.

Outline §5.3 adds fixed-cost dependency workloads and per-run final-order reference replay for causal diagnosis. Replay is offline, not an online oracle or a fourth primary configuration. Do not subtract serial replay wall time from parallel execution latency.

## 8. What evidence actually exists

| Material | Status / allowed use |
|---|---|
| Current outline/policy/reviews | Research design and critique, not implemented/proved protocol |
| Python `research/block_views` tests | Prior review records 35 passing tests for an older model; not re-run for this handoff and not current Overpass validation |
| Small score/cache/arrival/sweep calculations in review | Conditional examples, counterexamples and finite sanity checks; not distributed experiments or full proofs |
| Historical Commonware state-finality microbenchmark | Hash-based execution and precomputed join; no current planner/network/signature pipeline; not E2E evidence |
| Native consensus tests discussed in review | Source inspection is not a claim that those tests were executed in this session |
| `research/paper/` LaTeX | Earlier manuscript; not synchronized with current model |
| Google Docs | Earlier reviews exist; not synchronized with latest local design |
| Current Overpass implementation / native adapter / E2E results | Absent |

Some diagnostic calculations were run directly in tool sessions and documented as examples rather than committed as reproducible test programs. Recreate and preserve scripts/seeds before citing them as artifact evidence. Do not add the many toy-check counts together as a protocol-validation total.

## 9. Work state and authorization

- The prior persistent goal was critical review toward EuroSys / OSDI quality.
- Its recorded status is **blocked**, not complete: a separate request to expand into prototype implementation was awaiting user approval.
- Subsequent user requests authorized creating the private research repository and uploading this handoff. They did not themselves authorize a Commonware implementation, cloud deployment, spending, publishing the paper or editing external review threads.
- A future explicit implementation request should resolve that scope question; do not repeatedly ask for already approved policy/endpoint decisions.
- No live test, build, agent or cloud run is being handed off. Do not infer a running process from old logs or session names.
- No PR was created. This repository was pushed directly to its new `main` branch.

## 10. Repository and session pointers

- Private repository: https://github.com/djm07073/overpass-research
- Initial research snapshot commit: `8b596b8da336eda5c2a045f4b226786d7bb0785d`.
- Local repository: `/Users/suhajin/dev/b-harvest/ault/ault-project/overpass-research`.
- Original working directory: `/Users/suhajin/dev/b-harvest/ault/ault-project/clob-research`.
- Original remote: `git@github.com:b-harvest/dex-research.git`; unchanged by export.
- Original Commonware checkout: `<original working directory>/commonware`; not exported.
- Codex source thread ID: `01a0205a-a453-7e72-9b20-32178974f621` (local app retrieval aid, not a public share link or an authorization grant).

This repository is a snapshot, not an automatic two-way sync. Do not overwrite newer changes in either directory. If work continues here, identify the active working repository explicitly and commit future decisions alongside the current outline/policy. Do not import credentials or raw application session stores to transfer context.

## 11. Suggested first message to a successor agent

> Read SESSION_HANDOFF.md and AGENTS.md, then the current outline, prefix-plan and condensed review. Continue from Native Multimmit plus intended-order score-guided planning; do not restore placement, fixed-cut extension removal or plan approval voting. Explain which integration obligations remain and inspect the actual target code before proposing changes. Distinguish adopted decisions, proposed mechanisms, conditional examples and verified results. The next implementation work requires an explicit user request; if authorized, produce a concrete code-grounded plan and preserve existing user changes. Do not claim E2E validation until the current three configurations actually run under the same completion conditions.

If the user later delegates work to multiple agents, useful separate review tracks are native ordering/recovery, report/planner semantics, and evaluation/causal attribution. Agree on shared protocol contracts before concurrent edits; this handoff does not launch or authorize external messaging to any other task.
