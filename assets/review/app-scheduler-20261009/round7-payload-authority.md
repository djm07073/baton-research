# Round 7: payload identity, custody and canonical-first input

Inspected current native source `6233438985d8249d2b2bc1204191d5d405652288` and current reader pages, 2026-10-09. This is source evidence, not a new end-to-end protocol proof or runtime test.

## Identity construction and decode checks

| Value/path | Actual source contract | Limit |
|---|---|---|
| `Context::new` | Epoch, chain, positive producer height, parent header digest. `types/block.rs:32–70`. | Constructor rejects height zero; it does not independently establish committee membership, finality or an App execution-state parent. |
| `context.header(body_digest)` | Reconstructs exactly the producer header for that context and body commitment. | Callback payload is body digest; header digest is a separate derived identity. |
| Header digest | Hash of canonical header encoding, including context and body digest. `block.rs:175–188`; `types/primitives.rs:155–162`. | It commits to a body's supplied digest, not independently to VM semantics. |
| BlockRef | Chain, height and canonical header digest. `types/primitives.rs:229–277`. | Reference creation/decoding is not a signature or finality proof; epoch is committed through the header digest, not a separate BlockRef field. |
| `Body<H>` | Blanket implementation for `Codec + Digestible<Digest = H::Digest>`. `block.rs:264–267`. | No validator, signature checker, transaction pool policy or VM is supplied. Correct bounded decoding and a commitment covering the intended body semantics remain App implementation duties. |
| `TransactionBlock::from_context` | Creates header using the supplied body's `digest()`. `block.rs:284–293`. | This does not authenticate the producer or wait for durable storage. |
| `TransactionBlock::new` / `Read` | New compares `header.body_digest()` to `body.digest()`; Read decodes header and `B` with B::Cfg, then calls new. `block.rs:296–308,388–399`. | Generic code checks the body implementation's commitment. It does not enforce a particular hash preimage or redo application validity logic. |
| Complete block identity | `TransactionBlock::digest()` and `reference()` use header identity; Block::parent returns the producer parent. `block.rs:321–323,417–437`. | Same body bytes in distinct producer contexts yield distinct contextual block identities; execution reuse still needs its exact App parent/runtime/prefix. |
| Signed header | `SignedTransactionBlock` pairs header and attestation; decoding constructs the pair. `block.rs:461–530`. | Merely decoding or constructing this type does not verify the attestation; native scheme/ingress verification does. |

The example `application/block.rs:19–91` contains bounded opaque junk bytes. Its digest hashes its namespace plus raw bytes, not an automatically imposed generic encoding formula. Its App verdict only checks the requested header against the returned header (`application/actor.rs:108–122`). Replacing junk bytes with transactions therefore requires App checks; copying that small example verdict does not implement transaction validation.

## Marshal intake checks without a second App native verifier

1. **Buffered full-body ingress.** Buffered Engine uses a typed background receiver (`broadcast/src/buffered/engine.rs:177–185`); the receiver calls the configured type's `decode_cfg` and bounds concurrent jobs/mailbox use (`p2p/src/utils/codec.rs:238–293`). For TransactionBlock this runs the supplied body codec plus header/body commitment check. The buffer indexes decoded messages by their Digestible identity, which is the header digest. It does not run Automaton or a VM.
2. **Exact subscription.** Router subscribes by expected header digest, then explicitly compares `block.reference()` to the full requested BlockRef (`marshal/service/router.rs:336–374`). Found material is admitted durably through catalog before callers receive success (`:380–391`). No additional persistence operation is needed after successful subscription.
3. **Peer backfill.** Decode rejects oversized resolver values before parsing; ProducerBlock checks decoded full-block size, epoch, chain and digest. A segment additionally checks exact linked producer ancestry and bounded item count (`marshal/actors/backfill/validate.rs:58–166`). Waiter matching checks the complete requested reference (`backfill/waiter.rs:215–230`). Malformed/key-mismatched responses are Invalid; L-QCs take a separate cryptographic verifier path (`backfill/actor.rs:411–430,487–548`).
4. **Catalog admission.** Checks encoded block size, exact reference, configured chain range and epoch (`marshal/actors/catalog/validate.rs:21–56`). The already-constructed TransactionBlock carries the earlier body-commitment pairing. Catalog admission does not call application transaction validation.
5. **Canonical storage/delivery.** Commit checks dense exact output rows and producer frontier advancement (`catalog/validate.rs:219–280`); order reconstruction remains the synchronizer's responsibility. Delivery materializes exactly committed references and encoded lengths (`marshal/bodies.rs:160–185`; `storage/catalog/mod.rs:101–113`) and checks continuous indices/reference agreement (`delivery/actor.rs:288–301`). It supplies a complete block in native order, not a new app-specific validity verdict.

