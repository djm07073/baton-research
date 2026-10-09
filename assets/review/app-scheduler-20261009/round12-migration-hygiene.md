# Round 12: current documentation versus preserved history

Reviewer: `/root/docs_alignment`. Scope: current docs navigation and architecture, root entrypoints/instructions, compatibility links, generated Rust/diagram inputs, and separation from historical paper/archive/review records. No historical document, external publication or protocol source was changed in this pass.

## Confirmed reader issues and resolution

1. **Publication state at the root entrypoint.** Root `README.md:12` linked GitBook as a direct entry without explicitly saying this App-owned rewrite had not been published. Added that fact and directed readers to `docs/` for the current design. No claim was made about a live external readback. Its Rust row at `:8` now accurately describes existing Commonware API excerpts instead of “concrete App sketches,” matching the actual generated file.
2. **Compatibility anchors existed but landed at the wrong topic.** In `docs/baton/README.md`, the role, report and confirmed-delivery anchors had all been placed just before Baton-specific planning. Root moved them, without renaming or deleting them: `roles-and-responsibilities` now precedes composition (`:9`), `report-connection` precedes App entrypoints (`:25`), and `confirmed-order-delivery` precedes canonical application (`:54`). The primitives anchor remains at Baton-specific work (`:64`).
3. **The old interface-overview target landed on optional observations.** Root moved `docs/baton/interfaces.md#interface-overview` to immediately after H1, before the callback introduction. The separate `finalized-state-progress-notifications` anchor remains with native activities/optional local notifications. Older URLs now reach the relevant replacement topic.

The root owns core edits; I changed only its delegated companion `README.md`. None of these fixes changed diagram sources, APIs, policy choices or historical records.

## Current / historical boundary audit

| Surface | Finding |
|---|---|
| `AGENTS.md:11–19` | Current 2026-10-09 decision explicitly supersedes old public-layer and Baton-owned ordinary-delivery requirements. It names App internals and existing Automaton/Marshal connections, source pin `6233438`, nonblocking verify, retained Update, durable ACK and native independence. |
| Older AGENTS bullets | The “Earlier adopted requirements and history (subject to the decision above)” boundary at `:21` is explicit. Old `on_finality`, Executor/Orderer, five/four-trait and `534af0e` wording records superseded history; it is not a reason to reintroduce those roles. No blanket keyword deletion was applied. |
| `BATON_HANDOFF.md:3–13` | The current section explicitly supersedes earlier architecture and publication entries, records App-owned pool/modes/workers, current Marshal reuse and no publication of this rewrite. Dated GitBook and research-wave receipts remain historical. Their past completion claims do not close this user's 3-hour task or establish runtime correctness. |
| Root README and `docs/README.md` | Both lead to current local docs and the same one-App connection. README now directly flags unpublished GitBook differences. The backend survey is optional after the concise pool contract. |
| `IMPLEMENTATION_SPEC.md` | Compatibility entrypoint only: current source is `docs/`, older Korean section IDs route to current pages. Names such as `four-layers` or `result-certification-trait` remain intentional URL compatibility anchors, not current trait declarations. Actual target files and fragments exist. |
| `docs/SUMMARY.md` | All 32 current content pages occur once. Groups say App transactions, App scheduling, App execution/storage and Multimmit/Marshal. No removed standalone-layer page remains in navigation. |
| `.gitbook.yaml` / local generator | GitBook configuration points to `./docs/` and its README/SUMMARY. `build_docs.mjs:7,15–24` builds from those current sources and the current `docs/assets/diagrams` manifest. It does not select old root diagrams or archive pages as live site content. `site/` is generated and ignored. |
| Current live prose | Old framework names occur as explicit exclusions, historical mapping, supplied native AppExecutor, or source-specific third-party APIs. No surviving live obligation to implement public TxPool/Baton/Executor/Storage/BlockService/Orderer traits was found. |
| Old absent-Marshal claim | Every current `534af0e` mention identifies earlier research or the superseded limitation; current integration consistently pins `6233438`. Current body/order pages explicitly reuse Marshal. The paper and old source receipts retain their original pin and scope. |

## Export, diagrams and tooling

The generated `docs/assets/interfaces/baton.rs` contains the existing Automaton methods, Reporter, stage/put methods, Update value and Relay method. It contains no new trait declarations and explicitly says the excerpts are not standalone declarations or protocol implementation. The exporter reads only `rust,ignore` fences from `docs/overview/rust-interfaces.md`; `check_docs.py` verifies the exact generated concatenation.

Root separately checked the seven exported declarations against normalized pinned source and 109 current native URLs across 50 files for local pin bytes/file/line bounds. Its evidence is `rust-source-binding.json` and `current-source-links.json`. Those checks are attributed to root and do not imply remote URL availability or independent semantic proof.

All 19 current embedded Mermaid sources match the current manifest and `.mmd` assets. Current checks validate readable PNG signatures/dimensions and parseable SVGs; actual pixel inspections were recorded in the earlier visual rounds. Old root `assets/diagrams` and archived diagram manifests were deliberately not regenerated into the new architecture.

`assets/tooling/check_spec.py` still contains the earlier single-spec source pins, and `check_docs.py --migration` still checks the one-time partition against `assets/tooling/docs-migration.json` and its preserved archive. They are historical-snapshot checks, explicitly documented as such; neither is the current package `docs:check` command. The optional migration assertion requiring 39 old blank cells and preserving old citation occurrences is not a requirement to restore obsolete layer decisions in current docs. No fake migration pass or current-source validation claim was made from that tool. The ordinary checker imports only its heading-ID helper.

## Open-policy preservation

Current ordinary docs checks found 38 blank decision cells and no filled cell. Compared with the previous Git version, the only changed decision-label tables are native integration and execution responsibilities:

- Native body/fetch/backfill machinery now points to inspected existing Marshal instead of remaining an App implementation choice. Body payload/hash/limits/validity, App retention/floor coordination, scheduler bounds and native policy hooks remain open.
- Execution labels consolidate the existing exact identity, worker/access fences, backend/root, root-deferred view, recoverable state/output/applied/provenance linkage, query/material/state-sync and retention choices. “Atomic commit” became an explicit recoverable-linkage obligation, without inventing an atomic multi-store primitive.

Current prose still leaves comparator/tie-break, conflicting direction precedence, candidate generation, tail/hysteresis, codec/wire settings, signing boundary and concrete backend/pool policies open. It does not adopt per-block signing, an incumbent-first tail, inline policy bytes, exhaustive permutation, a plan-lock, arrival-time ordering or automatic cancel/reexecution. Bank semantics remain out of scope. The full native authenticated Baton adoption/preservation/continuation/recovery gap remains visible.

## Validation and untouched history

- Ordinary `python3 assets/tooling/check_docs.py`: **32 content pages, 247 local links, 19 diagrams, 38 blank policy cells, no failures**. Rechecked after the anchor moves.
- A separate root-entry link/fragment check covered **README 16**, **BATON_HANDOFF 27**, and **IMPLEMENTATION_SPEC 62** Markdown local targets, with zero failures. AGENTS has no Markdown-form local links; its required file names were present in the inventory.
- `git diff --name-only` for `baton-paper.md`, `archive/`, old root `assets/diagrams/`, prior Commonware research and prior GitBook update receipts returned no changes. They remain preserved as requested.
- No source/export/diagram mutation was needed beyond the already generated current artifacts and coordinated anchor placement. No external service was contacted or written.

No additional migration contradiction remains confirmed by this pass. Actual application/native implementation, proofs and runtime validation remain future work rather than implied by navigation or generated-artifact consistency.
