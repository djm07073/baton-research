# Round 21: adopted-policy preservation ledger

This is a fresh semantic comparison of baseline `08cfe68b8b565fff4a0f8119cb36ec9b22062a31` against the current reader documents and current `AGENTS.md` / `BATON_HANDOFF.md`. It does not rely on the prior rounds' pass conclusions. The complete baseline `docs/baton/{README,interfaces,direction}.md`, `docs/execution/{README,interfaces,qmdb,state-sync}.md`, `docs/tx/interfaces.md` and `docs/baselines/precut.md` were read, including their examples and open-decision tables. Current canonical pages and the relevant E2E/consensus/verification pages were read directly.

Latest ownership precedence: `AGENTS.md:13–19` and `BATON_HANDOFF.md:7–11` replace old public layers and ordinary App-owned order reconstruction with one App and existing Multimmit Marshal. They do not remove the scheduling, result, execution or retention semantics listed below. Current source pin is `6233438985d8249d2b2bc1204191d5d405652288`; the baseline's older API recipes are not presumed current.

## Confirmed omissions and disposition

1. **Result signers need not be members of the particular ordering QC.** `AGENTS.md:43` explicitly retains this rule. Current result pages required eligible epoch identities and irrevocable order but omitted the independence from a particular QC; the old policy could be accidentally narrowed during implementation. Restored one sentence in `docs/execution/interfaces.md:60`. This does not remove order verification or change signer eligibility, quorum, key or codec choices.
2. **Zero-report native-base behavior**, discovered in Round 20, is now restored. Baseline `docs/baton/direction.md`, the leader-stage table, says “No reports / no prepared valid candidate.” Current `docs/baton/direction.md:56–57`, `docs/e2e/leader.md:24–27,45,85` and `docs/reference/verification.md:32` now distinguish an empty snapshot from the nonempty raw-sum fallback. The empty sum is not permission to select an arbitrary candidate. Root/alignment/native agents own those changes; no duplicate edit here.

No other confirmed adopted behavioral omission was found in this fresh pass. This statement is scoped to the inventory below, not a protocol or implementation proof.

## Ownership, pool and callback integration

| Adopted requirement | Current exact location and owner | Disposition |
|---|---|---|
| One application owns pool, concrete PreCut/Baton choice, transaction execution and state; use existing external callbacks | `docs/baton/README.md:3–23`; `docs/execution/README.md:3–5` | Latest requirement preserved; no public framework required |
| PreCut and Baton use the same execution/backend, rather than separate execution engines | `docs/baton/direction.md:3–16`; `docs/baselines/precut.md:3–5,39` | Preserved |
| Native signing, DA, voting and finality remain native; ordinary history/order/custody/delivery already belong to Marshal | `docs/baton/README.md:15–16`; `docs/consensus/ordered-input.md:7,39–46` | Old logical responsibilities preserved under current supplied owner |
| Admit RPC/peer input using the same validity and immutable-payload classification; selected/unselected are logical classes, invalid input is dropped | `docs/tx/interfaces.md:9,13` | Public `admit` removed; App behavior preserved |
| Select only eligible local candidates under dependencies and work/count/full-body byte bounds; producer context is not merged execution parent | `docs/tx/interfaces.md:10,15` | Preserved |
| Selection/proposal cannot canonically retire transactions; retain stable bytes and handle cancellation/destructive backend selection | `docs/tx/interfaces.md:15,43,47`; `docs/baton/interfaces.md:26` | Preserved without a new proposal callback |
| Canonical pool maintenance follows durable outcomes; no pool ACK or scheduler approval barrier | `docs/tx/interfaces.md:11,29`; `docs/baton/interfaces.md:114–115,143` | Preserved; lost maintenance must reconcile before readiness is trusted |
| Preserve tx → body → exact native header/context → applied-output identity | `docs/tx/interfaces.md:31`; `docs/baton/README.md:38` | Preserved, with current digest distinction |
| Reuse fitting real pool machinery, not a queue presented as a complete backend | `docs/tx/interfaces.md:35–49` | Preserved as conditional source adaptation; backend choice stays open |
| Joined exact body/header/context, validity and custody qualify speculation; raw receipt or a body hit alone is insufficient | `docs/baton/interfaces.md:36–67`; `docs/baselines/precut.md:52` | Supplied Marshal replaces old joining service; App checks remain |
| Successful verify is not execution completion or an automatic other-lane arrival; local pre-sign, remote and recovery uses differ | `docs/baton/README.md:46–64`; `docs/baton/interfaces.md:61,67` | Latest requirement preserved with current remote-closure exception |
| No DA-certificate barrier is added solely to speculate; producer ancestry/authentication and actual execution readiness still apply | `docs/baselines/precut.md:52,87`; `docs/baton/interfaces.md:65,67` | Preserved |
| Recovery must answer custody before Engine open completes, then re-evaluate retained candidates after readiness | `docs/baton/interfaces.md:11–15` | App lifecycle replaces old generic recover action |

