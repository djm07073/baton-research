# Round 5: reader path and simplification

Reviewer: `/root/docs_alignment`. Read-only audit of current `docs/baton/*`, overview/entry/navigation pages and both transaction pages. No reader-page edits made in this round. This review concerns the documented implementation path, not validation of a working App or a backend choice.

## Can a new engineer find the four requested responsibilities?

Yes. Starting at `docs/baton/README.md` identifies one App, the reused Engine/Marshal, native callback handles and the full-Baton policy gap without requiring historical layer documents. The callback page is the implementation sequence; the direction page owns scheduler policy. The pool connection is explained, but its concise contract is less directly discoverable than the other three requirements.

| User requirement | Current answer | Remaining reader friction |
|---|---|---|
| Pool inside App | `baton/README.md:15,27`, `tx/interfaces.md:7–15`: shared RPC/peer admission, retained selected/unselected candidates, bounded stable packing, durable-outcome maintenance | Main entry has no direct link from its pool row to the concise transaction contract. Navigation first offers the much longer pool survey. |
| Pre-cut / Baton inside App | `baton/README.md:16,21`, `baton/direction.md:5–56`: two concrete policies, shared state/execution, pending-only sorting and exact-parent reconciliation | Clear. The repeated “no new public trait” reminders can be shortened locally, but the two modes must stay visibly distinct. |
| App and scheduler during verify | `baton/README.md:28,38–48`, full pseudocode in `baton/interfaces.md:29` onward | Clear. The small duplicate verify sketch in `tx/interfaces.md` now omits details intentionally retained by the canonical callback contract. |
| App and scheduler during Update | `baton/README.md:29,50–56`, full Update/ACK contract in `baton/interfaces.md` | Clear. Duplicate pool-page ordered-update pseudocode can be mistaken for a complete handler and appears to put pool maintenance before ACK. |

Concrete transaction semantics, comparator, runtime/backend, wire formats and budgets remain open on purpose. “Exactly what to implement” means responsibilities and sequencing, not an already selected complete protocol/backend implementation.

## Small recommended edits

### 1. Link the four implementation questions from the existing main tables

In `docs/baton/README.md`, link the existing component labels rather than add another overview/table:

- `App transaction pool` → `../tx/interfaces.md`.
- `App scheduler` → `direction.md`.
- The verify entry name → `interfaces.md#automatonverify-validity-custody-and-scheduling`.
- The Update reporter entry name → `interfaces.md#marshal-reportupdate-canonical-input-and-ack`.

In `docs/README.md:7–14`, include the concise pool contract in the initial route and treat architecture/Rust signatures as references available beside it. In `docs/SUMMARY.md:13–16`, list `tx/interfaces.md` as “Transaction admission and selection” before `tx/README.md`, labeled “Pool backend survey”. No files or anchors need to move. This lets a new engineer follow the four user questions without first reading external-backend fit evidence.

### 2. Remove the pool page's second verify/Update implementation sketch

`docs/tx/interfaces.md:17–36` duplicates all three callbacks. Keep the pool-specific propose sketch through stable body construction/staging. Remove `app.handle_verify` and `app.handle_ordered_update` from this page and link their canonical flows in `../baton/interfaces.md`.

Preserve the pool contract in the existing prose: selection retains stable bytes, lifecycle cleanup follows durable outcomes, lost maintenance must reconcile before stale backend state is used, and maintenance adds no native consensus/Update approval gate. The canonical callback page already retains lossless intake, Exact lifetime, floor overlap, late verify, ancestry and once-only completion rules. A second abbreviated handler cannot safely act as an equivalent contract.

Suggested replacement after the remaining propose snippet:

> Verification and canonical delivery use the [App callback handlers](../baton/interfaces.md). Pool maintenance consumes recoverable durable outcomes; it does not add a separate processing ACK to canonical application or native consensus. Reconcile missed maintenance before relying on the backend's readiness state.

Do not remove the pool-specific identity/packing/dependency bounds or backend lifecycle caveats.

### 3. Replace one vestigial public-interface instruction

`docs/tx/README.md:90` currently ends “expose only `admit` and `select`.” This reads like the superseded mandatory public API even though the opening correctly says these are concrete App operations.

Suggested replacement:

> Keep static analysis and selected/unselected classification inside App admission, and let batch selection consume retained selected candidates. Canonical maintenance stays internal.

