# Commonware reuse research and review

Active six-hour documentation task. The source pin, baseline and full requirements are recorded in [run.json](run.json). Research reports are review material; canonical reader-facing documentation remains under docs/. Each proposal needs independent review before publication.

The latest user decisions separate transaction execution from root/storage work and avoid a dependency on glue::stateful::Application. Existing application contracts may be simplified or replaced when an actual reusable component fits. A generic queue or provider handle is not evidence of a complete mempool. A Simplex example is not evidence of an unchanged Multimmit adapter.

This record does not claim completion, protocol implementation, performance validation or six elapsed hours.

## Reviewed findings

The first wave inspected actual chain source and then cross-reviewed the other components: [body assembly](block-wave1/REPORT.md), [pool candidates](pool-wave1/REPORT.md) and [storage lifecycle](storage-wave1/REPORT.md). The second wave independently rechecked [all documentation flows](wave2/flow/REPORT.md), [pool reuse](wave2/pool/REPORT.md) and [storage/sync source](wave2/storage/REPORT.md). The flow review's [resolution record](wave2/flow/RESOLUTION.md) verifies the corrected ownership and callback references.

Tempo and Alto assemble buffered body broadcast, resolvers and archives in the node/consensus layer. Baton reuses those components through existing native callbacks, without another public BlockService trait. Native Marshal is Simplex-specific; Multimmit ordering/custody integration remains adapter work. Pool reuse must account for actual admission, selection and canonical outcome semantics. Executor produces effects; Storage prepares selected roots and owns database application/durability using QMDB primitives. Full Stateful Application adoption is not required.

Current local checks cover 31 pages, 18 diagrams, five proposed application traits and 39 intentionally blank policy cells. The [browser verification](browser-verification.json) checks image loading, English content, search, Rust declarations and mobile navigation. GitBook publication and GitHub synchronization are tracked separately in run.json; local checks alone do not establish publication or a compiled Baton integration.

## Published batch

Change request #5 is published as `NY491pkJQdX6ny2Lyndj`. The [page verification](gitbook-verification.json) and [live revision comparison](gitbook-live-verification.json) cover 38 pages, 393 links, 18 Mermaid blocks, five proposed traits and all 79 previous heading anchors. [Attachment checks](assets-verification.json) confirm accepted upload IDs and sizes against local source; raw private downloads returned HTTP 403, so remote byte equality is unconfirmed. This batch publication does not complete the ongoing six-hour goal.

## Third reviewed batch

The third wave checked [network assembly](wave3/network/REPORT.md), [Orderer proof/storage reuse](wave3/orderer/REPORT.md), [concrete branch APIs](wave3/storage-types/REPORT.md), and [ecosystem pool candidates](wave3/ecosystem/REPORT.md), followed by independent source and reader cross-review. The [final resolution](wave3/DOCS_RESOLUTION.md) binds the eight edited page hashes. Nunchi supplies a conditional whole-pool actor candidate; its nonce refresh, restart, byte packing and ingress integration remain explicit requirements rather than chosen Baton policies.

Change request #6 is published as `GltIqzIYvnV8QtVLNNNH`. Its [page verification](wave3/publication/gitbook-verification.json) covers 38 pages, 428 links and 89 preserved heading anchors. The [live comparison](wave3/publication/gitbook-live-verification.json) confirms the reviewed page identities, document IDs and file metadata. All 18 diagrams were reused, and the updated Rust comments were uploaded. The five traits and method signatures are unchanged. Upstream integration remains uncompiled and the six-hour goal remains active.

## Fourth reviewed batch

The fourth wave derives precise [startup/lifecycle](wave4/startup/REPORT.md), [pool-to-producer](wave4/pool-builder/REPORT.md), [package/constructor compatibility](wave4/compatibility/REPORT.md) and [result-certificate](wave4/certification/REPORT.md) connections. Source and reader cross-reviews are bound to [the ten final page hashes](wave4/DOCS_RESOLUTION.md). Native git package identity differs from the references' registry release, and existing certificate schemes need a result-specific f+1 adapter rather than an unchanged consensus quorum. These are conditional source/API recipes, not dependency changes or a compiled implementation.