## Ordinary scheduling and execution identity

| Adopted requirement | Current exact location and owner | Disposition |
|---|---|---|
| Keep completed/current valid local prefix F; sort only eligible unstarted pending work after the immutable frontier and within the horizon | `docs/baton/direction.md:20–26` | Preserved literally as `F ++ sort_G(S_pending)` |
| Arrival is not the tie-break; ancestry/dependencies remain valid; comparator/tie/identity remain open | `docs/baton/direction.md:26,105–106` | Preserved, no default comparator introduced |
| A running, C then B before C starts gives ABC; B after C starts preserves AC and gives ACB | `docs/baton/direction.md:28–35`; `docs/baselines/precut.md:85` | Both traces preserved |
| Arrival while parent runs updates the pending queue only; a dependent child waits for its valid exact checkpoint | `docs/baton/direction.md:35`; `docs/execution/interfaces.md:13,18–22` | Preserved |
| If B is unknown, valid AC need not wait for hypothetical B; arrival alone does not reexecute started C | `docs/baton/direction.md:35`; `docs/baselines/precut.md:85` | Preserved |
| Equal rule/context/F/pending gives equal intent; equal total known blocks alone does not | `docs/baton/direction.md:37`; `docs/e2e/leader.md:43` | Preserved |
| F is not canonical; new continuous confirmed input can require exact-parent repair | `docs/baton/direction.md:37–43`; `docs/baselines/precut.md:91–106` | Preserved; current trigger is Marshal Update |
| Repair on unfinalized cut proposals is not silently adopted | `docs/baton/direction.md:37`; `docs/baselines/precut.md:106` | Open choice preserved |
| Advisory direction is authenticated to current leader/context; precedence over conflicting started work remains undecided | `docs/baton/direction.md:83–85` | Preserved; no cancel/reexecute default |
| Execution identity includes exact predecessor/input/base/runtime; a producer-header parent or same block digest does not prove reuse | `docs/execution/interfaces.md:9–13`; `docs/execution/qmdb.md:87,107` | Preserved |
| A→B→C to A→B→D may reuse matching completed AB; A from X cannot reuse A from S0 | `docs/execution/qmdb.md:87–107` | Preserved concrete branch example |
| Metadata admission is separate from dispatch; duplicate notification cannot launch the same active attempt twice | `docs/baton/interfaces.md:65,67,72–87`; `docs/execution/interfaces.md:11,18–22` | Clarified current owner/attempt/resource claim, no extra actor |
| Completion must be completed valid work for the current exact attempt; stale/partial/canceled/duplicate work is not reusable | `docs/execution/interfaces.md:24–28`; `docs/baton/interfaces.md:73–87` | Preserved and made implementable |
| Worker failure/failed launch settles ownership once; waiter cancellation alone is not termination or safe resource release | `docs/baton/interfaces.md:87`; `docs/reference/verification.md:34` | Preserved without selecting retry/quota policy |
| Required custody/canonical work cannot be indefinitely starved by speculation/report crypto/planning | `docs/baton/interfaces.md:120`; `docs/reference/verification.md:23` | Necessary progress invariant retained; concrete capacity policy open |

## Reports, planning and control cycle

