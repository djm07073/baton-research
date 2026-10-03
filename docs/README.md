# Baton Docs

**Baton connects transaction handling, consensus, speculative scheduling, and execution on Commonware Multimmit.** Each module page starts with its role and responsibility, then explains Rust inputs/outputs, call flow, and detailed completion conditions. Edit the Markdown in this docs folder as the source of truth.

**For API review, start with [Rust interfaces](overview/rust-interfaces.md).** All traits are collected there, with a generated single Rust file.

## Read these pages first

| Order | Page | Purpose |
|---|---|---|
| 1 | [Architecture](overview/architecture.md) | Four layers and the data, control, and canonical paths |
| 2 | [Roles and terminology](overview/glossary.md) | Module responsibilities and completion conditions |
| 3 | [Rust interfaces](overview/rust-interfaces.md) | Six core traits, two supporting traits, and one Rust export |
| 4 | [Normal E2E](e2e/normal.md) | Transaction → block → execution result → durable state |
| 5 | [Execution responsibilities](execution/README.md) | Executor-owned state finalization and state sync |

## Documentation structure

- **Overview:** architecture, terminology, Rust interfaces, P2P, interface-reading guide.
- **Tx:** admission, mempool, static analysis, candidate selection.
- **Consensus:** Multimmit, body exchange, finalized ordered input.
- **Baton:** reports, direction authentication/dissemination, speculative block requests.
- **Execution:** planning, execution tree, Runtime, QMDB, certification, state sync, recovery.
- **E2E:** normal flow, body exchange, native consensus, leader planning, reexecution, canonical application, restart, certification, state sync.
- **Development and references:** Commonware integration anchors and development/verification plans.

The [table of contents](SUMMARY.md) lists every page. Layer pages define responsibilities and interfaces. E2E pages explain message sequences and event order.

## Adopted responsibilities

Finalized input travels directly **Orderer → Executor**. **Executor ↔ Executor** exchanges execution signatures, certificates, and change sets and owns state finalization and state sync. Baton coordinates reports, direction, and speculative work. It does not approve or gate result certification or state application.

## Document status

These are implementation-design documents with pinned Commonware source references. Protocol implementation, native integration proofs, E2E execution, and performance results are not completed. Distinguish existing Commonware APIs from proposed application contracts. Open policy decisions remain blank. The Bank application model is outside the current scope.
