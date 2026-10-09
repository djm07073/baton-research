# Round 8: semantic preservation across the App rewrite

Reviewer: `/root/simplification`. Compared all nine requested baseline files at research commit `08cfe68b8b565fff4a0f8119cb36ec9b22062a31` with the current documentation: all three `docs/baton` pages, all four `docs/execution` pages, `docs/tx/interfaces.md`, and `docs/baselines/precut.md`. This was a full prose/table/pseudocode pass, not a keyword-only comparison. Current native source is `6233438985d8249d2b2bc1204191d5d405652288`.

The latest user decision supersedes mandatory public TxPool/Baton/Executor/Storage/BlockService/Orderer layers. This audit preserves their necessary functions and invariants, not their old names or an older absence-of-Marshal premise. Source-specific recipes were checked against the current native pin before restoration. No protocol behavior, codec, signing boundary or backend is selected here.

## Confirmed omissions and minimal restorations

| Baseline requirement | Gap after compression | Restoration |
|---|---|---|
| `baton/interfaces.md`: planning completion checks its original window/context before updating prepared state; stale completion cannot overwrite a newer context | Current direction covered report admission and later native proposal recheck, but did not explicitly preserve the intermediate App prepared-state check | Root restored owner checks for original window/context/current planning attempt in `baton/direction.md`; native actual-proposal recheck remains separate |
| `execution/qmdb.md`: Shared is writer-preferring; an outer guard plus nested reacquisition can deadlock | Current text required one access authority but omitted this concrete trap when implementing that fence | Restored one short paragraph in QMDB branch access; current `glue/src/stateful/db/mod.rs:148-152` and `any.rs:107-118` still confirm it |
| `execution/interfaces.md`: peer certificate decoding is bounded by the eligible roster | Current text retained a bounded envelope and post-decode signer checks but omitted the existing bounded certificate codec entry point | Restored use of the selected epoch verifier's `certificate_codec_config`, excluding its trusted-storage unbounded config; current `certificate.rs:338-345,776-786` |
| `execution/state-sync.md`: Current's retained operation range begins at or below target sync_boundary | Compression stated only that storage and execution boundaries differ | Restored the exact conditional inequality; current `storage/src/qmdb/current/sync/mod.rs:152-153` still requires it |
| `baselines/precut.md`: measure latency distributions/throughput and distinguish repair from transaction failure | Current measurement paragraph retained endpoint/cost comparisons but dropped those explicit distinctions | Restored phrases within the same paragraph; no benchmark performed or new comparison selected |

These are the only confirmed omissions found. The first four preserve correctness/implementation conditions; the fifth preserves the existing measurement contract. Other detail removed during simplification is either represented below, superseded by current Marshal, a source-version correction, or an unselected conditional implementation recipe.

## Requirement-to-current-owner mapping: pool and payload

| Baseline function / invariant | Current owner and location | Assessment |
|---|---|---|
| Admit RPC and peer transactions under the same bounded encoding/signature/domain/static rules | Concrete App pool; `tx/interfaces.md` admission paragraph and backend table | Preserved; no public admit trait required |
| Selected/unselected are logical classes; invalid input is dropped; live state/readiness is distinct from immutable-payload classification | Same pool record/backend; `tx/interfaces.md`, `tx/README.md` | Preserved; no second pool or new policy type |
| Select only eligible selected candidates, respecting predecessor dependencies, visited work/count/full-body bytes | App `Automaton::propose` uses concrete selection; `tx/interfaces.md` | Preserved |
| Stable selected bytes survive concurrent admission, replacement and proposal cancellation; selection is not canonical retirement | App body construction plus existing Marshal custody; tx and body pages | Preserved, including destructive-backend cancellation adaptation |
| Canonical pool maintenance derives from applicable durable outcomes and reconciles missed updates/restart readiness | App durable outcome path into selected pool backend; tx interfaces/survey and execution interfaces | Preserved; no pool ACK gates cut/direction/delivery |
| Transaction ID, body commitment and contextual header ID identify different objects | `tx/interfaces.md`, `baton/README.md`, consensus body page | Preserved explicitly; native private request IDs are not invented in Context |
| Nunchi/Reth/Constantinople are conditional reuse candidates requiring their actual lifecycle/codec/dependency fit | Current retained `tx/README.md` survey and shortened interfaces; current reference version caveat | Preserved as conditional implementation work, not adopted backend behavior |
| Complete body construction, lookup, active fetch, dissemination and durable retention | Existing Marshal mailbox/Relay, buffered broadcast and resolver; App supplies body semantics | Old body-attachment function reused, not lost |
| Header and body may arrive independently; unrelated receipt alone is not executable/report-eligible input | Native eligibility + exact Marshal body + App candidate checks; baton/body pages | Preserved and made callback-path-specific |
| Native DA does not require a speculative execution result; no added DA-certificate barrier for ordinary early work | `baton/interfaces.md`, PreCut candidate section | Preserved |

