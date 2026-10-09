# Round 10: native/body diagram semantics

Source pin: `6233438985d8249d2b2bc1204191d5d405652288`, inspected 2026-10-09. Reviewed the current `docs/assets/diagrams/diagram-{04,05,15,16}.mmd` and their embedded Mermaid/adjacent reader text. Top-level `assets/diagrams/` contains older snapshots and was not treated as the current reader source. This round checks semantics, not visual layout or a runtime protocol execution.

## Confirmed corrections

1. **04 completion type.** The caller arrow allows either `subscribe_block` or waiting for a retained custody token. Its old reply label, “Durably recoverable complete block,” fits subscription but not Custody::wait: the latter returns Result<(), Error>. Use “Durable custody established” as the common completion. App already holds its locally built complete block.
2. **05 optional fetch.** The old diagram put an optional fetch between subscribe and an unqualified “Durable complete block” reply. Label that reply explicitly as successful subscribe completion and say optional active fetch can run concurrently. Fetch success can expose buffered bytes before sync; it does not itself establish the custody fence. Preserve the existing no-execution-wait rule.
3. **15 independent native work.** The old Native protocol branch placed DA certificate publication before leader proposal, despite a note saying they are independent. Split Native DA and Native view/finality into parallel branches using the existing participants. Add a short scope note that the view machinery may already be running during producer validation. A particular lane inclusion still obeys native eligibility; this does not make proposal contents unconstrained.

These exact changes were sent to the E2E owner. Diagram16 needs no semantic change. No extra participant, driver, service or new API is required.

## Diagram04: local proposal and dissemination

| Arrow/result | Source assessment |
|---|---|
| Native producer → App propose(Context) | Correct: private AppExecutor::build constructs producer epoch, chain, next height and parent-header digest, calls Automaton::propose, then awaits its body-digest receiver (`actors/voter/actor/app.rs:83–116`). |
| App → TxPool selection → body construction | Proposed App responsibility, not native functionality. The diagram correctly locates it inside App. `TransactionBlock::from_context` commits the supplied body's digest (`types/block.rs:284–293`). |
| App → stage_block → accepted Custody token | Correct: stage accepts router/catalog work and returns its completion token (`marshal/mailbox.rs:327–352`). It does not claim the token's receipt is the durable boundary. |
| App → Native body digest, then Native → local verify | Correct. Local custody job derives Context/body digest from the prepared header and invokes verify (`actor/app.rs:121–163`). It precedes header signing. |
| Subscribe or retained token wait → custody | Both can establish the required fence; only subscription returns a complete block. Custody is Completion<Error> (`marshal/types.rs:311–318`); wait returns Result<(), E> (`actors/util/completion.rs:25`). This motivates correction 1. |
| Check expected header/body and payload validity → true | Correct contract. Body codec/digest matching alone is not application validity; the App's actual transaction rules remain to implement. Local storage failure must not masquerade as true or payload invalidity. |
| Native self-arrow signs header | Correct necessary ordering. Producer state must become Custodied before pending_build_sign_request exposes that header (`machine/producer.rs:438–480`). Native signing reservations/journal/publication gates remain compressed in this body-focused figure. |
| Native → Relay(header digest, ()) → buffered complete block | Correct identity and ownership. Native Frame uses complete header digest for its relay key (`wire.rs:498–502`); Marshal Relay looks it up in its staged cache and calls broadcast_shared (`marshal/relay.rs:107–114`). This is an illustrated successful staged lookup, not proof that every call sends: a missing cache entry returns Ok without broadcast. |
| Buffered → peer header+body; Native → peer signed header | Correct distinction. TransactionBlock carries header plus body; native DataMessage::Block carries SignedTransactionBlock, a signed header. Native requests Relay before the corresponding publication attempt (`actor/publish.rs:121–136`), but separate channels can arrive in either order. Existing diagram note correctly rejects a receiver-arrival-order guarantee. |

The adjacent text correctly distinguishes staging from durability and body digest from Relay's header digest. A Relay request is local submission only, not remote receipt/custody. The figure need not enumerate cache-miss/retry/error branches if kept identified as the successful body-distribution path; the networking page already documents no-op Relay lookup.

## Diagram05: remote/repeated verification and custody

