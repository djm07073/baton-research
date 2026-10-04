# Wave12 independent pool and execution walkthrough review

**Pass. The single TxPool comment correction expresses the intended canonical-outcome boundary without selecting a destructive backend. The execution walkthrough warrants no reader delta.** Reviewer `/root/reuse_network_v3`; exact report/page/source bytes are bound in `independent-cross-review/CROSS_REVIEW_RECEIPT.json`.

## Bound reports and freshness

- Pool REPORT `8c7324b80584009ef8eece36a75b4caa143b0e09e4ed0e1216d3f20be1ac5a4f`; delta `6a521ed8cf6b63276f5064ea4186b9be971d20cec3fabb05ba2d23785c665405`.
- Execution REPORT `512b59dc00c583606bcb70edc9dc67f19a0cc1765fd5a78b1f83d5f2deb90fb7`; delta `4044ce103d2719f2381ebdf0302c53f9a50e7a64be800472832c26ade7463234`.
- Root review `81c40939eb958460b1b5809c32915ae17376f86eb795a89e740e273c36c9c754`.

Two decisive Constantinople raw files were independently fetched at pin `3b6c92e76bf582855615844a4175b8304808f6a9` and Git-blob checked against this reviewer's retained authenticated complete wave10 tree. That tree is explicitly not a new wave12 retrieval. Five decisive native execution files were rehashed and reread against the retained pin/tree receipts; no fresh native retrieval is claimed. No new API uncertainty justified repeating the previous catalog.

## Pool comment adoption

The source establishes an actual destructive **candidate transfer**: private `pop_lane_proposal` removes whole entries, reduces queue byte accounting, stores only proposal digests/height, and returns transaction material (`actor.rs:402–435`). This is distinct from canonical execution or durable pool processing. Public `try_submit` returns an eventual batch-status receiver, while `try_ingest` is `pub(super)` and reports admission (`mailbox.rs:108–158`). Thus neither queue removal nor that submission handle implements the proposed durable `CommitResult` contract.

The current detailed pages already require retained selected bytes, cancellation/reselection ownership and outcome reconciliation (`tx/README.md:25,31,63`; `tx/interfaces.md:9,33–40`). They distinguish on_proposal from on_commit and non-destructive Nunchi candidates/selection-local Reth invalidation from this conditional source route. Replacing “Selection alone does not retire transactions from the pool” with **“Selection alone does not establish canonical retirement”** removes a misleading prohibition on physical candidate-queue removal. It does not authorize losing selected material, declare successful execution, impose reinsertion, select a backend or relax durable outcome processing.

The actual current draft changes exactly that comment in the canonical Markdown and generated export. Canonical SHA `0dfb0fd427edbc031e1ba30a4ab3c3dd5ab3e9958dde7fe5bead690a2360fb42`; export SHA `91481bfad6d4cdadca4dfd22835fd8d597079e151f2a36d18f02c09f13dd73f5`. Read-only extraction independently reproduces the export exactly. Five public traits and all method/type signatures remain unchanged. No additional reader wording is needed.

## Execution walkthrough sufficiency

The report's decisive source boundaries fit actual APIs: DatabaseSet's unsealed tuple is merely Send, its sealed tuple Clone/Send/Sync, fork_batches accepts the sealed parent, and finalize returns a durability Barrier with documented cancellation loss (`db/mod.rs:508–567`). Concrete Any get accesses the applied DB, stage consumes its wrapper, and write records mutations (`db/any.rs:110–152`). These APIs do not supply generic rootless multi-child snapshot access, freely cloneable unsealed drafts or application signing subjects. The existing reader explicitly supplies the necessary ownership, retained effects and exact branch/root context seams rather than implying a second universal storage engine.

QMDB sync returns a reconstructed DB; reached-target precedes journal sync, reconstruction, root verification and persistence (`sync/engine.rs:730–803`). The reader correctly separates progress, returned candidate DB/material, application authorization and canonical writer installation. It does not assert that this raw DB is a sealed tuple or the proposed retained PreparedResult. Existing certificate/material-before-switch, direct/imported provenance, exact-order checks and recoverable state/output/cursor linkage remain required; Baton introduces no approval or result relay.

All thirteen page hashes in the execution report match the reported d491 baseline. Current bytes remain identical except the subsequently adopted central TxPool comment; this is a temporal baseline difference, not a false report receipt or an execution change. Current relevant E2E/Storage/Executor text and diagrams preserve direct Orderer→Executor delivery and Executor's durable ACK. No omitted helper or adapter was found that calls for a new public trait, actor or reader page.

## Scope

These are source-grounded hypothetical reader walks, not compiled wiring, executed transactions or proof closure. Concrete backend/type/codec/ownership/import/recovery choices remain open. Implementing or proving those engineering follow-ups is outside this documentation research completion gate. The original concrete assembly research, repeated independent review for the full window through **01:29:14 UTC**, and verified publication/synchronization remain required; this scoped pass does not complete that goal early. No canonical edit, test/build, implementation, dependency change or publication was performed by this reviewer.
