# App scheduler integration review — 2026-10-09

**Completed after three hours of iterative review**, from 06:57:26 UTC through 09:57:55 UTC on 2026-10-09. Read the [final requirement audit](final-audit.md) and [bound validation snapshot](final-checkpoint.json). [run.json](run.json) preserves the timeline. No external publication was performed. Earlier checkpoint sections below describe their status at their own recorded times.

The user requested a complete rewrite of docs/baton around App-owned TxPool and Pre-cut/Baton schedulers, existing Automaton::verify and Marshal Reporter<Update>, with repeated independent simplification and source verification. Companion current pages, Rust reference/export and diagrams are aligned so the old public-layer design does not survive in adjacent instructions.

Source evidence uses the actual parent checkout `6233438985d8249d2b2bc1204191d5d405652288` and research baseline `08cfe68b8b565fff4a0f8119cb36ec9b22062a31`. The earlier `534af0e` pin, paper, archives and publication reviews remain historical. The latest user decision supersedes earlier current-state claims that Multimmit lacks Marshal or needs a separate app delivery engine.

## Round 1: source and ownership rewrite

- [Native audit](native-audit.md): three verify paths; supplied custody/delivery machinery; header/body identities; Update/ACK and no retry on Backoff; missing native policy hook.
- [Simplification audit](simplification-audit.md): minimal App responsibilities and boundaries to retain.
- [Companion alignment](alignment-audit.md): all entry/E2E pages, source anchors and diagram/tooling coverage.

First rewrite removes four proposed public application traits, reuses Marshal's normal delivery path, and keeps execution effects/root preparation and result certification within App. Nineteen Mermaid sources are updated. Initial docs checks pass links/navigation/export but correctly reject stale renders; fresh rendering/build remains pending.

## Review requirements

1. TxPool and both schedulers are App-owned; Pre-cut has no Baton instance or report traffic.
2. Verify checks validity/custody, handles local/remote/recovery calls and registers usable candidates without awaiting speculative execution.
3. Update transfers retained canonical input promptly; reuse/repair and durable state precede ACK; native consensus never awaits this ACK.
4. Ordinary Marshal body, order, backfill and cursor logic is reused rather than duplicated through public layers.
5. Exact-parent execution, pending-only sorting, authenticated report windows/support and result/import provenance remain explicit.
6. Full Baton native policy/adoption/continuation/recovery work remains clearly unimplemented; canonical Updates are never locally reordered.
7. Current pages, local links, generated Rust excerpts and rendered diagrams agree; historic paper/archive/review records remain preserved.
8. Three hours of iterative subagent work and a fresh requirement-by-requirement final audit are directly evidenced before completion.

No protocol implementation, native runtime test, integration proof or benchmark is claimed. No commit, push or external publication is part of this task.

## 07:27 UTC checkpoint: initial implementation docs and independent review

The complete first rewrite and subsequent source corrections are in place. [Checkpoint evidence](checkpoint-0727.json) binds current reader/asset hashes and exact validation scope. `docs:check` passes for 32 pages, 224 local links and 19 matching rendered Mermaid diagrams; `docs:build` and `git diff --check` pass. The browser check summarized in [checkpoint evidence](checkpoint-0727.json) loaded 32 pages and 19 diagrams and exercised search/mobile navigation. Its original raw browser receipt was not preserved; the mutable latest browser receipt describes a later run. Desktop/mobile callback screenshots were inspected. The final diagram19 title-only change was separately rendered/viewed after that browser run, then the site rebuilt.

Independent reports:

- [Developer walkthrough](round2-developer-walkthrough.md): role distinction, genesis, candidate re-evaluation at live activation and precise custody sequencing.
- [Native correctness](round2-native-correctness.md): floor-reset window overlap, current remote closed-verdict redispatch and pending producer-parent validation.
- [Simplification review](round2-simplification.md): ordinary order delivery reuse, preservation of execution/result invariants and bounded floor transitions.
- [Execution scenarios](round3-execution-scenarios.md): 24 analytical event traces; these are document/source checks, not runtime tests.
- [API/source binding](round3-source-binding.md): current signatures, get/fetch versus durable subscribe/stage, and native diagram verification.
- [E2E visual review](round3-visual-e2e.md): actual pixels for diagrams02–15, including corrected peer endpoint, canonical worker and native concurrency annotations.
- [Scheduler invariants](round4-scheduler-invariants.md): pending-only rule, fixed snapshot/support/no-wait and no adoption of the four unresolved policy choices; diagrams17–19 inspected.

The first elapsed half hour is progress, not completion of the requested three hours. Further adversarial event, retention and result/persistence reviews are running. The goal stays active through the original minimum end time and a fresh full audit.