The old public `TxPool::Source/Selection/Batch/Admission` shape is superseded. Corresponding source-aware ingress, stable bytes, bounded packing and maintenance still exist as concrete App responsibilities. The change does not claim that a bare queue or transaction provider supplies a complete pool.

## Requirement-to-current-owner mapping: ordinary delivery and recovery

| Baseline function / invariant | Current owner and location | Assessment |
|---|---|---|
| Verify/retain native finality/history, backfill gaps and interpret ordinary base ordering | Existing Multimmit Marshal `SchemeVerifier`, catalog, backfill/synchronizer and order code; consensus ordered-input page | Superseded implementation owner; no new App native proof engine |
| Emit only continuous irrevocable inputs; missing included body/history is not an empty slot | Existing Marshal order/delivery; App consumes indexed complete Updates | Preserved; old absent-dense-stream claim removed because source changed |
| Preserve already emitted interpretation and exact delivery identity across recovery | Marshal native cursor/history plus App exact applied-index/block check | Preserved; App may not sort Updates by local preference |
| Deliver independently of report/planning tasks; canonical work does not need advisory approval | Marshal Reporter<Update> and App canonical worker | Preserved |
| Track durable completion, recover cursor and redeliver idempotently | Existing Exact token/Marshal ACK cursor plus App linked durability records | Preserved with actual native API; no proposed CommitResult/cursor framework |
| Result state/output/applied identity/provenance must recover consistently before ACK | App state/backend integration; execution interfaces/QMDB and E2E canonical | Preserved; Marshal cursor persistence remains separate |
| Startup restores valid canonical execution base and retained body obligations before live work | App recovery lifecycle + existing native Engine/Marshal startup; E2E recovery and callback page | Preserved; now accounts for verify calls during Engine::open |
| Query/result/worker/sync retention may outlive logical pruning | App references plus native Marshal retention APIs; QMDB and recovery pages | Preserved; no scheduler generation revokes native custody |
| Full Baton interpretation must survive proposal, extension and view recovery | Still-open native authenticated policy bridge and matching Marshal interpretation | Preserved as open proof/implementation work, not falsely supplied by ordinary Update |

The former `Baton::on_finality -> OrderedRange -> Executor::commit -> CommitResult` public path is intentionally gone. Current Marshal supplies ordinary proof/order/backfill/delivery machinery directly. Exporting evidence to a remote consumer remains a separate open contract: a trusted local Update is not a portable peer finality proof. Restoring an App Orderer would duplicate the current source rather than restore a missing function.

## Requirement-to-current-owner mapping: scheduling and reports