| Arrow/result | Source assessment |
|---|---|
| Native → verify(Context, body digest) | Correct: chain_plane dispatch derives both from the admitted header (`actors/voter/chain_plane.rs:522–553`). Native cryptographic/context eligibility precedes remote dispatch, but parent application verification can still be pending. |
| App derives header and BlockRef | Correct. Context::header builds exact contextual header; BlockRef contains chain, height and header digest (`types/block.rs:32–70`; `types/primitives.rs:229–277`). |
| subscribe_block waits for custody | Correct. Public subscribe takes a bounded caller slot, then router races buffered subscription against local/backfill Wait acquisition; found material is durably admitted before success (`marshal/mailbox.rs:419–449`; `service/router.rs:341–391`). |
| Optional fetch | Valid explicit App choice, not automatic behavior of subscribe. It can run while custody subscription remains pending. fetch/get can expose material before durability, motivating correction 2. DA hints can independently activate backfill but are not a guaranteed callback for every body. |
| Required block unavailable → pending | Correct ordinary live-request behavior. Peer absence/wrong responses and operational pressure are not proof of permanent expected-payload invalidity. Callback cancellation/service failure still follows lifecycle handling. |
| Expected invalid payload → false | Correct only for a permanent application-payload invalidity decision; not queue full, missing bytes, failed I/O, or an ordinary state-dependent transaction outcome. Adjacent text preserves this limit. |
| Valid+durable → retained facts → true | Correct App contract and no-execution wait. Retaining facts before answering prevents a lossy optional notification from being the only candidate record. It does not mean an unsigned local candidate is already report-eligible. |
| Optional live/authenticated/ancestry admission → scheduler | Correct separation. The scheduler runs inside App and requires exact execution-parent readiness. A true child verdict alone does not make its entire ancestor path usable. |

The adjacent text correctly covers local/recovery verify, repeated calls, Observer lacking live chain-plane callbacks, stale admission checks and applied-state races. Neither the diagram nor its text needs an additional BlockService or event trait.

## Diagram15: DA and native finality

| Arrow/result | Source assessment |
|---|---|
| Producer propose → local verify → sign → signed header | Correct minimal local sequence. Detailed Marshal staging/Relay work is intentionally supplied by the linked body diagram. |
| Validator native checks → remote verify → true | Correct. Remote authentication/eligibility differs from complete ancestor App readiness. True is payload validity plus durable custody, not completed execution. |
| Speculation branch | Correct when an eligible live candidate is retained in App. It need not block DA or view machinery. Optional candidate loss/retirement does not remove canonical handling. |
| Native DA gates → validator DA vote to producer | Correct. ready_votes consumes contiguous validated native offers under bounds (`machine/da.rs:646–704`; `machine/eligibility.rs:490–524`). Durable Publication::signed directs DA votes only to the associated producer (`machine/durability/effect.rs:470–482`). |
| Producer publishes DA certificate when threshold met | Correct successful native threshold path; one true verdict is insufficient. Certificate construction/publication is native work, not an App execution certificate. |
| Leader proposal / parent evidence | Correct native role and authenticated object. begin_regular_sign_pass selects native parent/history; propose_chain chooses anchors and bounded suffixes (`machine/view/proposal.rs:280–350`; `machine/vote_body.rs:119–159`). It does not wait for completion of this diagram's separate DA-certificate branch, motivating correction 3. |
| Validator broadcasts native votes | Correct: ordinary votes are broadcast, unlike DA votes (`machine/durability/effect.rs:470–491`; `wire.rs:518–522`). Drawing one recipient L is a representative peer edge; it must not suggest vote unicast only to the leader. |
| L computes native finality/extension and reports Activity | A valid representative local computation. Finality is not exclusive to the scheduled leader: every native view/finality owner processes its authenticated evidence. The App-facing diagram intentionally omits quorum algebra and additional native certificate/view-exit branches. |
| Marshal interprets history and ordered bodies | Correct mechanism, conditional on native proof input and available material. Activity is best-effort/event-specific and not itself an Update. Round9 documents coalesced L-QC intake versus optional direct-finality hints. |

A note should make clear that native roles can overlap on one node and that shown finality is local native processing, not a unique central finalizer. No new participant is needed. The adjacent text correctly keeps App ACK and speculative execution outside native vote/cut prerequisites and identifies full Baton's native policy extension as unimplemented.

## Diagram16: ownership graph

All current edges are appropriate at this abstraction level:

- Native network → ingress/verifier → voter groups hostile decode/identification/cryptographic admission, not an assertion that all verifier work precedes every voter observation.
- Voter ↔ native proof resolver, machine and safety journal denote existing capability/completion/storage relationships. Their bidirectionality is consistent with current actors.
- Voter → App propose/verify identifies callback ownership; the ownership graph does not enumerate oneshot completion return arrows.
- App → Marshal custody calls/ACK groups existing mailbox requests and Exact completion. It does not introduce another ACK service or imply transaction execution is native work.
- Voter → Marshal Activity/Relay requests, body channels ↔ Marshal and Marshal → App ordered Update identify the correct separate native/body/application boundaries.
- App dashed future Baton policy → machine explicitly marks the missing native policy integration. It does not claim a current public method or a second App orderer.

Adjacent source map/open-start notes are accurate: Engine::open can verify retained bodies before start/readiness; native AppExecutor dispatches callbacks rather than executing transactions. Detailed service supervision stays in reference/integration.md.

## Owned text adjustment and validation

Accepted the E2E owner's related glossary precision check: consensus/block-body.md now has separate header-digest and BlockRef table rows. Relay uses the former; exact Marshal block methods use the latter. No diagram16 edit, native change or runtime test was needed.

E2E applied all three corrections above, the ordinary-vote broadcast clarification and the adjacent note about already-running view work/each owner's finality. Re-read those final sources and verified all four current `.mmd` files exactly match their embedded Mermaid. Focused owned diff check passed. Root owns the changed diagrams' render/visual check; this report does not claim that render completed.