Change request #7 is published as `VZgSSM1vxObvtUhGUVFR`. The [strict readback](wave4/publication/gitbook-verification.json) covers all 38 pages, 478 links, 18 diagrams, five traits and 94 prior section anchors. [Live comparison](wave4/publication/gitbook-live-verification.json) confirms the reviewed revision: ten updated documents, 28 unchanged documents and all existing file metadata unchanged. No attachments were uploaded. Local browser and migration checks pass; the six-hour goal remains active.

## Fifth reviewed batch

The fifth wave turns the inventory into precise existing-owner connections: [body archives/resolver](wave5/body-storage/REPORT.md), [localized pool source adaptation](wave5/pool-source/REPORT.md), [concrete root-deferred batch access](wave5/branch-access/REPORT.md), and [Baton task mechanisms](wave5/baton-tasks/REPORT.md). Independent source and reader reviews are bound to [eight final page hashes](wave5/DOCS_RESOLUTION.md). No extra generic body/pool/task/read-view engine is mandatory; conditional adapters retain their actual identity, lifecycle and root limitations.

CR8 is published as `jCIYtF1KMH1WI7GnVz2Y`. [Readback](wave5/publication/gitbook-verification.json) covers 38 pages, 498 links and 98 previous section anchors; [live comparison](wave5/publication/gitbook-live-verification.json) confirms eight updated and 30 unchanged documents with all attachment metadata unchanged. Five traits, 18 diagrams and 39 blank choices remain. No upload was needed. The six-hour goal remains active and source assembly remains uncompiled.

## Sixth reviewed batch

The sixth wave checks [result transport](wave6/result-transport/REPORT.md), [repeated QMDB sync](wave6/repeated-sync/REPORT.md), [native evidence retention](wave6/order-evidence/REPORT.md), and [commit metadata](wave6/commit-metadata/REPORT.md), with independent source/reader review bound to [eight final page hashes](wave6/DOCS_RESOLUTION.md). Existing typed P2P, sync engine, proof/archives and metadata/journal mechanisms remain underneath small application connections. Target progress, received messages and native safety snapshots each have explicit limits; they do not substitute for execution/result/delivery verification. The Tempo propagation call graph is now explicit in the body page.

CR9 is published as `NFuXtAIdglYgcndKT0Ly`. [Strict readback](wave6/publication/gitbook-verification.json) verifies 38 pages, 532 links and 98 preserved anchors; [live comparison](wave6/publication/gitbook-live-verification.json) confirms eight updated and 30 unchanged documents, all 95 file metadata entries unchanged, and no uploads. Local checks pass with five unchanged traits, 18 diagrams and 39 blank choices. The six-hour goal remains active; no compiled integration or protocol/recovery proof is claimed.

## Seventh reviewed batch

The seventh wave checks [body codec/identity](wave7/body-codec/REPORT.md), [QMDB ancestor ownership](wave7/execution-tree/REPORT.md), [existing static-selection hooks](wave7/static-selection/REPORT.md), and [local Reporter/mailbox composition](wave7/notifications/REPORT.md). Independent source and reader reviews bind [four final page hashes](wave7/DOCS_RESOLUTION.md). Existing primitives handle generic body/observer/branch/iterator work; exact context, ownership and work limits stay explicit integration contracts.

CR10 is published as `FC0fuQHY8XibiksLncT6`. [Strict readback](wave7/publication/gitbook-verification.json) verifies 38 pages, 551 links and 98 preserved anchors; [live comparison](wave7/publication/gitbook-live-verification.json) confirms four updated and 34 unchanged documents, all 95 file metadata entries unchanged, with no uploads. Five traits, 18 diagrams and 39 blank choices remain. The six-hour goal remains active; no compiled integration or chosen pool/packing/root policy is claimed.

## Eighth reviewed batch

The eighth wave checks [body receive/subscription](wave8/body-receive/REPORT.md), [public state-query proofs](wave8/state-query/REPORT.md), [runtime/future worker helpers](wave8/execution-workers/REPORT.md) and [local completion handles](wave8/delivery-ack/REPORT.md). Independent source and reader reviews bind [four final page hashes](wave8/DOCS_RESOLUTION.md). Existing primitives cover receive/wait, query verification and task completion plumbing; exact range/root/readiness, durability and worker authority remain application connections.

CR11 is published as `2KMSlL0AfmImuyvywE5i`. [Strict readback](wave8/publication/gitbook-verification.json) verifies 38 pages, 566 links and 98 preserved anchors; [live comparison](wave8/publication/gitbook-live-verification.json) confirms four updated and 34 unchanged documents and all 95 file metadata entries unchanged, with no uploads. Five traits, 18 diagrams and 39 blank choices remain. The six-hour goal remains active; no compiled integration, state-root/query format or cancellation/default policy is claimed.

