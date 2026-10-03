# Wave 7 final reader review — body page

Reviewer: `/root/reuse_network_v3`. Final draft `docs/consensus/block-body.md` SHA-256 **`2b214a3e446a03214868abd64beeb9b04827692c17f49bc7310b75a6f57a142e`**. Baseline `f2973dd98598eddac73d212c2b78e04cefb311c8`. **Pass; no remaining material issue.** Root resolved the requested Rust notation clarification to `Option<R>` where `R: Reporter` before this hash was bound. Review is source/document readback, not compilation, implementation, protocol proof or publication verification.

## Source and reader checks

The full body page keeps its existing headings, callback ownership, authenticated header/body join, parent custody, missing-body pending/error distinctions, explicit Simplex Marshal incompatibility, archive owner, receiver closure semantics and Orderer evidence-delivery boundary. All baseline body lines remain in order; additions remove no prior material.

The five-row codec table matches existing Write/EncodeSize/Read and automatic Encode/Decode/Codec/CodecShared implementations. Read's selected config and complete-frame Decode check are distinct. Vec and Bytes bounds, per-item limits and full-byte constraints remain separate. Concrete buffer/archive configuration accepts the body config; resolver's unit outer envelope wraps raw response Bytes and does not require a unit body decoder. Stable representation and coherent cached bytes/digest remain application duties. Body commitment stays distinct from native header digest/block_ref and parent header reference. Existing header methods supply that identity without adopting Simplex Block/Application or a new body trait. Codec/hash/domain/limit choices remain open.

Observer prose uses existing Reporters/Option<R> and actor mailbox handles without a generic distributor. Same-Activity typing, synchronous composition, absent optional reporter returning Ok and caller-owned overflow Policy are correct. Callback success is not receiver processing or durable delivery; native dispatch still ignores feedback. Optional observation cannot gate native cut, direction, canonical delivery, execution certification or Storage apply.

The preserved Tempo propagation description was independently traced through fresh decisive assembly sources: Tempo Marshaled's Inline/Deferred Relay delegation, epoch-manager relay handle, standard relay staged proposal/forward handling, Marshal Proposed/Forward dispatch, standard Buffer::send to broadcast_shared, and buffered Engine's typed send_ref on its network channel. Tempo attaches Executor and starts the body Engine separately while passing broadcast mailbox/backfill resolver into Marshal. These release/Tempo sources support a component-composition pattern; the page explicitly rejects copying Simplex Marshal unchanged into native Multimmit or treating temporary buffering/local feedback as durable custody/remote ACK.

## Receipts and scope

`DOCS_BODY_RECEIPT.json` records all four draft page hashes, baseline hashes, unchanged headings and all eight newly added body citations. Each new citation was checked against this reviewer's fresh pinned/tree/blob-checked primary file. Nine additional fresh decisive files close the exact Tempo relay route; their hashes/blob IDs are preserved in `cross-review-source-manifest.json`. Existing body-codec/notifications source reports and independent reviews cover the surrounding API claims; actual MCP response text was independently matched, not inferred from transport success.

Other three draft pages were read for architectural coherence. QMDB additions agree with the independently reviewed ancestor-handle/root distinction. Tx deltas remain conditional pool adaptations; they do not select a backend, policy, code path or new pool actor. Tx interfaces' sole replaced baseline line adds the existing Reth predicate method; no unrelated removal occurred. Their specialist source reviews remain separate rather than claiming this scoped body review substitutes for them.

No canonical edits, public signature changes, new ACK barrier, authority handoff guarantee, storage/backend/default choice, compilation or protocol execution were performed.