| Adopted requirement | Current exact location and owner | Disposition |
|---|---|---|
| Reports are authenticated intentions, not execution history, progress, completion, roots, result proofs or direction votes | `docs/baton/direction.md:47,73`; `docs/e2e/leader.md:43` | Preserved |
| Dispatch and reports use the same fixed prefix plus eligible sorted pending sequence/context/frontier/horizon | `docs/baton/direction.md:20–26,47`; `docs/e2e/leader.md:43` | Preserved through shared rule, no fresh all-input sort |
| Bind exact epoch/view/history/canonical parent/rule/window/frontier and count each eligible identity once | `docs/baton/direction.md:47,52` | Preserved; conflicting-report policy remains open at line 107 |
| Remote peers need authenticated window context; a leader-local timer is not announcement | `docs/e2e/leader.md:16–20`; `docs/baton/direction.md:103` | Preserved as actual announcement step; message codec is open |
| Worker crypto completion and snapshot-owner admission are different events | `docs/baton/direction.md:52,60` | Preserved |
| Fix deadline once; close on the first processed threshold/deadline event; count at most 4f+1 valid distinct original reports | `docs/baton/direction.md:51–53,60`; `docs/e2e/leader.md:45` | Preserved; no network-arrival timestamp assumption |
| Later/excess reports and crypto completion after closure stay out; arrivals do not extend deadline or rewrite signed reports | `docs/baton/direction.md:60,73`; `docs/e2e/leader.md:43–45` | Preserved |
| Evaluate a bounded admissible full-candidate set to completion; validate ancestry, predecessor closure and actual context | `docs/baton/direction.md:54,60,64,95` | Preserved; unfinished search cannot claim completed longest selection |
| Primary selection maximizes length of a valid nonempty entire prefix with 2f+1 original same-context supporters | `docs/baton/direction.md:55,64,66–73` | Preserved, with full-prefix versus per-position distinction |
| Primary prefix length beats a larger sum-LCP; raw sum fallback is only for nonempty snapshots with no qualifying prefix | `docs/baton/direction.md:56,64,68–73` | Preserved; sum is not trimmed by dropping f values |
| No reports or no prepared valid candidate means actual-parent valid native base before adoption | `docs/baton/direction.md:57`; `docs/e2e/leader.md:24–27,45,85` | Round 20 omission restored |
| Candidate completion cannot inject/reorder reports to manufacture support | `docs/baton/direction.md:60,73` | Preserved |
| 2f+1 support implies at least f+1 honest intentions, not completed work/reuse/native inclusion | `docs/baton/direction.md:73` | Preserved scoped claim |
| Tail, tie, hysteresis, candidate universe/horizon, budgets, freshness and dissemination targets stay open | `docs/baton/direction.md:73,99–113` | No old recommended default became adopted |
| Planning stays off cut/admission owners, including synchronous work at strategy creation/poll | `docs/baton/direction.md:60–62`; `docs/baton/README.md:80` | Existing runtime mechanisms retained; no second task framework |
| Stale planning completion cannot replace current prepared context; native actual-proposal recheck is separate | `docs/baton/direction.md:60`; `docs/e2e/leader.md:59–68` | Prior planning-context restoration is present |
| No direction receipt vote, ACK or Ready quorum; leader-local cycle does not wait for every executor to finish | `docs/baton/direction.md:58,77`; `docs/e2e/leader.md:34–37` | Preserved |

## Native protected-prefix boundary