| Baseline function / invariant | Current owner and location | Assessment |
|---|---|---|
| Keep completed/current F; sort only authenticated eligible unstarted pending work within context/frontier/horizon | Concrete selected scheduler; `baton/direction.md`, execution and PreCut pages | Preserved |
| A/C/B before C starts gives ABC; after C starts preserve AC and yield ACB if eligible | Same scheduler examples and baseline | Preserved; no arrival-driven reexecution or hypothetical-B wait |
| Metadata admission does not start a state-dependent child before its exact predecessor/resource readiness | App owner candidate state and claimed job; callback/execution/PreCut pseudocode | Preserved and made race-safe in round 7 |
| Block identity alone does not identify an execution node after different prefixes | App execution tree/context; execution interfaces and QMDB | Preserved |
| Reports use the same F++sort pending intention; equal total input alone need not give equal reports | App Baton report builder; direction and E2E leader | Preserved |
| Reports bind epoch/view/history/actual canonical parent/rule/window/frontier; one eligible original report per identity | App Baton admission under existing crypto/P2P | Preserved |
| Stable original report sequences; once-closed snapshot; owner admission distinct from worker verification/packet arrival | App report owner; direction and E2E leader | Preserved |
| Close on first processed 4f+1 admissions or fixed deadline, m<=4f+1; arrivals do not extend deadline | Existing Clock + App window state | Preserved |
| Complete bounded admissible candidate evaluation before publishing prepared choice | App planning worker and owner | Preserved; eager strategy execution placement restored in round 6, stale completion check restored here |
| Longest valid nonempty entire prefix with at least 2f+1 original supporters; otherwise raw sum-LCP | App direction selection; direction arithmetic/table | Preserved; per-position votes and trimmed scores are not substituted |
| Report support proves intentions, not completed reusable work or native inclusion | Direction explanation and consensus integration gap | Preserved |
| Cut never waits for reports/timer/optimizer/direction ACK; valid actual-parent base before adoption | Future native integration reads prepared App state; direction/native decision pages | Preserved |
| Authenticated adoption protects exact leading sequence after immutable frontier, not mere membership | Future native policy validation/preservation and Marshal interpretation | Preserved as unresolved proof work |
| Late reports/planning/native pool growth cannot rewrite an authenticated proposal | Native proposal owner; E2E leader and consensus decisions | Preserved |
| Local cycle can restart without every node finishing prior execution; no direction readiness quorum | App Baton control cycle; direction dissemination | Preserved |
| Non-leader checks leader/context and reuses exact parent; advisory precedence/tail policy remains open | App selected scheduler and execution tree | Preserved; no new reschedule API or automatic override |

Four unadopted defaults stay open: per-block signing, incumbent-first tail, inline policy bytes and finite-prefix permutation continuation. Removal of public `Baton::plan/on_block/on_context/on_report/on_direction/on_planned/prepared_policy/on_execution/on_commit` signatures removes interface ceremony, not these functions. Optional scheduler progress is App state, not a new approval protocol.

## Requirement-to-current-owner mapping: execution and QMDB

| Baseline function / invariant | Current owner and location | Assessment |
|---|---|---|
| Transaction interpretation/tree management belongs to application, not QMDB or native AppExecutor | App execution; execution README and interfaces | Preserved |
| Exact execution base/runtime/rule/ordered prior input governs reuse; missing/unfinished parent remains pending | App job/context and concrete handles | Preserved |
| Completed effects/outputs separate from selected root preparation; no obligatory hash for each abandoned attempt | App transaction worker + selected QMDB merkleization | Preserved |
| Root exists before signing complete result; local generations/permits are not shared signature fields | App result handlers; execution interfaces | Preserved |
| Existing sealed-parent forks; no invented unsealed-parent clone/fork | Concrete QMDB batches; QMDB root-deferral section | Preserved |
| Rootless replay/overlay requires exact retained effects and valid anchor; consuming one draft can lose the only representation | App effects retention and concrete batch ownership | Preserved; replay/overlay remains optional |
| Same values/order may yield different operation histories under different sealing/normalization; selected commitments need a common rule | App deterministic preparation; QMDB section | Preserved and still an open implementation choice |
| Canonical AB cannot apply one sealed ABC and hide C; reconstruct exact boundary or reexecute | App canonical reconciliation/QMDB | Preserved |
| Compatible descendants survive only actual storage ancestry and exact context; sibling logical equality is insufficient | App tree + existing QMDB applicability | Preserved |
| All required unapplied ancestor handles remain alive; a leaf alone is insufficient | Existing strong/weak QMDB ownership plus App retention | Preserved |
| Live reads fall through to current DB; validation and access must share authority across clones | App access fence + concrete QMDB reads | Preserved; nested Shared reacquisition caution restored here |
| Stale result invalidation differs from stopping CPU/live DB access; immutable work may outlive waiter | App current attempt/context and runtime handles | Preserved; no all-background-task completion barrier introduced |
| One canonical writer for direct/import; no advisory cancellation of by-value mutation | App state owner/concrete DatabaseSet | Preserved |
| Apply/readable state differs from covering finalize/barrier durability; failed mutable DB cannot be reused | Current QMDB call sequence and App recovery | Preserved with current API correction |
| No tuple-wide merkleize/single root; selected per-DB results need bound result/output interpretation | Concrete batch sealing and App commitment rule | Preserved |
| Guarded queries bind value/proof/root to retained checkpoint/readiness; operation inclusion is not current absence or execution certification | QMDB query paragraph and E2E results | Preserved; query scope remains open |
| Metadata atomicity covers its own store, not QMDB + separate journal; retention/recovery linkage remains App work | Existing journal/metadata utilities under App owner | Preserved; no replacement WAL/cursor engine |

