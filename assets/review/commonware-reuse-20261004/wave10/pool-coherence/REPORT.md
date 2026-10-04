# Wave 10 — one pool, existing actor connections

Baseline `01cf73b41dedd81614237977e4edf150c7d19a81`. Source/documentation audit only; no implementation, compilation or native test execution.

## Finding

The current reader pages already describe the intended connection: choose one compatible existing pool, retain its lifecycle owner, attach application admission/static payload hooks, select candidates through its existing handle/iterator, pack one retained body, and send durable canonical outcomes back to that same pool. No remaining instruction to construct a parallel generic mempool or dispatcher was found in the audited pages. Adding another inventory or new module would repeat the established recipe.

One small connector is misleading. `docs/tx/interfaces.md` places “For that conditional source route” immediately after the Reth packing-overlay paragraph, but the following Message/handle/oneshot, `finalize`, nonce hydration and TTL discussion belongs to the Nunchi source-adaptation route. Replace only that opening with “For a Nunchi source adaptation”. This explicitly identifies the already conditional candidate without choosing it.

## Existing seams are sufficient for the reader

- `tx/README.md` retains a fitting whole actor and states that backend reuse replaces candidate storage/selection rather than adding another pool. Its Nunchi source route retains the existing private kernel/owner and excludes the SDK chain builder.
- `tx/interfaces.md` already maps admission, static hooks, selection, proposal outcomes and durable canonical outcomes to one chosen backend. It separates eventual Constantinople batch status from admission completion, Nunchi notification from processed completion, and cloned/iterator selection from destructive ownership.
- `consensus/block-body.md`, `e2e/block-body.md` and `reference/integration.md` already connect candidate selection to producer callbacks and existing dissemination/archive components. Count selection is not full-body byte packing, and omitted predecessors require successor exclusion/re-evaluation.
- The normal E2E sends canonical outcomes directly from Executor to TxPool. Its separate admission/candidate-storage lifelines show logical responsibilities within TxPool; neither the page nor the architecture prescribes two pool actors. Existing architecture prose explicitly treats boxes as responsibilities rather than a process per box. No diagram change is needed.

Direct routing versus a packing overlay, workload, backend, static policy and limits remain open. Live nonce eligibility belongs to the selected pool's stateful lifecycle and does not turn nonce/balance/load into payload-static features. None of these candidate APIs establishes global exactly-once execution, native custody, processed canonical completion, or restart readiness.

## Fresh decisive source checks

All 17 saved raw source files were independently matched to Git blobs in five newly fetched complete, nontruncated pinned trees; see `source-manifest.json` for bytes and identities. This wave introduces no new upstream API claim or citation into the reader pages.

Nunchi's public `pending(count)` returns a mailbox snapshot of cloned contiguous nonce candidates. `finalized` is a fire-and-forget `try_send`; the actor applies it through the same owner. Its private `finalize` updates digests/nonces, advances height and runs TTL, including when the digest list is empty. This validates that the last interface paragraph is specifically about Nunchi rather than the preceding Reth route. [Handle](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs#L177), [kernel selection](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L160), [canonical/TTL handling](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/pool.rs#L211).

Reth's public predicate wrapper invokes `mark_invalid` for rejected entries, and the base best iterator locally excludes the sender/dependents. That hook permits the existing conditional packing discussion, without prescribing pool removal or choosing a workload. Constantinople's public `try_submit` receiver resolves eventual batch outcome, not admission acceptance, and its actor's whole-batch candidate removal remains a different ownership contract. [Reth predicate](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/traits.rs#L1175), [iterator exclusion](https://github.com/paradigmxyz/reth/blob/038edab20dfff017f7a7502e683c732e5628ad89/crates/transaction-pool/src/pool/best.rs#L124), [Constantinople outcome](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/mailbox.rs#L112), [candidate removal](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs#L424).

Native header identity, actual Commonware graph compatibility and source-port work remain explicit. This review does not turn the SDK's registry dependencies or a chain's execution-dependent builder into unchanged native components. It confirms the existing documented seams, not a compiled integration or a completed six-hour goal.
