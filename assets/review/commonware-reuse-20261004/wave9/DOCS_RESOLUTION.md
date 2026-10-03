# Wave 9 documentation resolution

Baseline `f29c8c9e98cb9f3e9f1d90a1860ae96d52cbd2ea`. Previous goal batch was progress: wave8 GitBook publication, exact GitHub SHA verification and local mirror synchronization. The user’s Tempo propagation question was separately checked against actual source. The requested six-hour window remains active; this publication is a reviewed batch, not goal completion.

## Adopted change

Only `docs/reference/verification.md` changes. It maps public deterministic runtime, simulated P2P and delayed-sync controls to future real application E2E, then shows Tempo’s actual execution/channel assembly and Alto’s two-run durable queue replay. Reuse public primitive handles and application callbacks instead of a new transport, test runtime or crash simulator. Native `multimmit::mocks::cluster::Cluster` is public with fixed mock attachments, so actual body custody, Orderer delivery and Executor/Storage require direct public Engine binding. No new public trait, production actor or default policy is added.

Four source reports underwent independent cross-review. Final reviews resolve the exact Cluster path, the `Blob::start_sync` gate boundary and comparing Auditor fingerprints; three independent reader reviews bind the final page SHA `fcb5f87d3fe5b6ed98259b406004f54c26619d9974fde95c4c14df658062231b`. The report hashes below identify actual final reviewed bytes, including the native report’s narrow import-path correction.

- [fixture-boundaries/REPORT.md](fixture-boundaries/REPORT.md) — SHA-256 `241415f69039956b7a8e552b98f9127d94eeb05092023de1faceffcde70c9a5f`.
- [native-fixtures/DOCS_GLOBAL_REVIEW.md](native-fixtures/DOCS_GLOBAL_REVIEW.md) — SHA-256 `edc9fec5427761eb7748f125a206f1dcbdcbf338d490f3d35a745381861baf86`.
- [native-fixtures/NETWORK_STORAGE_ROOT_CROSS_REVIEW.md](native-fixtures/NETWORK_STORAGE_ROOT_CROSS_REVIEW.md) — SHA-256 `70618010c62105a3b07df842499fa5dce33bb168ccca93ba62850f3bb082da2e`.
- [native-fixtures/REPORT.md](native-fixtures/REPORT.md) — SHA-256 `29eb5f5dbd2abb10da77270cc034f310443cb8de73cec11900186c63618362ae`.
- [simulated-network/DOCS_NETWORK_ACK.md](simulated-network/DOCS_NETWORK_ACK.md) — SHA-256 `ff137a04aa30ca9d1659286769195c907cbe5adf59b472f0cb816ac29714717f`.
- [simulated-network/REPORT.md](simulated-network/REPORT.md) — SHA-256 `11af5383234d8d031c5e5cdb6e41da9a8fe9a63027e15f18fcba8611e6361aaf`.
- [simulated-network/STORAGE_NATIVE_CROSS_REVIEW.md](simulated-network/STORAGE_NATIVE_CROSS_REVIEW.md) — SHA-256 `32a534f40fcf05876cbe0ba0d01f0a4e17fc0e06c1e829ffc90f6fa660ae7f60`.
- [storage-fixtures/DOCS_STORAGE_ACK.md](storage-fixtures/DOCS_STORAGE_ACK.md) — SHA-256 `05094f9b68142dcf3ef760b9fdbdc4fa23ac1fc8b44bbd1d28e9436b3cb807c8`.
- [storage-fixtures/NETWORK_ROOT_CROSS_REVIEW.md](storage-fixtures/NETWORK_ROOT_CROSS_REVIEW.md) — SHA-256 `1837f16a1eab1f1f0aa64cb0c1f17e9f8f68798996cbd6adf7008eb8b2872b02`.
- [storage-fixtures/REPORT.md](storage-fixtures/REPORT.md) — SHA-256 `ca96c73745e96d3c59b885a8bb4c30ed29c7a0afb0d6805b77471ffe92b45ebc`.

## Verification and publication

Local build, migration and browser checks pass: 31 pages, 257 local links, 18 diagrams, five traits, 30 methods and 39 blank choices. All 32 Markdown headings/old source URLs and Rust/Mermaid blocks are preserved; all 56 non-Markdown docs assets remain byte-identical. Browser checks cover all pages/images, Rust, search and mobile navigation. Root inspected the new verification-page screenshot. Root fetched nine primary files against three fresh complete pinned trees and checked 14 introduced anchors; independent reviews also freshly check source fit.

GitBook CR12 `O83KZMexKQYIp2XEzHmj` is published as `36O47tlujxrEW9C1xjfX` from reviewed draft `dcd53ylFybyBc9OzY7qb`. Strict readback verifies 38 pages, 580 links, 18 Mermaid blocks, five traits and 98 old anchors. Fresh live comparison confirms one changed and 37 unchanged documents and all 95 file metadata entries unchanged. Nineteen existing SVG/Rust assets were reused; no upload occurred. Raw private remote attachment bytes remain unconfirmed. GitHub/mirror receipts are separate.

## Preserved boundaries

All nine verification cases remain Not run. No application integration, native compile/test, benchmark or proof was executed. Native and registry package identities remain separate; native-only completion_delayed is not attributed to the inspected release. Runtime checkpoints/traces and per-engine restart differ from application receipts, device failure coverage and arbitrary external determinism. Actual state/output/cursor/provenance, f+1 full-subject certification, direct/imported signing, exact order, one writer/fencing and body custody need application assertions. Executor/Storage/Baton boundaries, no-wait cut behavior, the adopted native pin and open prefix-adoption/continuation/recovery work remain unchanged. The six-hour goal is active.