Old `Executor::execute/commit/recover` and `Storage::prepare/apply/recover/read` names map to these internal actions and existing DB calls. The Bank/account model is still unselected application semantics. New trait declarations would not implement any missing operation.

## Requirement-to-current-owner mapping: certificates and state sync

| Baseline function / invariant | Current owner and location | Assessment |
|---|---|---|
| Own direct execution/validation evidence + exact irrevocable inputs/base/runtime + prepared result before signing | App execution result handler | Preserved |
| f+1 distinct eligible epoch identities on one full subject; root equality/transport counts are insufficient | App collection/verification over existing crypto | Preserved |
| Incomplete signatures do not pause direct work or native cut; delivery durability may progress independently | App canonical path and result protocol | Preserved, with ACK-window compatibility added in round 6 |
| Imported work cannot become own direct evidence; retain original certificate/provenance through recovery | App state/results | Preserved |
| Serve/query exact retained certification separately from material/read/durable availability | App result handlers and retained QMDB/output state; E2E results/state sync | Preserved without a public ResultService or query trait |
| Typed peer transport identity does not prove original signer eligibility; different attestations cannot share one buffered-object key | Existing P2P/optional buffer + App exact-subject checks | Preserved |
| Optional collector counts transport responses before validation; result threshold is not collector count | App validated signer set; execution recipe | Preserved; pull lifecycle remains conditional |
| Scheme assembly is not verification; no duplicate roster indices; scheme PoP/original-signature requirements remain | Existing certificate primitives + App validation | Preserved; bounded peer codec entry point restored here |
| Native N5f1 n-f threshold cannot be copied unchanged for f+1 execution results | App chosen compatible scheme/quorum integration | Preserved; no native threshold change selected |
| Certified import is normal-path option; continue direct work until certificate AND applicable material are ready | App execution/state-sync orchestration | Preserved |
| Certificate arriving before exact irrevocable input stays pending/recovers ordering | App exact target validation | Preserved |
| QMDB Target is caller-trusted ops root/range; same-history advancement is not arbitrary branch switching | App authorized target + existing sync engine | Preserved |
| Current canonical root differs from ops root; reuse OpsRootWitness for the relationship | Selected Current integration if chosen | Preserved |
| Reached-target notification is not completed persisted DB; check final target/result/outputs after returned DB | App sync completion handling | Preserved |
| Concurrent candidate needs separate storage ownership; same partitions are not isolation; Current lower bound is storage-specific | App storage handoff + QMDB sync | Preserved, including exact sync_boundary condition restored here |
| DB P2P attachment is enqueued serving replacement, not writer handoff/readiness acknowledgement | Existing Source/serving handles + App handoff | Preserved |
| Imported state/floor/delivery coverage must match before readiness/ACK; partial local branch is not another delta's base | App single writer + existing Marshal floor APIs | Preserved and strengthened for current startup-floor authority/window resets |

Detailed collector retry slots, staged-index API trivia, generic associated-type equalities and selected ecosystem compute examples are source-specific conditional recipes. They are not adopted independent application functions; current pages retain the necessary caller checks and links without mandating those optional paths.

## Requirement-to-current-owner mapping: PreCut and evaluation

| Baseline invariant | Current location | Assessment |
|---|---|---|
| Independent PreCut implementation with no Baton instance/reports/direction/native policy | `baselines/precut.md` and entry architecture | Preserved |
| Same pool/body/backend/root/resource/result/import contracts across Original/PreCut/Baton | Baseline architecture and comparison section | Preserved |
| Ordinary native order stays ordinary; early proposals/frequent cuts are separate sensitivities | Same comparison section; current Marshal source | Preserved |
| Confirmed continuous input is repair trigger; tentative-proposal repair remains undecided | Baseline repair section and scheduler direction | Preserved |
| Reuse prefix/repair suffix, not unconditional whole-chain reexecution; ABC/AB, AC/ABC, AXBC examples | Baseline repair table and QMDB | Preserved |
| Matched deterministic output/root oracle; separate ordering/result/state-finalization/durable endpoints and total costs | Baseline measurement section and reference verification cases | Preserved; latency/throughput/failure distinctions restored here |
| No baseline implementation, E2E result, performance win or native Baton proof claimed | Baseline status/TODO and reference verification | Preserved |