| Adopted requirement | Current exact location and owner | Disposition |
|---|---|---|
| Keep native Multimmit fault model, tip extraction, extension, voting and recovery | `docs/consensus/README.md:19`; `docs/baselines/precut.md:36`; `docs/consensus/decisions.md:12–13` | Preserved |
| Producer Automaton context/propose/verify are not leader-window/cut-policy hooks | `docs/baton/direction.md:89–93`; `docs/consensus/decisions.md:7` | Preserved missing-integration boundary |
| Freeze prefix/policy/rule in authenticated proposal bound to actual parent/history/frontier/context | `docs/consensus/decisions.md:9–10`; `docs/e2e/leader.md:63–77` | Required future behavior retained, not claimed implemented |
| Late reports/planning or larger native pools cannot change an already signed proposal interpretation | `docs/e2e/leader.md:75–77`; `docs/consensus/decisions.md:10` | Preserved |
| Selected valid p must be exact leading prefix of final O after the same frontier/input state/runtime; membership alone is insufficient | `docs/baton/direction.md:95`; `docs/consensus/decisions.md:11–12` | Preserved A1/X/B1 counterexample |
| Mandatory predecessor missing makes candidate invalid; do not discard extra native inputs to force p | `docs/baton/direction.md:95` | Preserved |
| Report closure is not protected adoption; before adoption base fallback/no-wait, after adoption no dropping/reinterpretation | `docs/baton/direction.md:97`; `docs/consensus/decisions.md:14` | Preserved |
| Adoption/availability, native sufficiency, continuation and recovery proof remain open; a commitment field alone is insufficient | `docs/baton/direction.md:93–97`; `docs/consensus/decisions.md:7–15` | Preserved |
| Preserve emitted exact order and authenticated interpretation across extension/recovery; gaps/missing content are not empty | `docs/consensus/ordered-input.md:19,31,50–52`; `docs/consensus/decisions.md:12–13` | Existing ordinary Marshal owner plus future policy-specific obligation |
| App cannot implement protected order by sorting finalized Updates | `docs/baton/README.md:84`; `docs/consensus/ordered-input.md:52` | Preserved |

The historical local-prefix uniqueness observation depended on one closed `m ≤ 4f+1` snapshot. Current reader pages retain that bound and do not claim uniqueness across larger pools or different snapshots. Omitting an unused theorem is not removal of a required runtime behavior. Its scope remains explicit in `BATON_HANDOFF.md:127`. Likewise, historical ordinary-position/DA-anchor analytical evidence remains historical; the current guide does not promote it into an executed trace or full Baton proof.

## Execution, storage, certification and recovery

