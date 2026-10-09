# Round 19: root delivery and documentation-check review

Reviewer: `/root`. This is an independent source/document inspection during the ongoing three-hour task, not runtime testing or completion.

## Delivery source

Read `consensus/src/multimmit/marshal/actors/delivery/actor.rs`, `acks.rs`, `utils/src/acknowledgement.rs`, the shared `Reporter` definition and the example `application/reporter.rs` from native commit `6233438985d8249d2b2bc1204191d5d405652288`.

- Delivery calls synchronous report with an owned full Update and fails on Closed; Backoff does not arrange a retry. PendingAcks owns the waiter after report returns.
- Exact clone increments obligations; unacknowledged drop cancels its waiter. App must retain its received token and not casually clone it into optional scheduling work.
- Only the contiguous acknowledged prefix leaves the outstanding queue. Ready/syncing cursor prefixes are tracked separately; those storage syncs do not themselves consume outstanding application slots.
- Reset clears native waiters/cache and resets its cursor. It cannot clear Update values already transferred into App.
- The synthetic example's headless immediate ACK is not durable transaction application. Current core and E2E documents explicitly require replacement with the retained canonical worker.

Current core `interfaces.md`, consensus `ordered-input.md` and E2E `canonical.md` agree on these boundaries. No extra actor, trait, ACK protocol or cursor store is needed.

## Documentation tooling

Read `check_docs.py`, `export_interfaces.mjs`, the existing browser checker and the current Rust binding receipt. The checker verifies current navigation/local targets, blank decisions, source/export equivalence and rendered-asset source hashes/dimensions; the historical `--migration` mode intentionally checks a different preserved snapshot. The exporter labels its five Rust blocks as API excerpts, not standalone code.

These tools do not prove native semantics, compile the excerpts or execute App behavior. Existing review wording correctly separates local source inspection, presentation validation and future acceptance cases. A routine check/build after Round18 changes passed with 32 pages, 251 local links, 19 diagrams and 38 blank policy cells. Later prose/navigation edits need the next regular check; no blanket later-state claim is made here.

## Simplification disposition

Applied the Round18 role table in the App entry and Round19 direct link to assembly/callback handlers. The separate execution interface table was replaced by canonical links by its owner. Native delivery details remain in their focused guide and core callback contract because one describes supplied machinery and the other the App obligation; removing either outright would hide a real boundary.