The heading “Commonware primitives in the transaction layer” can become “Commonware primitives for the App pool” while preserving the old anchor if required. The actual upstream public `submit`, source `PoolTransaction`, and existing Nunchi actor/handle are legitimate source APIs; they are not vestigial App traits and should not be removed by a keyword sweep.

### 4. Remove the main entry's second inventory of superseded layers

`docs/baton/README.md:58–68`, “What to reuse, and what remains new,” repeats the current composition in `:11–19` but leads with old names such as `Executor::execute/commit` and `Baton::on_finality`. That historical mapping already exists, collapsed and clearly labeled, at `docs/overview/glossary.md:44–57`.

Remove the duplicate replacement table, or replace it with one link to the glossary mapping. Keep the current composition table and the final native-policy gap at `:75–81`. Existing content already states the reused Marshal custody/history/backfill/cursor, concrete App pool/work/apply and Commonware runtime/P2P. No current requirement is lost. No current local link targets this section heading; a compatibility anchor may still be retained cheaply if desired.

### 5. Collapse the architecture page's repeated callback walkthrough

`docs/overview/architecture.md:51–57` retells propose, verify and Update immediately after the owner table, before another path table. Its unique digest/custody/ACK facts are already owned by the main callback guide, body page and Rust reference. Preserve the `inputs-and-outputs-between-layers` compatibility anchor and shorten this section to a linked description:

> `propose` connects the App pool to Marshal custody; `verify` connects usable payloads to speculative scheduling; Marshal `Update` connects exact canonical input to App reconciliation and durable apply. Follow [callback behavior](../baton/interfaces.md) for completion, cancellation and recovery rules.

Keep the data/control/canonical path table, worker ownership/fencing paragraph, budget/overlap limits and root-deferred storage caveat. Those explain architecture rather than repeat handler pseudocode.

## Do not simplify away these distinctions

- Validity/custody is independent from speculative admission, execution completion and canonical retirement. Current-state rechecks after async work and native retention after App apply matter.
- Speculative admission is bounded and optional; retained canonical Updates cannot be dropped on `Backoff`. Floor changes can overlap native delivery windows.
- A callback handle's `&mut self` does not establish App-wide serialization or a database writer fence. This unique note in `overview/interfaces.md:19` deserves to remain.
- Body/header/execution-parent identity, local pre-sign versus authenticated candidacy, observer/nonproducing-validator differences and startup custody-before-ready prevent actual wiring errors.
- Backend survey details are evidence, not obsolete layers. Keep decoding/size bounds, nonce-prefix behavior, destructive selection retention, canonical maintenance and cross-version compatibility limits in their current survey sections.
- Pre-cut's lack of Baton messages and full Baton's missing authenticated native-policy integration must remain visible near the entry point.

No unnecessary new actor/class was found in the reader path: the architecture explicitly says green boxes are ordinary App responsibilities, not one actor per box. Selected/unselected are required logical pool classes, and typed Reporter handles are required by the existing associated-type boundary. The recommended cuts remove duplicated explanations rather than those responsibilities.

## Authorized edits and verification

Root subsequently authorized this reviewer to change `docs/tx/{README,interfaces}.md`, `docs/README.md` and `docs/SUMMARY.md`. Applied at 2026-10-09 07:37 UTC:

- `docs/README.md:9–15`: the first five pages now cover App composition, the concise pool contract, callbacks, schedulers and normal E2E. Architecture, Rust signatures and the optional backend survey remain linked directly below; no reference was removed.
- `docs/SUMMARY.md:15–16`: admission/selection precedes the clearly labeled backend survey.
- `docs/tx/README.md:90`: replaced “expose only” with concrete App admission/selection and internal maintenance; all backend source evidence and policy cells remain.
- `docs/tx/interfaces.md`: removed the 11-line duplicate verify/Update sketch and shortened its repeated callback explanation. The remaining propose snippet retains stable bytes and custody association. Line 27 links the canonical handlers and preserves recoverable maintenance/no-extra-pool-ACK; line 29 retains transaction/body/header/applied correspondence. The page went from 58 to 47 lines without cutting any backend table, citation, selection bound or retention rule.

Root owns the main-entry links/table cut and any architecture shortening; this reviewer did not edit those files. No diagram or generated interface changes were needed. Targeted `git diff --check` passed. Fresh `npm run docs:check` passed: 32 content pages, 237 local links, 19 rendered diagrams, 38 blank policy cells, zero failures.
