# Round 13: reader-oriented simplification

Reviewer: `/root/docs_alignment`. Reviewed the 32-page current navigation, page purposes/headings and repeated callback/scheduling/ACK explanations. The aim is to make `docs/baton/` the implementation entry without removing required contracts, compatibility anchors or useful detailed evidence. This pass proposed the three material prose cuts below; their approved application is recorded at the end. No files or diagrams were consolidated.

## Navigation and canonical topic ownership

| Current pages | Distinct reader purpose |
|---|---|
| `docs/README.md` | One reading route and implementation status, leading to App composition, pool contract, callbacks, scheduling and normal E2E. |
| Overview: architecture, glossary, interfaces, Rust interfaces, networking | Ownership diagram; precise identities/terms; question-to-contract index; existing API signatures; actual network planes/handles. The interfaces index is short and does not duplicate the full handler guide. |
| Baton: README, interfaces, direction | Main composition/trigger guide; canonical callback/owner/lifecycle sequence; shared scheduler rule plus Baton planning and native-policy gap. These remain authoritative for implementation. |
| Transactions: interfaces and README | Concrete App pool contract versus conditional backend adaptation/source evidence. The long backend survey is not a required first step. |
| Consensus: README, block-body, ordered-input, decisions | Native source/actor map; block identities/custody APIs; Marshal order/delivery/retention authority; unresolved native Baton policy work. These describe reused machinery rather than another App implementation layer. |
| Execution: README, interfaces, QMDB, state-sync | Responsibility overview; execution/result and durability contract; concrete backend/access/root/canonical recipes; imported material and checkpoint/floor authority. These remain distinct from scheduler priority policy. |
| Nine E2E pages: normal, block-body, native-consensus, leader, reschedule, canonical, recovery, results, state-sync | Concrete scenario diagrams and the caveats needed to read each scenario. They should link the canonical contract for exhaustive callback exceptions rather than grow second copies of it. |
| Pre-cut baseline | Independent no-Baton comparison configuration, common resources/endpoints and planned measurements. Its baseline-specific conditions warrant a separate page. |
| References: integration, verification, sources | Real assembly/development sequence; future acceptance cases; provenance/version/publication status. These do not claim runnable App integration. |

Every page has a defensible role. No reduction in file count or removal of legacy anchors is needed. The three cuts below focus repeated prose after useful tables/diagrams, not source recipes, actual failure bounds or unresolved decisions.

## 1. Shorten the body E2E's repeated verification contract

Target: `docs/e2e/block-body.md:80–84`, three paragraphs after the diagram and body-fetch/custody distinction.

Why: the page currently repeats the full role/origin, ancestry, capacity, late-verify and retirement explanation already owned by `baton/README` and `baton/interfaces`. That turns the explanation of one body sequence into a second callback reference. Keep the unique `subscribe_block`/buffered-fetch/wrong-response paragraph at line 78 and pool-retirement link at line 86 unchanged.

Exact suggested replacement:

> The diagram shows one eligible live validation request. `verify` also runs locally before signing and during recovery; qualify role/lane, lifecycle and exact identity before treating success as a new peer candidate. Nonproducing validators have no own-lane exclusion, while Observers normally enter through Update. [Role and origin rules](../../../docs/baton/README.md#when-speculative-execution-begins).
>
> Admission uses the App owner's current state after custody completes. Required producer ancestry and authentication still apply, and the scheduler waits for the exact execution checkpoint before dispatch. Already-applied or retired speculative work can still require an honest native custody response. Follow the [candidate/dispatch handler](../../../docs/baton/interfaces.md#automatonverify-validity-custody-and-scheduling) for deferred-capacity, duplicate and stale-request handling.

When applying to the actual E2E page, use `../baton/...` for those two links. No body diagram changes are needed.

Fact-retention map:

- Three origins, no origin flag, nonproducing/Observer roles, local pre-sign authentication and optional-observation limitations remain in `docs/baton/README.md` under “When speculative execution begins.”
- Pending parent validation, permanently invalid ancestor handling, bounded deferral/forgone speculation, honest custody verdict and canonical intake independence remain in `docs/baton/interfaces.md` under verify.
- The post-async current-owner check and exact-block deduplication remain in that handler and its pseudocode; current-attempt completion ownership remains under dispatch.
- Exact native retention/release semantics remain in `docs/consensus/block-body.md`, separate from the App retirement rule retained in the replacement.

## 2. Keep the canonical E2E's handoff rule, link its exhaustive failure contract

Target: `docs/e2e/canonical.md:55`, the long paragraph after the ordinary ACK/window explanation.

Why: lines 49–53 already give the scenario's durable-apply ACK, example-consumer caveat and native/window/cursor separation. Line 55 duplicates almost the entire canonical callback's Backoff/Closed/token/floor/recovery contract. A short handoff paragraph plus the authoritative link keeps this page readable after the diagram without weakening the callback reference.

Exact suggested replacement:

> `report` is a synchronous retained handoff: preserve every accepted Update and its Exact token in App state, using coalesced wakeups if needed. `Backoff` does not request redelivery, and an unacknowledged dropped Exact clone cancels completion. The [canonical callback contract](../../../docs/baton/interfaces.md#marshal-reportupdate-canonical-input-and-ack) defines active-window sizing, clone obligations, crash replay and App-owned floor/import coordination; floor resets do not clear App's retained Updates.

Use `../baton/interfaces.md#marshal-reportupdate-canonical-input-and-ack` in the actual page. The existing ordinary window and separate cursor-I/O paragraph at line 53 stays unchanged. The detailed Exact source link already exists at `docs/consensus/ordered-input.md:29`; it need not be retained a second time here solely to preserve citation count.

Fact-retention map:

- Synchronous full-Update retention and private worker processing: canonical callback pseudocode.
- One active window, native independence, Closed/Backoff behavior and every-clone acknowledgement: canonical callback's ordinary-window paragraph.
- Honest durability, exact replay identity/gap/error handling: canonical callback's replay paragraph and recovery E2E.
- Old retained Updates, missing upstream generation field, bounded reset overlap and App-owned transition fence: canonical callback floor paragraph and execution state-sync handoff.
- On failure, recover authoritative state rather than using the failed instance: callback storage/canonical clauses plus QMDB/recovery pages.

## 3. Let the execution overview introduce execution, rather than repeat four callback paragraphs

Target: `docs/execution/README.md:21–27`, four paragraphs after its nine-row responsibility table. This is another agent's/root-owned page; suggestion only.

Why: the table already identifies candidate admission, exact-parent effects, canonical reconciliation, durable application and ACK. The following paragraphs then restate verify origins, ABC/ACB scheduling, synchronous Update and replay. The actual new subject begins at “Execution effects and storage roots.” Link those repeated topics and retain the execution reuse constraint as the bridge.

Exact suggested replacement:

> The [callback contract](../../../docs/baton/interfaces.md) defines candidate admission, synchronous Update retention, replay and durable ACK. Both scheduler modes use the same exact-parent execution state and canonical writer: valid speculation is reusable only for matching input, parent and runtime, and a differing canonical path needs repair. Keep started work fixed on ordinary arrival and sort only eligible pending work under [the shared scheduling rule](../../../docs/baton/direction.md#global-rule-for-local-execution-and-reports).

Use `../baton/...` links in the actual execution page. Preserve its native AppExecutor paragraph, responsibility table, effects/root separation, single writer/access fencing, result provenance and all open backend choices.

Fact-retention map:

- Verify origins and exclusions: main entry guide and canonical verify handler, both linked.
- Fixed started prefix, pending sorting, ABC/ACB cases and repair from exact parents: `docs/baton/direction.md:18–43`, plus scheduling E2E.
- Synchronous Update, continuous indexed order, exact reuse/repair/import, durable ACK, separate native progress and crash replay: `docs/baton/interfaces.md` canonical worker and milestone table.
- Completion meanings remain locally visible in the execution overview table, so this cut does not force readers to follow a link merely to understand the responsibility list.

## Terminology and heading assessment

Only three current pages use `AppExecutor`: `docs/baton/README.md:5`, `docs/consensus/README.md:19`, and `docs/execution/README.md:5`. Each explicitly identifies the private native callback-dispatch role and distinguishes App transaction execution. There is no unqualified public AppExecutor/Executor implementation obligation to repair.

A few retained headings say “layer” in the ordinary grouping sense, and old compatibility fragments mention traits/layers. Their surrounding tables and introductions now state concrete App responsibilities and existing native mechanisms. Renaming them merely to remove a keyword would add churn or compatibility anchors without a reader benefit. The optional third-party pool traits and QMDB utility wrappers are real supplied interfaces, not resurrected public Baton layers.

The supplied `## Reuse the same body components as Tempo` heading leads immediately to the directly compatible current native example and labels Tempo/Alto historical evidence. Its prose is clear; a cosmetic rename is unnecessary for this task. The recent legacy anchor relocation already solved the actual wrong-section navigation issue.

No other material cut is recommended. In particular, keep the body-digest/header/BlockRef distinctions, synchronous-versus-oneshot method signatures, normal Update/ACK sequence, precise pending/failed completion rules and explicit missing native Baton integration. They answer the user's original points and are not redundant implementation decoration.

## Applied follow-up

Root approved all three exact replacements. I applied the two E2E replacements in `docs/e2e/block-body.md` and `docs/e2e/canonical.md`; root applied the execution-overview replacement in `docs/execution/README.md`. The fact-retention maps above identify the authoritative remaining contracts. All actual page links use `../baton/...` as specified, including stable verify, canonical Update and scheduling headings.

The body E2E retains the fetch-versus-custody distinction, correct peer/role/lifecycle interpretation, current-owner timing and native custody obligation after speculative retirement. The canonical E2E retains the durable ACK boundary, example immediate-ACK caveat, active-window/native independence and separate cursor-I/O timing. The execution overview retains its private native AppExecutor distinction and full responsibility table. No callback lifetime, failure-cleanup, capacity/floor contract or policy decision was removed from its canonical page. No diagram source or compatibility anchor changed.

After the edits, `python3 assets/tooling/check_docs.py` passed with **32 pages, 250 local links, 19 diagrams and 38 blank policy cells**. `git diff --check` passed. No rerender was needed because the embedded diagrams and assets were unchanged.