## Ninth reviewed batch

The ninth wave checks [simulated-network assembly](wave9/simulated-network/REPORT.md), [native fixture reachability](wave9/native-fixtures/REPORT.md), [real-storage recovery controls](wave9/storage-fixtures/REPORT.md) and [actual two-run chain examples](wave9/fixture-boundaries/REPORT.md). Independent source/reader review binds the [final one-page change](wave9/DOCS_RESOLUTION.md). Reuse public Commonware runtime/network/sync gates for future application E2E; the fixed native Cluster, runtime fingerprints and private Simplex helpers do not substitute for application assertions.

CR12 is published as `36O47tlujxrEW9C1xjfX`. [Strict readback](wave9/publication/gitbook-verification.json) verifies 38 pages, 580 links and 98 preserved anchors; [live comparison](wave9/publication/gitbook-live-verification.json) confirms one updated and 37 unchanged documents and all 95 file metadata entries unchanged, with no uploads. Five traits, 18 diagrams and 39 blank choices remain. All nine verification cases are Not run. The six-hour goal remains active.

## Tenth reviewed batch

The tenth wave audits [body composition](wave10/body-coherence/REPORT.md), [one-pool connections](wave10/pool-coherence/REPORT.md), [execution/storage ownership](wave10/storage-coherence/REPORT.md) and [introductory wording](wave10/intro-coherence/REPORT.md). Source and reader cross-reviews bind [four precise prose changes](wave10/DOCS_RESOLUTION.md). No redundant generic engine/actor or structural change was needed. Executor/Storage/ACK responsibilities and the Nunchi paragraph’s target are now explicit from the first explanation.

CR13 is published as `SKpBMBP5bB8nbXs83CtR`. [Strict readback](wave10/publication/gitbook-verification.json) verifies 38 pages, 580 links and 98 preserved anchors; [live comparison](wave10/publication/gitbook-live-verification.json) confirms four changed and 34 unchanged documents, all 95 attachment metadata entries unchanged and no uploads. Five traits, 18 diagrams and 39 blank application choices remain. Implementation/tests remain outside this documentation batch and the six-hour goal is active.

## Eleventh reviewed batch

The eleventh wave audits original [goal/presentation coverage](wave11/goal-coverage/COVERAGE_AUDIT.md), [body reuse](wave11/body-coverage/COVERAGE_AUDIT.md), [pool/Orderer connections](wave11/pool-orderer-coverage/COVERAGE_AUDIT.md) and [execution/Storage contracts](wave11/execution-coverage/COVERAGE_AUDIT.md). Independent cross-reviews bind all final reports in [the resolution](wave11/DOCS_RESOLUTION.md). No reader edit or new generic infrastructure is needed. Engineering/proof obligations are explicitly identified without treating their implementation as an unauthorized documentation completion gate.

All 88 tracked docs files match committed d4915b3 and the local mirror; all 115 prior report hashes match. Fresh GitBook inspection confirms unchanged published revision SKpBMBP5bB8nbXs83CtR, including page/document/file metadata. Prior full readback/browser checks retain their stated scope; no native tests or remote raw-byte verification is implied. The six-hour review remains active, with a further three-agent developer walkthrough underway.

## Twelfth reviewed batch

Three adversarial developer walkthroughs inspect [body composition](wave12/body-walkthrough/REPORT.md), [one-pool wiring](wave12/pool-walkthrough/REPORT.md) and [execution/Storage integration](wave12/execution-walkthrough/REPORT.md), with independent source/reader cross-review. [Resolution](wave12/DOCS_RESOLUTION.md) binds the exact reports and final two-file comment change: selection does not establish canonical retirement. Existing destructive-backend ownership/reconciliation remains conditional; no new backend, framework, signature or policy is selected.

CR14 is published as sO0NK8i80XqUpnV6qDTu. Strict full readback verifies 38 pages/580 links/98 old anchors; fresh live comparison confirms one changed and 37 unchanged documents, 95 previous file metadata entries unchanged and one updated Rust attachment. All 18 diagrams are reused. Build/migration and changed-page browser smoke pass; broader prior browser scope is not represented as rerun or native tests. Six-hour research/review continues through the original 01:29:14 UTC window.