## 07:46 UTC checkpoint: callback ownership and reader simplification

The [next checkpoint](checkpoint-0746.json) records the revised pages/assets. Current docs check passes for 32 pages, 240 local links, 19 diagrams and 38 blank policy cells. Build and diff checks pass. A fresh local browser pass loaded all 32 pages/19 images and exercised search/mobile navigation; the updated App entry screenshot was directly inspected. Diagrams02/08/09 were rerendered from their edited sources and pixel-reviewed.

- [Retention review](round4-retention-source.md) separates native body release from App candidate retirement.
- [App event traces](round4-app-event-traces.md) check receipt, custody and canonical-entry assumptions.
- [Result persistence](round5-result-persistence.md) preserves direct/imported evidence and exact state linkage.
- [Authority boundaries](round5-authority-boundaries.md) checks caller-authenticated startup floors and local Update authority.
- [Reader simplification](round5-reader-simplification.md) moves the concise pool contract before its optional backend survey and removes repeated callback pseudocode.
- [Boundedness](round6-boundedness.md) checks ACK-window progress, current attempts and eager strategy work.
- [Lifecycle review](round6-lifecycle.md) identifies Marshal-open tasks, existing service supervision boundaries and accepted work surviving caller cancellation.
- [App races](round7-app-races.md) checks claim-before-launch, exact replay exit, writer rechecks and owner-serialized durable publication.
- [Source-link targets](source-link-targets.json) records an earlier local file/line-bounds check of 94 pinned references. This does not assert remote URL reachability or semantic verification of every linked line.

The main entry now links directly to App pool behavior and no longer repeats the old-layer replacement table. Callback documentation explicitly handles an Update as the App's first encounter with a block and keeps pool maintenance outside the ACK approval path. Native payload authority and preservation of original adopted requirements are under further independent review. This remains an intermediate checkpoint before 09:57:26 UTC.

## Subsequent core simplification and preservation pass

- [Callback reader trace](round6-reader-callbacks.md) verifies the current source-to-App connections and the three corrected E2E diagrams.
- [Payload authority](round7-payload-authority.md) separates existing body codec/commitment/custody checks from App transaction semantics, including canonical-first input.
- [Core simplification](round7-core-simplification.md) proposes three changes subsequently applied by root: essential startup with existing detail links, ordinary Update/ACK milestones before floor exceptions, and one shared canonical worker instead of a second apply recipe in the scheduler page. Writer/live-access and current-owner checks remain explicit. The pool page now distinguishes local selection from peer/canonical block validity.

The latest docs check passes 32 pages, 244 local links, 19 diagrams and 38 blank policy cells; diff and build checks pass. The previous browser receipt remains scoped to its recorded time, before these later prose-only edits. A source comparison also restored planning-completion window/attempt checks and concrete storage/certificate recipe safeguards. Full requirement-preservation and native-policy-gap reviews continue; the three-hour task is still active.

Those two reports are now available: [semantic preservation](round8-preservation.md) maps all nine baseline/current App pages and five restored requirements; [native policy gap](round8-native-policy-gap.md) traces construction, signing, validation, recovery and fixed Marshal traversal. Existing native context/authentication is reused; a production Baton adoption/preservation seam is still missing. Neither report claims executed protocol tests or completion of the three-hour window.


## 08:12 UTC checkpoint: exact native boundaries and rendered flows

- [Role walkthrough](round8-role-walkthrough.md) checks producer, nonproducing validator, observer and startup behavior.
- [Native activity pressure](round9-activity-pressure.md) verifies direct Marshal reporter wiring and existing bounded/coalesced hints.
- [Durable boundaries](round9-durable-boundaries.md) checks the successful barrier, selected recovery targets and source-backed execution links.
- [Native diagram semantics](round10-native-diagrams.md), [E2E diagram semantics](round10-e2e-diagram-semantics.md) and [App diagram semantics](round10-app-diagrams.md) distinguish accepted storage work, durable custody, native finality, transaction effects and durable App completion.

Diagrams04/05/09/14/15 were rerendered and their final pixels inspected by root or the named reviewing agent. A fresh browser check loaded 32 pages and 19 images and passed search/mobile navigation. Root directly inspected the updated mobile callback and desktop architecture screenshots. Current docs check (32 pages, 247 local links, 19 diagrams, 38 blank policy cells), build and diff checks passed. Subsequent small reader edits are outside this browser snapshot until rebuilt.

A source correction restored the real `Start::Floor.floor_generation` requirement: it is authenticated and bound to the imported snapshot by the caller. `Floor` and `Update` themselves do not carry this field. The earlier misleading preservation note records the correction explicitly. Independent floor-authority, App implementability and original-reader-requirement reviews continue. This is still progress within the requested three hours, not completion.


