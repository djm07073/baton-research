# Block construction and body exchange

**App builds and validates transaction bodies; existing Multimmit Marshal stores and exchanges complete blocks.** Put the TxPool inside App. Selected transactions feed `Automaton::propose`; `Automaton::verify` obtains durable custody and makes valid eligible blocks available to the App scheduler.

## Interface overview

| Value | Meaning |
|---|---|
| Body / body digest | Application transactions and the hash of their committed representation |
| `TransactionBlockHeader` | Epoch, producer chain, height, producer-header parent and body digest |
| Header digest | Hash of the complete contextual header; the existing Relay lookup key |
| `BlockRef` | Producer chain, height and header digest together; the exact reference used by Marshal block APIs |
| `TransactionBlock<H, B>` | Existing native header plus `Arc<B>` application body |
| `SignedTransactionBlock` | Signed header and attestation on native wire, without body bytes |

Implement the body's existing `Codec` and `Digestible` requirements. The `Body<H>` marker is blanket-implemented for matching types. `TransactionBlock::from_context` constructs the pair; `TransactionBlock::new` verifies a body commitment against an existing header. [Native block types](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/types/block.rs#L265).

Concretely, implement `Write`, `Read`, and `EncodeSize` (or `FixedSize`) for the body; these supply `Codec`. `Digestible` additionally requires `Clone + Send + Sync + 'static`. The body's `Read::Cfg` has those same bounds and supplies Marshal's `body_codec_config`; use it to bound untrusted body decoding. `TransactionBlock` already implements the shared consensus `Block` trait. [Codec requirements](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/codec/src/codec.rs#L197), [digest requirements](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/cryptography/src/lib.rs#L233), [Marshal configuration](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/config.rs#L339).

App supplies the bounded body codec and correct commitment implementation. The marker and header/body digest comparison do not implement transaction signatures, payload policy or VM semantics. Marshal checks native identity and custody; App's validity/execution code handles those application rules. No additional block-validation trait is required.

The producer-header parent differs from the execution-state parent. Scheduler/execution state records its own exact checkpoint, input sequence and runtime identity. Identical body bytes in different producer contexts do not give an interchangeable block/execution identity.

<a id="reuse-the-same-body-components-as-tempo"></a>

## Use Marshal's existing body APIs

The earlier Tempo/Alto investigation established the buffer/resolver/storage composition. Current native `log-multimmit` supplies directly compatible assembly: buffered full-block broadcast → `marshal::open` → resolver bridge → `Service::relay` → `Service::start`. Start from [that code](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/examples/log-multimmit/src/marshal.rs#L126). Other chain versions remain [historical references](../reference/integration.md#reference-versions-are-not-one-compatible-dependency-graph).

| App need | Existing call | Completion condition |
|---|---|---|
| Submit a built block | `marshal.stage_block(block)` | Accepted storage work; returned Custody token may still be pending |
| Wait for durable submission | `custody.wait()` or `marshal.put_block(block)` | Block durably recoverable |
| Wait for expected bytes | `marshal.subscribe_block(reference)` | Exact complete block under durable custody; starts no active peer fetch |
| Explicit peer fetch | `marshal.fetch_block(reference)` | Resolve requested complete block through existing backfill |
| Local lookup | `marshal.get_block(reference)` | Read local material without initiating peer fetch |
| Publication | Existing `marshal::Relay` | Request buffered broadcast of the staged complete block |

Accepted DA evidence may independently trigger backfill that fulfills a subscription. `get_block` can read buffered local material, and `fetch_block` can complete after buffered admission before its storage sync. Neither success alone establishes the verify custody fence. Use successful `subscribe_block`, `put_block`, or a staged Custody token's successful wait; a successful subscription needs no redundant second flush. [Mailbox contracts](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/mailbox.rs#L327).

If missing broadcast requires active retrieval, start `fetch_block(reference)` without waiting for the pending subscription to finish. When fetch supplies the exact valid block first, `put_block(block).await` can establish custody and the superseded subscription can be canceled. Do not assume a successful fetch wakes every earlier subscription: a subscription whose backfill wait failed may still be waiting only on buffered ingress. This uses the existing APIs; a subscription that already succeeded needs no extra put. [Subscription race](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/service/router.rs#L330).

## Select transactions and build a block

1. Engine issues `propose(context)`. App selects a bounded batch from its pool's selected candidates, preserving transactions until internal canonical cleanup permits retirement.
2. App builds `TransactionBlock::from_context(context, body)` and calls `stage_block`. Successful staging admits storage work; the proposal receiver may return the **body digest** before all storage I/O finishes.
3. Native constructs the same header and calls local `verify(context, body_digest)`. App waits on exact durable custody and validates the payload before resolving true. Native signs its header after this fence.
4. Native calls the supplied Relay with the **header digest** and publishes the signed header on its data plane. Relay broadcasts the full staged block on the body channel.

This is the example's [build/stage/answer](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/examples/log-multimmit/src/application/actor.rs#L309) and native [custody sequence](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/actors/voter/actor/app.rs#L121). Waiting for `put_block` before the proposal answer also satisfies the contract. Neither requires speculative execution completion.

The callback futures yield oneshot receivers. Keep temporary missing input pending; a definite proposal decline may close its receiver. Returning a digest commits App to verifying that contextual payload. An uncanceled local verification failure is a fatal Engine error (internally `Fatal::Automaton`); resource pressure cannot become payload invalidity. [Automaton contract](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/lib.rs#L134), [local failure](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/actors/voter/actor/live.rs#L578).

## Body dissemination, lookup, and custody

Headers and bodies have separate channels. A receiver may authenticate a header first and wait for its body, or buffer a body before native header admission. Sender-side Relay submission before native transmission does not guarantee receiver arrival order. [Native publication](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/actors/voter/actor/publish.rs#L124), [supplied Relay](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/relay.rs#L107).

For a remote lane, native authentication/ancestry eligibility precedes `verify`. A producer parent may still be pending application validation; dispatch does not prove all predecessor payloads are already valid/available for App scheduling. App reconstructs the expected header from context/body digest, subscribes by its exact BlockRef, checks application bytes, retains eligible scheduler candidate state and resolves true. Execution then runs asynchronously when its exact execution parent is ready. True does not wait for speculative execution, report collection or result certification. [Remote dispatch](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/actors/voter/chain_plane.rs#L522), [custody verification](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/examples/log-multimmit/src/application/actor.rs#L70).

`verify` also runs for this node's own block and during Engine recovery. Interpret another-lane availability only after successful verification, lane classification and lifecycle checks; callbacks are not one-to-one network receipt events. Local verification precedes signing. If candidate policy requires signed provenance, retain the prepared local candidate and admit it on the later `TransactionProposed` observation. That observation is best-effort; a missed observation can reduce speculation but cannot remove canonical Update handling.

For a producing validator, derive the local lane from the epoch's `Protocol::producer_chain(participant)` before comparing it with `context.chain()`: participant and chain indices need not match. A nonproducing validator has no local lane to exclude. [Producer assignment](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/config/protocol.rs#L197).

The shared Automaton contract describes requests as single-shot and reserves closure for terminal inability. Current Multimmit remote validation nevertheless maps a closed receiver to `Unavailable` and schedules that block again; local closure is fatal and recovery closure makes `Engine::open` fail. Keep temporary absence pending instead of using this remote behavior as a retry API, and tolerate repeated calls even without restart. [Remote rescheduling](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/machine/eligibility.rs#L326).

Deduplicate exact contextual block identities, skip already applied blocks for scheduling and fence stale/canceled work. Removing a speculative candidate does not invalidate its payload or cancel Engine's remaining custody requirements. Missing bytes/dependencies keep a live verdict pending; false means permanent invalidity. Storage failure cannot become true. Speculative queue pressure must not lose canonical input or make a valid block invalid. See [App handlers](../baton/interfaces.md).

`stage_block` can return `Busy` when router intake is full, and explicit `fetch_block` can return `Busy` at the pending-fetch bound. `subscribe_block` waits for a caller slot instead of rejecting that intake pressure; its acquisition and custody can still fail. Handle recoverable pressure within the live request's cancellation/lifecycle policy, without returning false or claiming custody. `Closed` signals a stopped service; a `Failed` result needs its underlying cause assessed. Failed mutable storage requires recovery of that instance. [Request/error paths](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/mailbox.rs#L313), [public errors](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/types.rs#L178).

Marshal already bounds native custody retention with `CertificateRecorded`, floors and the durable ACK cursor. During ordinary delivery, `prune` protects outputs beyond the current ACK cursor and blocks Engine may reverify. A coordinated floor installation replaces the delivery boundary; it does not install App state itself. App separately retains live execution/checkpoint/result material. [Retention API](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/mailbox.rs#L449).

`CertificateRecorded.released` is a per-producer custody bound that trails the certified height by the native pipeline depth; it is not the App's applied index. A previously dispatched verify can still reach App after release, but Engine ignores its settled verdict. Do not recreate speculative work for that stale request. Route native activities to Marshal so its existing retention can use the release; no release conservatively keeps bodies. App transaction/result/query retention has separate obligations. [Release contract](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/types/activity.rs#L104).
