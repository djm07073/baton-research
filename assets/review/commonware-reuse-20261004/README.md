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