## 08:24 UTC checkpoint: callback concurrency and continued simplification

[Checkpoint evidence](checkpoint-0824.json) records the current reader/asset hashes and successful docs check/build/diff scope.

- [Floor authority](round11-floor-authority.md), [App implementability](round11-app-implementation.md) and [reader requirements](round11-reader-requirements.md) confirm the corrected startup configuration and original requested boundaries.
- [Callback errors](round12-callback-errors.md), [App counterexamples](round12-app-counterexamples.md) and [migration hygiene](round12-migration-hygiene.md) check clone ownership, cancellation, seven racing/recovery traces, current entrypoints and preserved history.
- [Event provenance](round13-event-provenance.md) distinguishes transaction-header authentication from generic native admission observations.
- [Wait continuations](round13-wakeups.md) identifies current-attempt termination cleanup, now made explicit in the canonical handler.
- [Reader simplification](round13-reader-simplification.md) records three applied prose cuts and where every removed explanation remains authoritative.
- [Rust source binding](rust-source-binding.json) compares all seven excerpted declarations with the pinned source; [native link targets](current-source-links.json) records a local file/line and exact Git-blob check at its own timestamp. Neither check claims compilation, remote availability or automatic semantic proof.

Cloned callback handles now explicitly share App state while body/custody waits run as bounded pending jobs. Native AppExecutor is labeled as local callback work. Compatibility anchors now lead to the corresponding ownership/callback/canonical sections. The Rust reference remains existing API excerpts. No new protocol or public App framework was introduced. The three-hour review remains active.


## 08:41 UTC checkpoint: progress under load and concrete API limits

[Current checkpoint](checkpoint-0841.json) records successful docs check/build/diff and the fresh local browser pass: 32 pages, 19 diagrams, search and mobile navigation. Root inspected the current mobile callback screenshot. Diagrams02/13 were rerendered from matched sources and pixel-reviewed; admission is separate from dispatch, and scheduling resumes only after successful native readiness and a valid App base. Prior available browser receipts are preserved under timestamped directories in [browser](browser/README.md).

- [Native extension surface](round14-extension-surface.md) challenges public configuration/observer/verifier/constructor hooks; none supplies full authenticated Baton prefix adoption and continuation.
- [Progress budgets](round14-progress-budgets.md) identifies bounded-but-starved required work; the core handler and future acceptance cases now require progress under optional backlog.
- [Flow consistency](round14-flow-consistency.md) records the two diagram corrections and source/image fingerprints.
- [Custody liveness](round15-custody-liveness.md) distinguishes native callback widths from App/Marshal capacities and canceled work still alive.
- [Concrete branch APIs](round15-branch-api.md) corrects reader version/snapshot assumptions and narrows ancestor-retention requirements to actual operations.
- [Identity language](round15-identity-language.md) distinguishes digest/reference, parent, generation, progress coordinate, root/proof and threshold meanings.
- [Body progress](round16-body-progress.md) traces fetch-first custody through existing put/stage APIs when an earlier subscription remains pending. It is a design/source-path analysis, not a native bug or executed regression-test claim.
- [Result ownership](round16-result-ownership.md) checks imported/direct authority and clarifies that a quorum adapter cannot lower an existing threshold sharing's polynomial requirement.

The architecture still consists of the existing Engine/Marshal plus one App. Callback handlers, worker accounting and canonical application remain concrete internal responsibilities; no new public service or trait was added. Further independent preservation/lifecycle reviews are running, and the requested three-hour interval remains active.


## 09:07 UTC checkpoint: independent cross-review and restored empty-window rule

[Checkpoint evidence](checkpoint-0907.json) records current hashes and successful document/build/diff checks: 32 pages, 252 local links, 19 matching diagrams and 38 blank policy cells. The fresh local browser pass loaded every page/image and exercised search/mobile navigation. Root directly inspected the role table on desktop/mobile in the preserved 08:59 browser snapshot and current diagram06; alignment inspected both current diagrams06/12. Later screenshots are not automatically claimed as pixel-reviewed.