| Adopted requirement | Current exact location and owner | Disposition |
|---|---|---|
| Transaction computation yields completed effects/outputs; roots are prepared when selected/useful and before full result signing | `docs/execution/README.md:25`; `docs/execution/interfaces.md:58`; `docs/execution/qmdb.md:11,48` | Preserved; no mandatory root per abandoned attempt |
| Reuse concrete QMDB/DB handles without requiring Stateful Application/full actor | `docs/execution/README.md:27`; `docs/execution/qmdb.md:38,63` | Preserved and concrete Simplex/Multimmit boundary qualified |
| Rootless branch access is not an upstream unsealed-parent fork; use retained exact effects plus valid anchor or a selected overlay | `docs/execution/qmdb.md:73–81` | Alternatives preserved; no mandatory generic read-view engine |
| Retain effects before consuming the only unsealed draft; shared logical values do not prove matching operation roots | `docs/execution/interfaces.md:46`; `docs/execution/qmdb.md:81–83` | Preserved |
| Deterministic canonical operations/batching/root choice remains necessary but unspecified | `docs/execution/qmdb.md:57,83`; `docs/execution/README.md:42–44` | No per-block checkpoint/signing default introduced |
| Root alone/bounds alone do not bind execution prefix, runtime, outputs or direct provenance | `docs/execution/qmdb.md:9,11,69,123`; `docs/execution/interfaces.md:58–60` | Preserved |
| Shared DB reads can fall through to live applied state; generations do not prevent invalid reads | `docs/execution/qmdb.md:65–69,131` | Preserved with same-authority, lock and tuple-coherence limitations |
| Retain still-required ancestors; later compatible descendants can survive canonical promotion; conflicting branches lose adoption authority | `docs/execution/qmdb.md:69,107–109` | Preserved; physical retention separate from logical pruning |
| One canonical writer covers direct/import; no advisory cancellation of mutation or bypass using another clone | `docs/execution/README.md:29`; `docs/execution/qmdb.md:65,125`; `docs/execution/state-sync.md:11` | Preserved |
| Commit exact finalized prefix; ABC cannot be applied when only AB is canonical; missing AB checkpoint requires materialization or reexecution | `docs/execution/qmdb.md:118,123`; `docs/baselines/precut.md:95–97` | Preserved, including optional explicit effect validation at new parent |
| Recheck exact predecessor after async preparation; no late completion can promote another canonical branch | `docs/execution/interfaces.md:38–43`; `docs/execution/state-sync.md:11` | Preserved |
| Mutable storage failure/lost by-value handle is fatal for that instance, not ordinary retry; missing durability evidence is not rollback evidence | `docs/execution/qmdb.md:125,129`; `docs/baton/interfaces.md:31` | Preserved under current APIs |
| Current apply/finalize/covering barrier completion differs from mere readable state; metadata alone is not cross-store atomicity | `docs/execution/qmdb.md:49–55,125–129` | Old API recipe intentionally updated, semantic durability retained |
| State, outputs, exact applied identity and direct/imported provenance must recover consistently | `docs/execution/interfaces.md:40–48`; `docs/execution/qmdb.md:127–129` | Preserved; concrete linkage still App work |
| Physical reclamation respects worker/query/recovery/certificate/material/sync retention | `docs/execution/qmdb.md:109,121`; `docs/e2e/results.md:40` | Preserved, no retention numbers selected |
| Queries bind value/proof/root/checkpoint readiness; reader handles are not historical snapshots, proof is not execution cert/durability | `docs/execution/qmdb.md:131–133` | Preserved and made more precise |
| Primary state finalization is exact irrevocable order/base plus f+1 valid distinct eligible epoch signatures on the same full statement | `docs/execution/interfaces.md:58–60`; `docs/e2e/results.md:36–38` | Preserved |
| Honest direct signers require their own completed execution/validation and prepared commitment; no particular ordering-QC membership requirement | `docs/execution/interfaces.md:58–60` | QC independence omission restored this round |
| Stable signed subject binds epoch/range/ordered inputs/base/runtime/rule/result/output/material, not local worker generations or writer permits | `docs/execution/interfaces.md:58`; `docs/execution/qmdb.md:11` | Preserved |
| Matching roots/transport counts are insufficient; signer identities are eligible, validated and deduplicated | `docs/execution/interfaces.md:60,72–81` | Preserved using existing crypto primitives |
| f+1 cannot be obtained by copying native n-f/DA/nullification threshold material unchanged | `docs/execution/interfaces.md:81` | Preserved and current-source qualified |
| No standalone result relay/service or Baton approval; App peers exchange statements/certificates/material directly | `docs/execution/interfaces.md:56`; `docs/baton/interfaces.md:135,143` | Old Executor-owned semantics preserved inside App |
| Direct execution/apply/ACK need not wait for f+1 certification; fewer signatures do not stop valid direct work/native cut | `docs/execution/interfaces.md:60,66`; `docs/baton/interfaces.md:135` | Preserved |
| Certification, material availability, readable state and local durability are distinct | `docs/execution/interfaces.md:62`; `docs/e2e/results.md:40` | Preserved |
| Common statement boundaries and required retained output/material affect eventual usable completion, without selecting per-block/chunk policy | `docs/execution/interfaces.md:64–66`; `docs/e2e/results.md:38–40`; `docs/execution/qmdb.md:83,109` | Requirements retained; concrete common boundary/retention policy open |
| A longer-range certificate cannot certify a sliced shorter range; ACK batching cannot require beyond-window delivery before any progress | `docs/execution/interfaces.md:64–66` | Explicit safeguards preserved |
| Normal validators may import; continue direct work while cert/material unavailable; a cert cannot settle unresolved order | `docs/execution/README.md:35`; `docs/execution/state-sync.md:3–5` | Preserved |
| Stop/fence unfinished work only when cert and usable applicable material are verified and shared writer can adopt safely | `docs/execution/state-sync.md:5,9–12` | Preserved; switch policy remains open |
| Imported work is not own direct execution; relay original certificate; sign later directly executed range; recover provenance | `docs/execution/interfaces.md:62`; `docs/execution/state-sync.md:13–15` | Preserved |
| QMDB sync target is caller-trusted storage root/range; full execution authority/output binding remains App work | `docs/execution/state-sync.md:19–29` | Preserved; reuse Current witness conditionally |
| Target updates must share authenticated append-only history; progress notifications are not completed reconstructed DB/readiness | `docs/execution/state-sync.md:25,29–31` | Preserved |
| Concurrent sync candidate needs separate storage ownership; same partitions are not isolated; serving attachment is not writer-ready ACK | `docs/execution/state-sync.md:33–35` | Preserved |
| Marshal floor does not install App state; exact floor/snapshot authority, startup authentication and retained old updates need coordination | `docs/execution/state-sync.md:39–43` | Current-source floor-generation requirement retained, not confused with worker generations |

