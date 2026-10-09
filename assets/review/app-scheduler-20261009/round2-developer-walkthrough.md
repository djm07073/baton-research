# Round 2: first-block developer walkthrough

Scope: current `docs/baton/*`, `docs/overview/*`, consensus pages, execution overview/interfaces/state-sync, Pre-cut baseline and the matching E2E pages. Source checked at `6233438985d8249d2b2bc1204191d5d405652288`. This review reasons from source and document scenarios; it executes no application protocol.

## Findings

### 1. Distinguish a nonproducing validator from an observer

Locations: `docs/baton/README.md:46`, `docs/baton/interfaces.md:55`, `docs/e2e/block-body.md:80`.

A node with `producer_chain=None` is not necessarily a native observer. `actors/voter/actor/chains.rs:129` constructs the per-chain verification planes for any `Role::Validator`, even if `protocol.producer_chain(participant)` returns None. For `Role::Observer` it immediately returns the empty task set. `engine/mod.rs:615` derives these roles from `scheme.me()`.

Counterexample: a developer starts an observer with App state and waits for `verify` to register every pre-cut candidate. No live validator verification plane exists, so that intake never fires. Separately, treating None as lane zero would incorrectly suppress another producer's lane-zero block on a nonproducing validator.

Proposed fix: state the primary early-verify flow applies to validator Apps. For a validator without a producer lane, there is no own-lane exclusion; native verified producer context supplies the identity. An observer must not assume this callback; ordinary canonical application still uses Marshal Update, and observer speculation would need an explicitly available authenticated observation path. This does not require adding a new observer service or public trait.

### 2. The fresh-start execution base is missing from the first-block recipe

Locations: `docs/baton/interfaces.md:7-9` and `docs/e2e/recovery.md:3-7`; dispatch pseudocode `docs/baton/interfaces.md:64`.

The text explains recovering an existing canonical checkpoint and waiting for a valid parent, but not initializing the first one. A new deployment has no recovered App checkpoint. A developer following the literal steps can leave the first block permanently pending, or incorrectly use a producer's native genesis-header digest as an App state checkpoint.

Source: `marshal/types.rs:57-70` defines OutputIndex zero as stream genesis and says it is never delivered. The first ordinary delivered index is one. The native producer header parent names lane ancestry and does not initialize application state.

Proposed fix: add one sentence to startup: on a fresh deployment initialize the configured deterministic App genesis state/runtime and bind the initial applied position to Marshal's genesis prefix; index zero is not an Update to await. On restart recover that binding; on checkpoint boot verify the floor-to-App-state relation. Keep the actual application genesis contents open rather than inventing a default transaction model.

### 3. Lifecycle activation should consume retained candidate state

Locations: `docs/baton/interfaces.md:9`, `:41-44`, `:60`; `docs/e2e/recovery.md` startup prose.

The handler retains verified metadata while not live but adds pending work only if already live. Startup later says to activate scheduling, without an explicit retained-state scan. A completed successful verdict does not promise another callback, and a best-effort Activity may never arrive. The shared Automaton contract documents single-shot requests; the current remote implementation separately retries closed receivers as Unavailable (`chain_plane.rs:540`, `machine/eligibility.rs:352`), as the native reviewer found. That retry is not a substitute for re-evaluating already successful retained candidates. Merely changing a phase flag can leave a valid retained candidate out of pending forever.

This is a lost speculative opportunity, not a canonical-safety failure, because Update remains authoritative and the current design explicitly permits bounded speculation to be forgone. It should nevertheless be deliberate, rather than depend on a repeat callback that native does not promise.

Proposed fix: lifecycle activation and worker/capacity recovery are ordinary App-state wakeups that re-evaluate retained candidate facts against current applied identity/context before dispatch. Explicitly discarded candidates need not be reconstructed solely for speculation. No new native origin field or reliable Activity channel is needed.

### 4. Remove the duplicated custody await in the core verify pseudocode

Location: `docs/baton/interfaces.md:31-40`.

The default path says locate/subscribe, then await body/custody, then separately await required durable custody. Current `Mailbox::subscribe_block` already establishes durable custody (`marshal/mailbox.rs:418-441`), and the example waits it once before checking the header (`examples/log-multimmit/src/application/actor.rs:74-110`). A literal implementation could add another archive flush or a redundant custody abstraction.

Proposed fix: name the concrete default once: `block = await marshal.subscribe_block(expected_ref)`; validate exact header/body and App validity; retain candidate state; reply true. Keep active `fetch_block` as a distinct optional retrieval trigger. Alternative reconstruction guarantees need not occupy the central Marshal recipe.

### 5. Minor source name typo

Location: `docs/baton/README.md:5`.

The internal type's path is `actors::voter::actor::app::AppExecutor`, matching `consensus/src/multimmit/actors/voter/actor/app.rs`, rather than `actors::voter::app::AppExecutor`. Prefer the source link and short type name to a long private module path.

## Shared review finding already addressed in owned pages

The native and simplification reviewers found that a floor reset can replace Marshal's active ACK window while old Updates remain held by App; the per-window `max_pending_acks` is not a global inbox bound. `Update` contains no generation field. E2E canonical/recovery/state-sync now require App-owned serialized floor/import fencing and old-Update reconciliation, or explicitly bounded overlap. The concrete cross-store transition remains implementation work.

## Checked counterexamples that the current text handles

- Header arrives before body: subscription is pending and explicit fetch is separate; no premature false/empty interpretation.
- Local producer verify before signing: local candidates cannot manufacture signed report eligibility.
- Body digest reused under another producer context: body/header identities and execution parent are separate, so dedup/reuse uses exact context.
- C begins on A before B arrives: preserve AC, append eligible B, and repair only on differing canonical input.
- Update arrives before any local speculation: canonical worker executes from its exact predecessor; scheduling hints are not required.
- App apply persists but Marshal cursor does not: exact identity/applied metadata permit idempotent redelivery and ACK.
- Report callbacks return Backoff after lossy enqueue: explicitly prohibited; accepted Updates retain their token and Closed is the terminal path.
- Missing f+1 execution signatures: certification remains incomplete without gating native cut or directly valid canonical work.

## Simplification assessment

The new reader flow is materially smaller in required architecture: one App, existing Engine, existing Marshal; four public application traits and a second ordinary delivery/proof/cursor mechanism are removed. Typed handles are justified by Reporter associated-type constraints, not new deployed services. Two scheduler modes share execution and persistence.

Further prose reduction should consolidate the detailed verify and ACK contracts in `baton/interfaces.md`. `overview/interfaces.md` can remain a compact reading map; it currently repeats the callback table, identity table and completion summary also present in the Baton and Rust references. The E2E pages justify their repetition through ordered diagrams and concrete recovery scenarios. Preserve the native policy-gap section and source-backed custody/ACK distinctions when shortening.

## Owned-page follow-up

E2E body now distinguishes nonproducing validators from observers and explicitly notes child verification can start while native parent verification is pending. E2E recovery now gives the fresh App-genesis / index-zero boundary and lifecycle candidate re-evaluation. Core root/peer files were not edited by this reviewer. Closed-verdict behavior remains correctly scoped: E2E recovery only claims failure for recovery verification, not a universal no-retry implementation rule.