- Round17 [lifecycle](round17-lifecycle-contract.md), [Baton window](round17-baton-window.md) and [pool baseline](round17-pool-baseline.md) reviews retain real resource/authority boundaries without introducing services.
- Round18 [entry clarity](round18-entry-clarity.md), [App responsibility ledger](round18-app-responsibilities.md) and [body API surface](round18-body-api-surface.md) simplify repeated callback prose and identify concrete existing codec/body/config contracts.
- Round19 [first-read walkthrough](round19-first-read-walkthrough.md), [lane identity](round19-lane-candidate-identity.md), [result validation](round19-result-validation.md) and [root delivery/tooling review](round19-root-delivery-and-tooling.md) check the user's implementer path. Local producer mapping comes from Protocol; optional effect reuse must produce the checkpoint for its actual new parent.
- Round20 [core](round20-core-cross-review.md), [execution](round20-execution-cross-review.md) and [native](round20-native-cross-review.md) reviews cross owner boundaries. Existing Stateful targets the block/ancestry Application and Simplex Update contracts, while its concrete DB utilities remain reusable independently.
- Round21 [empty-report restoration](round21-empty-report-restoration.md) records a real omission found after earlier preservation passes: no reports must choose the valid native base before protected adoption. The core table, E2E, diagrams06/12 and future acceptance case now preserve it; raw sum-LCP applies only to a nonempty report snapshot. The earlier preservation report explicitly records this correction.
- The [native citation review](round21-native-citations.md) semantically checks the consensus/reference citation set. The reproducible [local target/signature checker](check_native_sources.py) checks all 121 current-native references across 59 files and seven excerpted declarations; its [receipt](native-source-targets-latest.json) does not claim remote reachability, compilation or automatic semantic proof.

The requested three-hour interval remains active through at least 09:57:26 UTC. Further requirement-preservation and acceptance-feasibility reviews are ongoing; this is not final completion.


## 09:40 UTC checkpoint: final reader/source challenges and standalone links

The core role/callback/assembly and App execution contracts were reread by three independent reviewers, then the root agent reread the full core and primary pool, execution, integration and native delivery contracts. Native `verify` and delivery/ACK control flow was independently traced again.

- [Adopted policy preservation](round21-adopted-policy-preservation.md) restores result-signer independence from a particular ordering QC; [open-policy mapping](round22-open-policy-map.md) maps all 39 baseline questions into the current 38 blank cells without silently choosing defaults.
- [Acceptance feasibility](round22-acceptance-feasibility.md), [diagram semantics](round22-diagram-semantics.md), [code-facing snippets](round23-code-facing-snippets.md) and [minimum assembly](round23-minimum-assembly.md) distinguish existing APIs, private pseudocode and future implementation cases. The App's optional native Activity reporter is no longer shown as mandatory assembly.
- [Responsibility boundaries](round24-state-responsibility-boundaries.md) and [ACK/readiness](round24-ack-execution-readiness.md) separate native state from App execution and durable state.
- [User requirements](round26-user-requirements.md), [native connections](round26-precompletion-connections.md), [App design](round24-precompletion-app-design.md) and [three native boundaries](round27-three-boundaries.md) found no further required semantic correction. ACK observation can be delayed by a cold read; the absence of a direct native ACK dependency is not unconditional node liveness under exhausted resources.
- [Reader path](round25-reader-path.md) records two final simplifications: rename the body API heading around actual Marshal reuse, retaining the old anchor, and link its fetch/subscription details from the core callback rather than repeat them.
- [PNG receipts](visual-receipt-bindings-latest.json) bind all 19 current Mermaid/PNG byte hashes to actual visual inspections: [root architecture](round25-root-architecture-visual.md), [nine E2E diagrams](round25-final-png-qa.md), [native diagrams](round25-native-visual-qa.md), and [App diagrams](round23-final-app-pngs.md).
- [Standalone reference inventory](round27-standalone-reference-inventory.md) and [preview repair](round28-preview-link-repair.md) record three reproduced 404s and their fix. The site now supplies just three linked Markdown artifacts as byte-exact downloads. A fresh browser run checks 32 pages, 19 decoded diagrams, 54 unique local article HTTP targets and 24 linked HTML fragments; search/mobile controls also pass. Four isolated builder cases cover exact/minimal copying and rejected lexical, symlink and directory escapes.

Current document check passes 32 pages, 253 local Markdown links, 19 diagrams and 38 blank policy cells. Build, diff, 121-source-reference/7-declaration check and 19-image receipt binding pass. Root directly viewed the new desktop App entry and mobile callback screenshots. All claims remain scoped to documentation, source and tooling; native/App runtime tests and benchmarks were not run. The goal remains active until at least 09:57:26 UTC and the final audit is recorded.


## Final completion

The final requirement audit and current file/source/browser bindings passed at 09:57:55 UTC, after the requested three-hour interval. The last independent challenges cover [native policy hooks](final-native-policy-challenge.md), [four App event traces](final-app-event-challenge.md) and [evidence navigation](round29-evidence-navigation.md). Actual browser downloads of all three source artifacts completed with bytes matching their repository originals. All 32 browser-checked source pages and built HTML still match their recorded hashes. No remaining documentation correction was found; implementation/proof gaps remain explicitly open.