## Delivery and comparison endpoints

| Adopted requirement | Current exact location and owner | Disposition |
|---|---|---|
| Continuous exact native ordered input is independent of reports/planning; unresolved/missing included input cannot be guessed empty | `docs/consensus/ordered-input.md:7,19,50`; `docs/baton/interfaces.md:118–120,131` | Current Marshal replaces old App orderer; requirement preserved |
| Synchronous report means retained local intake, not execution or disk completion; canonical-first blocks work without earlier speculation | `docs/baton/interfaces.md:91–120` | Preserved through actual Update API |
| ACK follows matching durable application, may follow reuse without rerunning transactions, and does not gate native finality | `docs/baton/README.md:72–74`; `docs/consensus/ordered-input.md:23–31` | Preserved exact endpoint |
| Redelivery checks exact index/block and avoids duplicate effects; App applied identity and Marshal cursor are separate durable stores | `docs/execution/interfaces.md:30–48`; `docs/execution/qmdb.md:127–129` | Preserved; no second generic cursor engine |
| Marshal ordinary window is bounded, accepted Updates/tokens cannot be lost, Backoff is not retry, Exact clone/drop semantics matter | `docs/baton/interfaces.md:129–133` | Latest current-source requirement preserved |
| Independent PreCut has no Baton/report/direction/protected policy; ordinary native order/cadence unchanged | `docs/baselines/precut.md:3–5,41,122` | Preserved |
| Compare Original, PreCut and Baton under same backend/resources/endpoints and result-sync capabilities | `docs/baselines/precut.md:110–124`; `docs/reference/verification.md:40` | Preserved |
| Repair is incremental exact-parent work, not entire-chain rerun or ordinary transaction revert | `docs/baselines/precut.md:93–106,124`; `docs/reference/verification.md:34` | Preserved |
| Early proposals/frequent cuts are separate sensitivity experiments; advisory-only Baton does not prove protected integration | `docs/baselines/precut.md:122` | Preserved |
| Measure ordering, execution result, primary certification and durable/read endpoints separately; include total work and compare exact-input outputs | `docs/baselines/precut.md:124`; `docs/reference/verification.md:40` | Preserved; benefit remains an unmeasured hypothesis |
| Planned scenarios and source inspection are not runnable App tests, benchmarks or completed native proof | `docs/baselines/precut.md:128–136`; `docs/reference/verification.md:3,38–40` | Preserved |

## Intentionally superseded or still open

- Required public `TxPool`, `Baton`, `Executor`, `Storage`, `BlockService`, `Orderer`, their associated types and `on_*` method vocabulary are superseded. Their still-needed App semantics are mapped above. Concrete private functions/handles suffice; the removed declarations are not preservation failures.
- Ordinary App `on_finality` verification, proof archive, native-order interpretation, body resolver and recoverable delivery cursor are superseded by current Marshal. Native protected-policy validation and matching interpretation/recovery are still required future native work; they are not silently supplied by ordinary Marshal.
- Old `534af0e` combined `finalize(sealed)` is replaced by current `apply(sealed)` then `finalize()` and a covering barrier. Old optional `OptionFuture`, collector and source-adapter detail is not a mandatory interface/lifecycle choice. Its reusable mechanisms remain conditional; no automatic f+1 verifier, rootless fork or repeated-validator import is asserted.
- Per-block signing, incumbent-first tail, inline policy bytes and finite-prefix permutation remain unadopted. Current open tables preserve their underlying questions (`docs/baton/direction.md:99–113`, `docs/consensus/decisions.md:23–30`, `docs/execution/README.md:41–49`, `docs/execution/interfaces.md:64`). No positive-adoption construction, direction lock, extension deletion or receipt quorum was restored.
- Concrete transaction semantics, comparator/tie/horizon, resource quotas, root/checkpoint/codec/key choices, common signing boundaries, cancellation/access protocol, durable linkage and import/floor transition sequencing remain implementation decisions. The ledger records required outcomes, not invented policies.

Validation: scoped `git diff --check` for the owned reader edit and this report. No source edit, diagram edit, native test, external write or runtime/protocol proof claim.
