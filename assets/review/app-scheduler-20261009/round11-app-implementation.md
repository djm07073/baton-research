# Round 11 — Minimal App implementation boundaries

## Outcome

The current core pages give an implementer a coherent way to wire one concrete App to existing Automaton, Relay and Reporter interfaces. No missing public Executor/Storage/TxPool/Baton abstraction or extra required actor was found. Both modes share body custody, exact-parent execution, canonical apply and result handling. Full Baton native policy/adoption remains explicitly open; the document does not claim that App-only report/direction handling changes native order.

This is a design and current-source review. The open VM, encoding, comparator, result, resource and recovery policies still need implementation choices; the pseudocode is not a compiled App. No protocol or runtime proof is claimed.

## Implementer's wiring path

| Decision or connection | Current location | Why it is sufficient without another layer |
|---|---|---|
| One App owns concrete pool, selected scheduler and execution/state | `docs/baton/README.md:9-21` | Files/private functions or a local mode enum express these responsibilities; public traits are not required. |
| Start custody and retained output handling before native recovery callbacks | `docs/baton/interfaces.md:5-11`; `docs/reference/integration.md:24-46` | Existing node owner handles startup/recovery and service lifetime. A second lifecycle service is unnecessary. |
| Native Engine receives Automaton, supplied Marshal Relay, and native Activity reporter | `docs/overview/rust-interfaces.md:22-60,96-103`; integration assembly | Existing callback associated types and concrete body/header identity are explicit. Optional App observations are a sibling to Marshal, not a forwarding dependency. |
| Marshal receives App Update reporter | `docs/overview/rust-interfaces.md:55-60,81-94` | A typed handle addresses the existing Reporter associated-type constraint. The retained Update carries its actual Exact token; no application ACK protocol is invented. |
| App picks one scheduling mode at startup | `docs/baton/README.md:21`; `docs/baton/direction.md:7-16` | PreCut contains no Baton report/direction instance. Both use the same candidate/checkpoint state and canonical writer. |
| Native order stays authoritative | `docs/baton/interfaces.md:85-131`; `docs/baton/direction.md:87-97` | Exact canonical input enters independently of speculative admission. The still-required native protected-prefix extension is not hidden behind an App method. |

Read the core entry guide, callback page, scheduler page, then their linked Rust/assembly and QMDB details. That is a navigable implementation path rather than a list of interchangeable frameworks.

## Actual wait boundaries

| Path | Required boundary | Independent work |
|---|---|---|
| Propose | Build context-bound full block; await accepted staging; return body digest through the response receiver | Later local verify establishes durable custody before signing. The design allows an implementation to wait earlier, but does not equate staging acceptance with a flush. |
| Verify | Await exact body/context checks and durable custody; keep temporary uncertainty pending | Metadata admission is short. Exact-parent execution, root preparation, report collection and direction replies are not prerequisites for true. No false verdict merely because speculation is saturated. |
| Dispatch | Owner claims a current pending attempt and reserves resources after exact parent is ready | A duplicated wakeup cannot launch the same attempt. Parent completion, candidate admission and worker result adoption have distinct identities. |
| Synchronous Update report | Transfer the complete Update/token into retained App ownership and return Feedback | Execution and storage run outside the callback. Backoff is not a resend request. Ordinary capacity comes from the active native window, with explicit floor-transition overlap accounting. |
| Canonical apply | Exact order/base and completed direct work, or verified applicable import; one writer; covering durability and App recovery linkage | Direct apply does not wait for f+1 peer signatures, direction approval or pool cleanup. Only imported work additionally needs its certificate/material checks. |
| ACK | Exact input is recoverably applied; signal the retained Exact token | Native consensus proceeds independently. Marshal separately persists its delivery cursor. A later crash can replay an already applied input. |
| Baton planning | Authenticated bounded snapshot and completed candidate evaluation before publishing prepared state | Strategy creation/polling is placed off short native/App handlers. A cut does not await planning; pre-adoption base behavior and post-adoption preservation remain distinct. |

These boundaries agree across `baton/interfaces.md`, `execution/interfaces.md`, `execution/README.md` and `baselines/precut.md`; none requires a different execution/durability contract for PreCut.

## Fresh current-source checks

Inspected actual local source, not only previous audit findings:

| Source | Observed contract | Document correspondence |
|---|---|---|
| `consensus/src/lib.rs:125-158,258-268` | Cloneable Automaton handle returns a future yielding a response receiver; Reporter is synchronous with one associated Activity | Core and Rust pages distinguish response delivery from handler pseudocode and use typed reporter handles. |
| `examples/log-multimmit/src/node.rs:242-335` | Existing transport registration; Marshal setup; application start; Engine::open receives App, Relay and Reporters; then engine start/readiness | Current integration assembly follows this owner graph without transplanting an obsolete Orderer or full Stateful application. |
| `consensus/src/multimmit/marshal/mailbox.rs:327-358,419-446` | Stage accepts durable work/token; put awaits it; subscription establishes custody, can wait for a slot, and does not start a peer fetch | Verify's legitimate body/custody wait is kept separate from forbidden speculative-capacity/execution waits. |
| `consensus/src/multimmit/marshal/actors/delivery/actor.rs:237-247,303-355` | Report synchronously, retain native Exact waiter, fill bounded delivery window; only Closed rejects immediately; sync ACK cursor separately | Retained App intake, Backoff handling and later independent cursor I/O are accurate. |
| `glue/src/stateful/db/mod.rs:296-324,541-550` | Concrete reads/writes belong to unmerkleized wrapper types; child forks use a sealed parent | Root-deferred effects/overlay remains optional App work. Current docs do not advertise an unsealed-parent generic fork. |
| `glue/src/stateful/db/any.rs:106-150,523-544` | Batch reads reacquire live applied DB; batch writes are local mutations; apply and start_sync are separate | Exact ancestry and live-access fencing are necessary even when stale completion adoption is prevented. |
| `glue/src/stateful/db/current.rs:537-560`; `storage/src/qmdb/current/db.rs:665-697` | Sync targets bind operations root/range; apply checks ancestry and publishes in-memory/journal state; separate durability operation remains | Current canonical root versus operation sync root and valid branch applicability remain explicit in QMDB/state-sync pages. |
| `glue/src/stateful/db/mod.rs:334-336,358-397,415-485,493-579` | Failed/canceled by-value mutation loses instance; init can select checkpoint; apply need not be durable; finalize covers preceding checkpoints; await barrier true; mutations do not overlap; prune requires durability | Current QMDB recipe preserves all these conditions, including exact output/applied/provenance recovery linkage as App-specific work. There is no automatic cross-store commit claim. |

Root's corrected startup paragraph was read back at `execution/state-sync.md:41` against `marshal/config.rs:163-185`: `Start::Floor` really includes caller-authenticated positive monotone `floor_generation`, bound to the imported snapshot. Floor and Update themselves lack that field. This is separate from App worker attempts/generations. The paragraph was not edited by this agent.

## Necessary state versus unnecessary framework

The retained candidate map, exact-parent checkpoints/current attempts, canonical Update tokens, and durable applied identity each preserve different facts and cannot safely be collapsed into a single “executed” flag. They can all live in ordinary App state with existing collections, handles and runtime work; no dedicated service/trait is implied. Baton alone needs a report window/frozen snapshot/planning attempt. PreCut does not retain empty copies of those structures.

The current root prose is occasionally repetitive, but the repetitions generally make an entry page self-contained or explain a different completion boundary. In particular, do not trim the separate treatment of custody versus speculation, candidate identity versus execution identity, or result certificate versus App durability merely because all mention validity/completion.

One genuinely redundant core sentence is `docs/baton/interfaces.md:83`, “No extra public execution trait is needed.” The opening already defines the pseudocode as private handlers, and README establishes the concrete internal composition. Removing that sentence is an optional one-line editorial trim, not a correctness fix; root owns that page and this review did not edit it. No paragraph-scale deletion was justified.

## Narrow owned edits and verification

Renamed QMDB's obsolete “Existing APIs at the native pin and indexed release” heading to **Current QMDB APIs** and removed its legacy-heading explanation. Retained the old explicit anchor so existing links resolve. The table already covers only the current checkout; historical evidence remains clearly linked in the introduction. No execution behavior, policy, diagram or source link changed.

Removed the state-sync page's first H2, which exactly repeated its H1. The introduction now proceeds directly to the adoption checks; the existing `#state-sync-from-certified-execution-results` link still targets the H1. This removes duplication without creating a replacement section or altering root's startup paragraph.

Scoped `git diff --check` passed. Root owns the final documentation link/build checks. No further execution/baseline change is recommended from this round.
