# Round 17: pool/propose lifecycle and comparison reading flow

Reviewer: `/root/docs_alignment`. Read the current transaction contract/survey, App composition and proposal description, body E2E, PreCut baseline, documentation entry route and table of contents. This review treats pool behavior and comparison assumptions independently of the detailed callback-owner audit. No current content contradiction or unnecessary mandatory adapter layer was found; no document or diagram edit was needed.

## Lifecycle counterexamples checked

| Reader scenario | Required behavior and current evidence | Result |
|---|---|---|
| A valid peer/canonical block contains a transaction absent from the local pool or classified locally as unselected | `tx/interfaces.md:17` explicitly limits pool membership/selection/readiness to this node's proposals. Blocks use agreed payload-validity rules without local admission/selection prerequisites. `:13` distinguishes stateless validity, local immutable-payload classification and live readiness. | Clear separation. The text does not silently elevate a local selected/unselected policy to consensus validity or choose an open payload rule. |
| An RPC and a peer submit the same kind of candidate | `tx/interfaces.md:13` applies the same admission classification to both paths. `tx/README.md:57` warns that Nunchi's built-in peer path does not automatically run a wrapper policy, and forwarding it through local submit can change gossip behavior. | Both paths must actually connect the selected policy. No second pool is introduced to compensate for a missed ingress hook. |
| A producer selects bytes, then pool replacement/concurrent admission/proposal cancellation occurs | `tx/interfaces.md:15,22–25` retains stable selected encoding and the accepted body/custody association. The survey `:47` explicitly says Clone/Send/Sync does not ensure byte immutability under interior mutation; `:67` says outstanding digest bookkeeping alone does not retain canceled proposal material. | The already built body's commitment cannot change. Retained bytes and cancellation/reselection work are an internal backend adaptation, not a public cancellation protocol. |
| A destructive backend pops candidates before native publication succeeds | `tx/interfaces.md:47` requires retained bytes and canceled-proposal reconciliation. `tx/README.md:29,35,67` distinguishes selection pop/status from canonical cleanup and calls out aggregate pending-material limits. | Selection behavior is conditional backend evidence. It does not weaken App's retention contract or imply a second candidate store is mandatory. |
| Stage is accepted, verify returns true, or the body is published, but the transaction never durably applies | `tx/README.md:7,17` and `e2e/block-body.md:84` tie retirement/refresh to durable canonical outcomes, not publication/verify/selection. `e2e/block-body.md:37` distinguishes accepted staging from successful custody. `tx/interfaces.md:31` preserves selected bytes → body → contextual header → applied outcome correspondence. | No premature canonical retirement. Native block custody and pool candidate readiness/retention remain different lifecycles. |
| Pool maintenance is lost or crashes after canonical application and before backend refresh | `tx/interfaces.md:29,45` requires replay/reconciliation from durable outcomes before trusting readiness. `tx/README.md:49` gives the concrete lost-lane update and initial nonce-hydration hazard. `baselines/precut.md:104` preserves internal outcome reconciliation. | The update is not assumed processed because it was enqueued. Pool-processing completion does not add an ACK gate to canonical delivery, native cut or direction. |
| A bounded selection filter skips an excluded dependency or inspects arbitrarily many entries to fill a batch | `tx/interfaces.md:10,15` bounds visited work, encoded full-body bytes and returned count, and forbids bypassing an excluded required predecessor. `tx/README.md:45` explains pre-filter truncation and intentional underfill; `:51,65` retain bounded decoding/ingress checks. | Count-only selection is not claimed sufficient. No full-batch-fill liveness promise or chosen packing policy is invented. |
| Several producers include the same transaction, or a cache already has its bytes | `tx/README.md:33,65,69` distinguishes local duplicate suppression, canonical replay semantics, body/cache availability and canonical outcomes. Duplicate execution semantics remain an open App choice. | A cached duplicate is not treated as already executed, and no local pool rule is used to silently choose canonical transaction semantics. |

The selected/unselected distinction is readable as one pool's logical policy classes. It does not require two stores, actors or physical peer connections. Static payload facts are consistently distinguished from canonical nonce/balance readiness and transient node load.

