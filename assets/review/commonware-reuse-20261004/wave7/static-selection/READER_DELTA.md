# Proposed reader delta — not adopted edits

Baseline `f2973dd98598eddac73d212c2b78e04cefb311c8`. Keep existing headings, diagrams, interfaces and policy tables. No Rust declaration change is needed.

## docs/tx/interfaces.md

In the existing backend mapping select row, Reth's dependency-aware iterator can name `BestTransactions::filter_transactions`. One paragraph after that table is enough:

> For a packing overlay, Reth already exposes a predicate wrapper around its best iterator. Rejected entries invoke the iterator's dependency control; the base implementation excludes entries locally without deleting them from the pool. An ordinary filter after yielding a predecessor does not preserve this behavior. A returned-count limit after filtering does not bound visited candidates or static-analysis work. Keep analysis on immutable payload facts and connect the chosen body-byte/work limits without introducing another pool actor. [Public predicate](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L1175), [filter loop](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/pool/best.rs#L337), [base iterator exclusion](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/pool/best.rs#L124).

## docs/tx/README.md

In the existing Nunchi paragraph describing pending/packing, add:

> `pending(limit)` truncates before a wrapper filters candidates. Repeated calls rotate ready-lane starts, rather than paging further into the same lane. A filtered limited prefix can therefore hide later entries until canonical or pool state changes; excluded nonce predecessors can also make their successors ineligible. Filtering before truncation, if required, belongs in the existing Pending message/kernel, with its contract and limits still undecided. [Pending walk](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L160).

In the existing Constantinople destructive-selection paragraph, append its lane-head caveat: selection pops whole batches and stops a lane when its head exceeds remaining tx-byte budget; it does not search smaller later entries. Its existing retention/cancellation warning remains necessary. [Whole-batch pop](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L406).

One sentence near the existing Reth/Tempo comparison gives the real chain example: Tempo filters immutable payment content and checks encoded block size inside its existing body builder while retaining the pool/iterator composition; its state-aware wrappers and execution builder are not adopted. [Content classification](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/payload/builder/src/lib.rs#L590), [Size filter](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/payload/builder/src/lib.rs#L616).

## docs/reference/integration.md

Only if its existing pool assembly row needs the hook spelled out, name the selected Reth best iterator/predicate beside the existing complete-pool candidate. Do not add a new primitive/actor/trait row. Keep source-port compatibility, whole backend lifecycle and canonical refresh caveats. No new generic scan engine, cache, reconciliation actor, policy defaults, budgets or backend choice.
