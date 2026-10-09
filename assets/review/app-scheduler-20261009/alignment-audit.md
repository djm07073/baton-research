# Companion documentation alignment audit

Review scope: current reader pages against the user decision to own TxPool and both schedulers inside one application, reusing the current Multimmit Automaton/Relay/Reporter and Marshal. This is documentation verification, not protocol testing or publication.

Inspected implementation: monorepo commit `6233438985d8249d2b2bc1204191d5d405652288`. The older `534af0e` research pin does not describe the current Multimmit Marshal.

## Initial contradictions

| Pages | Required correction |
|---|---|
| Root README, docs README/SUMMARY, glossary | Remove four-public-trait/five-role architecture as the required composition. Present one app, current native Engine and current Marshal. |
| overview/networking | Current example already registers six channels with the actual two-argument API. Distinguish Marshal body broadcast and resolver from four native planes. |
| e2e/normal, block-body | App selects from its pool, builds TransactionBlock, stages via Marshal and returns body digest. Native local verify is before signing. Relay uses header digest, full block travels through buffered broadcast. |
| e2e/block-body, reschedule | Verify runs for peer validation, own custody, recovery. True follows validity and custody, never speculative execution. Pending scheduling is app state, not a BlockService/Baton/Executor public chain. |
| e2e/canonical | Marshal already orders and delivers indexed Update with complete block and Exact acknowledgement. App does reuse/repair/apply; Baton does not rebuild ordinary delivery. |
| e2e/recovery | Current Engine::open performs recovery; start spawns actors and returns Running. App/body access must exist before open. Marshal owns its durable delivery cursor; app applied metadata is separate. |
| e2e/leader/native-consensus | Preserve native prefix-policy work as unfinished. Automaton producer callbacks do not create a leader policy hook, and app must not reorder Update. |
| e2e/results/state-sync | Preserve exact-context f+1 result and direct/imported provenance invariants inside app execution/storage code. Remove mandatory public Executor/Storage interfaces. |

## Validation tooling

- `npm run docs:interfaces` extracts every Rust fence from the canonical Rust interface page. Its fixed export prelude must stay honest about whether snippets are proposed application interfaces or existing callback sketches.
- `npm run docs:check` checks SUMMARY coverage, all local Markdown links/anchors, fences, blank decision cells, generated Rust equality and exact Mermaid source hash correspondence to `.mmd`/SVG/PNG manifest entries.
- `npm run docs:build` regenerates interfaces and builds every summary page; it fails if a Mermaid source has no rendered manifest entry.
- `--migration` is a one-time snapshot migration audit. It additionally requires historical external citation multiplicity and 39 blank policy cells; deliberate current documentation replacement must not be described as satisfying those historical retention constraints without checking them.
- Renderer: `node assets/tooling/render_spec_diagrams.cjs COMBINED_MARKDOWN OUTPUT_DIR MERMAID_RUNTIME_DIR PLAYWRIGHT_MODULE [CHROMIUM_EXECUTABLE]`. It emits numbered sources, SVG, PNG and a fresh manifest. Preserve historical `origin_snapshot_sha256` provenance; update `source_pages` separately if retaining that metadata.
- Existing assets use diagram-02/03 normal, 04/05 body, 06/12 leader, 07 reschedule, 08/09 canonical, 10/13 recovery, 11 results, 14 state sync and 15 native consensus. Embedded sources and `.mmd` will be changed together; global renders wait for all authors.

## Assigned companion edit scope

This reviewer owns `docs/e2e/*`, `docs/overview/{glossary,networking}.md`, `docs/README.md`, `docs/SUMMARY.md`, and root `README.md`. Root owns Baton and canonical architecture/interfaces; other reviewers own execution/Tx/baseline and consensus/reference. Historical paper, archives and previous review receipts stay preserved.

## First rewrite and self-review

All assigned companion pages are rewritten around App + Engine + Marshal. Existing E2E sequence heading anchors remain where their topic still applies. No new public App subsystem trait or actor is prescribed. All 14 owned Mermaid `.mmd` sources match their embedded fences; global render is intentionally pending the other authors.

Direct source checks covered current example six-channel assembly and two typed App handles, `Service`/buffer/resolver wiring, `stage_block` versus `put_block`, subscription versus explicit fetch, `Update`, `Exact`, delivery's `Feedback::Closed` handling, contiguous ACK capacity release and cursor sync, and current `Running::ready() -> Result<(), Stopped>`.

Self-review results:

- `git diff --check`: pass after first rewrite.
- `npm run docs:check`: current-page links/anchors pass; two root-owned compatibility anchors were missing and reported to root. Mermaid renders/manifest are expected stale until the combined render. This intermediate failure is not a final successful check.
- Removed mandatory public layer names from live ownership paths. Remaining old names in glossary explicitly map the previous design to current App/Marshal responsibilities.
- Preserved incomplete native Baton policy/adoption/preservation/recovery status; no App-only scheduling claim changes canonical order.
- Preserved exact-parent reuse, pending-only sorting, fixed report snapshot/support thresholds, direct/imported provenance, f+1 result endpoint and separate durable ACK endpoint.
- Root draft cross-review found no substantive connection/ownership conflict. Reported `Engine::ready()` typo and absent-local-producer-lane condition for correction.

The paper, archives and historical publication/review receipts remain untouched by this reviewer. No protocol code, runtime tests, benchmark, commit or external publication was performed.