## Source-version corrections that must not be restored

- The baseline's `534af0e` absence-of-Multimmit-Marshal and unimplemented ordinary dense-export statements do not describe `6233438`. Current Marshal owns that ordinary machinery.
- The older `DatabaseSet::finalize(sealed)` recipe is replaced by current `apply(sealed)` then `finalize()` and covering barrier rules.
- Do not restore the old `N5f1::f_plus_one` API assertion where the current pin does not expose that method. The f+1 application condition itself remains required.
- Old duplicate/invalid `Signers::from` panic wording does not match current fallible `Signers::new/TryFrom`; current validation/deduplication requirements remain.
- Indexed release and ecosystem pins remain historical compatibility evidence, not one compiled type graph or selected production backend.

## Result

All adopted functions reviewed have a current owner. Five localized omissions were restored without recreating public layers; no additional tx change was justified. Existing primitives cover native custody/order/delivery, storage algorithms and crypto machinery. App still owns transaction semantics, scheduling, exact execution identity, result interpretation and recoverable application-state linkage. Open native Baton adoption/continuation and App policy choices remain open.

Validation is documentation/source review plus `git diff --check`; no protocol test or benchmark was run.

Correction recorded during the later source audit: root initially inspected `Floor` alone and incorrectly removed the startup generation requirement from the reader page. `Floor` and `Update` have no generation field, but native `Start::Floor { floor_generation, floor }` does. The caller must authenticate the anchor and bind the emitted frontier and positive monotone `floor_generation` to the imported App snapshot (`marshal/config.rs:171-186`). The requirement has been restored in `execution/state-sync.md` and made explicit in `consensus/ordered-input.md`; it is distinct from App-local worker generations. The fingerprints below describe the earlier checkpoint, before this correction.

## Compared content fingerprints

Captured 2026-10-09T07:54:21+00:00.

| File | Baseline SHA-256 | Current SHA-256 |
|---|---|---|
| `docs/baton/README.md` | `a5fc7e6175b6402c399fbc3761f984d8c463004e1d4f0937ed870cd350fb7743` | `4fc0f382071023391145df6db72f3f0f225abd03776386ab6371f0a5bc32a719` |
| `docs/baton/interfaces.md` | `1180631c37c446a4ed429c1cf63b147127dbf56de6ae56aab3746ec24d78cc24` | `2fb8ad610376d74e6b8af622b4dd744f203bb78012480366ecb5a9f711661d0d` |
| `docs/baton/direction.md` | `f02de51cc93a28f10a27fb3cb13be76f34d5802f40a9b7abde626775c2937c6d` | `16288ea14ccf80d1b7ec3542d61646ef95a7a65811788a6c2972bf24cade60ec` |
| `docs/execution/README.md` | `de6c18b7bd92df8319ef85cca8b1cae56824c296e28c99984f8d1f88bd4d2300` | `f316f388176a51519cbf63d6eb3eee5bec94e2737441698855f772c0eca03273` |
| `docs/execution/interfaces.md` | `5e60c6b445a9e5e141613ffc890ec7c9f997abe0351930cf6f00f983ed6fdce1` | `eb1c38b1a34f484d537ad0c46b534448cfc1bceedf9db3359e77bfb53d1b2128` |
| `docs/execution/qmdb.md` | `85148b26f3616f2a8251e3b49c0194d8488a4f838809a487a4e5e21d636cfdd0` | `601119b6bc30944bbaf5cba53d9908ac66978faa9ae5e1a502f5e8d5eb3afefe` |
| `docs/execution/state-sync.md` | `43d98720e4abfda32c1310fb22cbd191d813e1ca826ac6a054191ac3383205e8` | `4217fa3926cd72f652cc8c27890275ddaa5793e299ed168a4d290cc6ec77718c` |
| `docs/tx/interfaces.md` | `65304d3f086e0f274cf9fc22ea6ae9e8059712eafe1f5a84fca1182fa2b3fb24` | `000d26910db81d098c24bb15bde475a83561c0474e462718a2226767a728a7c2` |
| `docs/baselines/precut.md` | `f1a63b4cd3f571606d1fe6ed73a855dc82ee11c4f3c125e88b9734c843757bdd` | `672cb053c048d7c99c567084c450c2d38e7c498af561a218f60e0d3e2360e74f` |
