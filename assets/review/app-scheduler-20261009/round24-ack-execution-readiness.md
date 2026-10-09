# Round 24: ACK, execution and read readiness

## Disposition

No current page makes direct local application/ACK depend on Baton reports, advisory direction, or peer result signatures. No inspected page calls an accepted/queued Update an applied state. One E2E heading still used the ambiguous phrase “execution commit”; I changed it to “Native finality → ordered delivery → durable App application” in `docs/e2e/canonical.md:7` and preserved the old `cut-commit--ordered-range--execution-commit` slug explicitly. The sequence body already has the correct durable boundary, so no Mermaid or asset change was needed.

The detailed callback contract remains authoritative in `docs/baton/interfaces.md#marshal-reportupdate-canonical-input-and-ack`. The heading fix adds no repeated contract or new approval boundary.

## Reader trace

| Milestone | What is established | Authoritative current explanation |
|---|---|---|
| Native finality and Marshal ordered delivery | The input has native ordering authority, with exact index/block identity. It has not become App state merely by reaching the inbox. | `docs/baton/README.md:70`, `docs/baton/interfaces.md:91–118`, `docs/e2e/canonical.md:43–47` |
| Speculative completion | Reusable exact input/parent/runtime effects may exist; root preparation, canonical applicability and durability remain separate. | `docs/baton/interfaces.md:65–87`, `docs/overview/glossary.md:37–39`, `docs/e2e/canonical.md` execution-lifecycle section |
| Local durable canonical application | State, required outputs, applied position/identity and provenance have the recoverable linkage required by App. Exact matching speculation can be selected without reexecution; otherwise execution/repair or verified import is necessary. | `docs/baton/README.md:70–72`, `docs/baton/interfaces.md:100–115`, `docs/execution/qmdb.md:115–129` |
| Delivery ACK | App signals that same exact durable application. It is an in-memory signal, distinct from native consensus and from Marshal's subsequent cursor sync. | `docs/baton/interfaces.md:124–131`, `docs/e2e/canonical.md` What the ACK waits for |
| Result certification | Irrevocable exact input/base/runtime and f+1 distinct eligible matching signatures establish the adopted research result endpoint. Direct apply/ACK can progress while signatures are collected; import additionally needs verified applicable certified material. | `docs/baton/interfaces.md:135`, `docs/execution/interfaces.md:54–66`, `docs/e2e/results.md:36–40` |
| Local query/read readiness | The selected state, value/proof/root and applied identity need matching valid read authority; a live readable database, a certificate or a root alone does not prove durable completion or establish the query contract. | `docs/e2e/results.md:40`, `docs/execution/qmdb.md:125–133` |

Line references are the review snapshot; stable headings above remain the navigation targets.

## Adversarial reader checks

- A block only retained by `report(Update)` cannot be ACKed as durable merely because callback Feedback returned. The core event table explicitly calls this retained handoff, and the E2E sequence shows the worker's later storage completion.
- A valid speculative result on the wrong parent is not reusable by block identity alone. Exact reconciliation precedes apply.
- A directly executed block can become durably applied and ACKed without an f+1 certificate. Core `interfaces.md:135` states this explicitly; the result-certification sequence deliberately does not represent the canonical ACK path.
- An imported result is different: the certificate and applicable material must both be verified before using that import. This requirement does not add a signature wait to the direct path.
- Empty report windows or missing directions cannot gate canonical work. `interfaces.md:120` disallows the approval dependency; `:143` likewise excludes scheduler approval and an extra ACK protocol.
- ACK does not imply Marshal's cursor is durable. Crash replay validates exact index/block/applied identity; no duplicate effects are permitted.
- Readable application before a flush finishes does not justify ACK. The QMDB page separately binds query access and recoverable application completion; query scope and historical retention remain open rather than being chosen by this review.

## Local source cross-checks

- `consensus/src/multimmit/marshal/actors/delivery/actor.rs:303–379`: synchronous reporting constructs `Exact`, records the waiter, and later handles acknowledgement readiness and separate durable cursor completion. The library does not itself execute App transactions or inspect peer result certificates; the App's durable-before-ACK meaning is its design obligation.
- `consensus/src/multimmit/marshal/actors/delivery/acks.rs:107`: completed acknowledgements retire the continuous front of the pending window, independently of the later cursor-sync state.
- `glue/src/stateful/db/mod.rs:210`: a reader acquires a guarded live database. It is not a pinned historical checkpoint or an execution certificate.

Validation after the heading/anchor edit: `npm run docs:check` passed (32 pages, 252 local links, 19 diagrams, 38 preserved blank policy cells); `git diff --check` passed. No native tests, rebuild, rendering or external writes were needed.