Get/fetch can expose buffered material before its durable admission; Round 3's custody distinction still applies. Codec/body bounds and correct digest implementation are part of the supplied App type/configuration. These source checks support trusting the local Marshal stream under its configured native contracts, not accepting a peer's arbitrary Update-shaped message.

## Native DA attests custody, not completed application execution

The native application contract explicitly makes `verify(true)` mean valid, locally available, crash-reconstructible payload and states that a validator DA-votes only after this fence (`consensus/src/multimmit/mod.rs:50–65`).

- Remote producer headers are authenticated by native scheme verification before reaching the chain plane (`scheme/bls12381_threshold/claims.rs:143–150`; `actors/verifier/verify.rs:40–145`; `machine/eligibility.rs:213–234`). A parent can still be Pending when another verify is dispatched, but the DA eligible run uses valid linked children (`eligibility.rs:491–523`).
- The local producer path performs its own pre-sign verify/custody check. Its later chain-plane observation is marked custodied from native producer state and does not require a redundant remote check (`machine/chain.rs:219–240`; `eligibility.rs:233–236`).
- DA choices consume contiguous validated eligible runs (`machine/da.rs:647–708`); signing/recording remains native authority. Inbound DA shares use structural precheck and are authenticated collectively during threshold recovery, rather than a separate pairing for every incoming share (`scheme/bls12381_threshold/claims.rs:157–167`; `actors/verifier/verify.rs:89–120`). This does not turn an individual unverified share into an execution certificate.

Neither a DA vote/certificate, producer signature, successful body decode nor custody completion proves transaction effects, state root or execution-result certification. App's static/context-independent payload rules belong in validity handling; outcomes depending on merged execution state belong to execution against the actual App parent. A transaction revert/conflict is not permission to reorder or remove the native canonical block.

## Canonical input without prior local verify

Marshal service takes the body type/codec, native verifier and Update reporter, not an Automaton. Its canonical delivery can obtain needed blocks through custody/backfill independently of the local chain-plane callback history. Observer role builds no live per-chain validation tasks (`actors/voter/actor/chains.rs:118–137`). A validator can also miss speculative admission, lose an optional activity hint, or receive a canonical body through recovery without the App retaining a usable speculative result.

Thus an Update can be the first App encounter with a block. Canonical handling receives a body already decoded through the configured contract and performs remaining application checks/interpretation or reuses exact previously validated work, then executes/repairs or imports applicable material and durably applies it. It must not require pool membership, a retained scheduler entry, a previous local true verdict, or a second native finality verifier.

If App detects an actual malformed/inconsistent canonical input, it cannot silently skip that index or fabricate an ACK. Source reconstruction and App validation failures remain failures to resolve. An ordinary state-dependent transaction outcome follows the App's deterministic execution rules and leaves native order unchanged. This review does not invent the VM's invalid-transaction policy or an additional validation API.

Counterexamples that the documented design now excludes:

- Treating any `B: Body<H>` as a transaction-validity proof because the marker exists.
- Using only body digest as a scheduler execution key across different producer contexts or execution parents.
- Treating a codec-valid buffered block as producer-authenticated early candidate before its appropriate native context/provenance is known.
- An Observer's first Update failing because no `verify` populated the speculative map.
- Accepting a peer block fetched under the wrong reference, or returning true from fetched bytes without durable custody.

## Relay cache scope and no-op result

Service::relay uses the existing `max_outbox_effects(participants)` bound, sized to native publication obligations (`marshal/service/mod.rs:194–209`; `config/profile.rs:97–105`). Staging inserts complete blocks by header digest; a successful subscription of this node's producer block also remembers it for recovery republishing. Repeated insertion updates its stored block without adding another order entry; beyond the configured count the oldest insertion is evicted (`marshal/relay.rs:21–70`). This is a bounded publication cache, separate from Marshal's durable body retention.

Relay::broadcast looks up the header digest. Missing/evicted identity returns Feedback::Ok and makes no buffered broadcast call (`relay.rs:107–112`). A found block is submitted to buffered broadcast; its local feedback still does not prove peer delivery, peer custody or native finality. Alignment's networking clarification is accurate. No App cache, retry layer or replacement Relay is required for the documented ordinary integration path.

## Documentation resolution

Root callback/E2E canonical pages already state that an Update can arrive without prior verify or speculative entry. The owned block-body page now explicitly says the Body marker/digest pairing supplies no transaction/VM validator. The owned ordered-input page mirrors the canonical-first condition and confirms no second native proof/order verifier is needed. Current Rust excerpts remain unchanged and accurate. Result proof/material policy, concrete VM and full native Baton policy remain open implementation work.
