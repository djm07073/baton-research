# Baton Docs

**Connect one App to the existing Multimmit Engine and Marshal.** The App owns TxPool, a Pre-cut or Baton scheduler, transaction execution and durable state. Existing `Automaton`, `Relay` and `Reporter` connections provide the native boundary; there is no required new BlockService, Orderer or public Executor trait.

## Read these pages first

| Order | Page | Purpose |
|---|---|---|
| 1 | [App and Multimmit](baton/README.md) | The composition and what the App must implement |
| 2 | [Transaction admission and selection](tx/interfaces.md) | App pool operations, stable body packing and canonical maintenance |
| 3 | [Callback behavior](baton/interfaces.md) | `Automaton::propose/verify` and Marshal `Reporter<Update>` |
| 4 | [Scheduler behavior](baton/direction.md) | Pre-cut and Baton, candidate admission, dispatch and confirmed-order repair |
| 5 | [Normal E2E](e2e/normal.md) | Transaction → block → speculative work → Update → durable state |

Use [Architecture](overview/architecture.md) for the ownership diagram and [Rust interfaces](overview/rust-interfaces.md) for existing signatures. The [pool backend survey](tx/README.md) provides optional reuse evidence after the App pool contract.

## Documentation structure

- **Overview:** ownership, terminology, existing interfaces and message paths.
- **App transactions:** admission, retained candidates and body selection inside the App.
- **Multimmit and Marshal:** native Engine, complete-block exchange and finalized ordered input.
- **App scheduling:** callback integration, Pre-cut/Baton behavior and the remaining native Baton-policy extension.
- **App execution and storage:** exact-parent work, QMDB, result certification, canonical apply and state sync.
- **E2E:** concrete producer, verification, scheduling, Update/ACK and recovery sequences.
- **Baselines:** [Pre-cut](baselines/precut.md) as a separate scheduler mode with no Baton instance or messages.
- **References:** source anchors, implementation obligations and planned verification.

The [table of contents](SUMMARY.md) lists every page. Markdown is canonical; site assets and the single Rust export are generated from it.

## Adopted responsibilities

The ordinary confirmed path is **Multimmit Activity → Marshal → App Update reporter → App canonical worker → durable state → ACK**. The App's selected scheduler registers valid eligible pre-cut work without waiting for its execution inside `verify`. When Update arrives, the App preserves that exact indexed order and reuses or repairs its speculative path.

Baton mode adds reports and advisory direction within the App. Changing native agreed order still requires an authenticated proposal-policy extension with preservation, continuation and recovery proofs. The current callbacks and Marshal are reusable now; they do not provide that missing Baton protocol extension automatically.

## Document status

These pages describe a proposed transaction App connected to inspected existing native code. App implementation, modified Baton native integration, E2E execution and performance results are not complete. Current integration references use monorepo commit `6233438985d8249d2b2bc1204191d5d405652288`; older research sources remain identified separately. Backend, comparator, wire and resource policy decisions remain open. The Bank application model remains outside scope.