## Minimal composition and conditional adapters

`baton/README.md:21–23` permits ordinary files, concrete scheduler implementations or a local mode enum inside one App. `tx/interfaces.md:3,37` chooses concrete pool operations and one fitting candidate store. The survey's `TransactionSource`/outcome adapters are conditional conversions for a selected external backend's real Header/Round/canonical-update types; they are not new public layers between every App and Multimmit.

The same distinction holds for Nunchi's existing Message/handle/handler (`tx/README.md:47`), an optional bounded ingress seam (`:55–57`), and an inventory/admission bridge only if announced-hash propagation is selected (`:65`). The source already supplies a pool or transport mechanism; App supplies its exact classification, encoding and lifecycle connection. `:21` explicitly avoids running a reusable backend beside another custom pool, and `:47` rejects a separate reconciliation actor as a requirement.

The Rust names `PoolTransaction`, `TransactionSource`, and Reth's maintenance APIs refer to actual conditional ecosystem interfaces. Their presence does not restore the superseded public TxPool/Baton/Executor/Storage architecture.

## Original / PreCut / Baton reader path

The first-reader route in `docs/README.md` leads from App composition to `tx/interfaces.md`, callbacks, scheduling and normal E2E. It labels the longer `tx/README.md` as an optional backend survey. `docs/SUMMARY.md` likewise lists the pool contract before the survey, with the baseline in its own comparison section. An implementer can understand the App pool contract without first choosing an ecosystem backend.

`baselines/precut.md:116–124` is explicit:

- **Original:** transaction execution starts on ordered Update and uses ordinary native Multimmit/Marshal order.
- **PreCut:** eligible-candidate speculation begins when its exact execution parent is ready; canonical order remains the same ordinary native order.
- **Baton:** the same ordinary speculative start gains report/direction work and the still-required authenticated native policy extension for the complete research objective.

Original is a comparison configuration, not a mandated third scheduler framework. PreCut is explicitly independent of any Baton instance, report window, direction exchange or report-dependent policy (`:3–5`). Both speculative modes share the pool, body/custody, transaction backend, storage, result protocol and measured endpoints. The baseline diagram uses existing callbacks, Marshal and App-internal responsibilities; it does not introduce a separate Orderer or replacement body service.

Fairness includes committee/topology/workload, pool/body behavior, native profile and cut cadence, pending rule, execution/storage backend, root/checkpoint boundaries, worker limits and budgets (`:122`). Result import capability/configuration stays matched, with direct repair versus imported completion measured separately (`:110–112`). Endpoint distributions, throughput, total discarded/reused/import/hash/network/storage costs and deterministic output/root checks remain explicit (`:124`). Earlier proposals/frequent cuts are separate sensitivities; advisory-only Baton is not proof of protected-prefix integration. No result or performance advantage is claimed.

## Historical source reuse remains conditional

The survey explicitly marks compatibility with the current Multimmit graph as uncompiled (`tx/README.md:15,53–55`; `tx/interfaces.md:47`). It retains fixed transaction/context types, destructive lifecycle issues, SDK/commonware dependency mismatch, bounded ingress requirements and Ethereum-specific provider/runtime assumptions. Nunchi, Constantinople and Tempo/Reth are source-adaptation alternatives, not selected production backends or newly researched recommendations.

All GitHub source links in the two transaction pages name a full 40-character revision: 42 links in the survey and 4 in the concise contract. This local syntax check confirms pinning, not external source availability, current product suitability, Rust compatibility or semantic correctness of the external code. No external repository was fetched and no fresh backend recommendation was made.

Backend, transaction identity/codec, duplicate behavior, admission-response durability, classification, numerical limits, transport, cancellation/reselection and physical retention remain open decisions. The reader path does not force a default while demonstrating the required App connection.

## Validation and disposition

No content fix was warranted, so no unchanged diagram, build or protocol check was rerun. The review used current prose/diagrams and narrow terminology/link-pin inspection. It claims design consistency only; actual pool adaptation, mode implementations and matched benchmarks remain planned work.
