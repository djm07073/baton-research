# Round 16: exact body retrieval and custody progress

Audited source `6233438985d8249d2b2bc1204191d5d405652288`, 2026-10-09. This is source-path reasoning, not a runtime reproduction or a claim of a demonstrated native bug. No native edits or tests.

## Finding and reader correction

The existing APIs cover missing body broadcast: active fetch obtains the exact complete block, and successful subscribe or put/stage completion establishes durable custody. No new BlockService or background resolver is needed. The current example only uses subscription for verification; a robust App must also choose active retrieval when it is required for progress.

One clarification was warranted: do not assume concurrent fetch necessarily wakes every earlier subscription. A subscription whose internal backfill wait failed can still wait on buffered broadcast after a later fetch succeeds. The owned consensus/block-body page now states the existing-API fallback: when fetch returns the exact valid block first, use put_block(block).await (or stage plus the returned custody completion), then retire the superseded wait. A successful subscription already supplies custody and needs no second flush. Root received the same minimal core clarification.

## Exact identity from callback to peer response

1. Native verify provides producer Context and body digest. Context.header(body_digest) reconstructs epoch, chain, height, producer-header parent and payload commitment. Header.block_ref hashes that full header and includes chain/height; the body digest alone is not the retrieval key (`types/block.rs:32–70,156–191`).
2. Public get/fetch/subscribe take that exact BlockRef. Relay instead takes its header digest and looks up the complete staged block (`marshal/mailbox.rs:396–445`; `relay.rs:51–68,107–113`).
3. Backfill's peer key is ProducerBlock(chain, header_digest), while the retained Target keeps the full expected BlockRef (`actors/backfill/waiter.rs:165–173`). Decoding checks epoch, chain, digest and size; TransactionBlock decoding checks header/body commitment; the waiter then checks complete BlockRef equality, including height (`validate.rs:148–158`; `types/block.rs:296–307,389–402`; `waiter.rs:211–226`).
4. Buffered subscription uses the header digest and filters the received complete block by exact reference (`service/router.rs:343–351`). Native producer-header authentication already happened before an eligible remote verify. App still checks its own payload rules before true; a wrong peer response is not proof the expected committed payload is permanently invalid.

## Why broadcast and passive subscription are insufficient alone

Relay retains a bounded cache of recently staged bodies; successful own-chain subscription also remembers a body for resumed local publication. A cache miss returns Feedback::Ok without calling buffered broadcast (`relay.rs:41–67,75–78,107–113`). Native publication treats Closed specially but does not turn Ok into peer receipt/custody evidence (`actors/voter/actor/publish.rs:114–145`). Header and body channels therefore have no guaranteed receive ordering, and a signed header may be usable before body arrival.

Public subscribe does not request a peer fetch itself. Its backfill target is Wait; local admission can complete it, and accepted DA evidence may promote it to fetching. Explicit fetch uses Fetch mode and initiates resolver work after a local miss (`marshal/mailbox.rs:402–426`; `actors/backfill/mailbox.rs:215–224,328–345,379–403`; `actor.rs:582–598,825–855`). A missing or dropped optional DA hint is not an active-fetch guarantee. Waiting for a DA certificate is also not a substitute for acquiring a body needed by this node's own DA vote.

The example verify_stored runs only `subscribe_block` under response.closed() cancellation, checks the returned header and replies true. It does not call fetch_block (`examples/log-multimmit/src/application/actor.rs:60–119`). The example assembly already supplies the buffered broadcast engine, generic resolver using BackfillBridge, native Marshal and SchemeVerifier (`examples/log-multimmit/src/marshal.rs:126–212`). Stronger App retrieval policy uses those handles rather than another service.

## Pressure branch that motivated the clarification

The following is a concrete possible source path, not a tested schedule:

1. subscribe_block acquires its caller slot and router starts buffered-versus-backfill acquisition.
2. Backfill registration can fail or evict the Wait with PendingFull before doing the local recheck (`actors/backfill/actor.rs:644–660`).
3. Router observes Err from that branch and then awaits buffered ingress; it does not re-register a backfill wait in that branch (`service/router.rs:354–373`).
4. A later explicit fetch can obtain and stage the exact block through backfill. The old failed Wait is no longer registered, so completing current backfill waiters does not revive it (`actor.rs:758–798`). Without another buffered arrival, it is unsafe for App to assume that old subscription must now finish.
5. App already has the exact fetched block. `put_block(block)` routes it through existing stage_block and waits for the Custody token (`marshal/mailbox.rs:354–358`). This supplies the missing durable boundary independently of the old subscription's acquisition branch.

This does not require canceling an otherwise useful subscription early. A successful subscription can win and avoid the put. If fetch supplies usable bytes first while that subscription remains pending, App can take the put/stage-completion path and retire the superseded caller. Duplicate acquisition is not another canonical writer and does not change the block identity.

## Minimal App progress choices

| Situation | Existing API path | Completion required before true |
|---|---|---|
| Local proposal has retained Custody token | Await the accepted stage token, checking exact contextual payload validity | Successful token completion |
| Local or buffered exact body becomes available | subscribe_block(reference) | Successful durable complete-block result plus App validity |
| Broadcast absent and active retrieval required | Start fetch_block(reference) without waiting for a passive subscription to finish | Durable subscription success, or put_block(fetched_block) / stage-plus-token success |
| Only get_block/fetch_block succeeded | Treat returned body as available but not yet proven durable | One of the preceding custody completions |
| Body still unavailable | Keep the live verdict pending and service retrieval/cancellation | Do not invent empty input, false, true or automatic native retry |

These paths can run as the existing bounded App callback jobs. They should not monopolize the App owner while waiting and do not wait for speculative execution, report collection or result certificates. Progress remains conditional on an available exact source, healthy storage/transport and the chosen capacity policy allowing required work to run; the API does not guarantee missing bytes eventually exist.

## Errors, cancellation and accepted work

- Wrong/oversized/malformed peer responses are rejected by backfill validation and reported Invalid to the existing resolver, without establishing permanent invalidity of the requested payload (`backfill/actor.rs:406–425`).
- PendingFull maps to public Busy; stopped backfill maps to Closed; other causes remain Failed (`marshal/types.rs:222–231`). Retry recoverable pressure within the live request's bounded/cancellation policy. A fatal mutable-storage failure is a lifecycle/recovery issue, not a bool verdict.
- Fetch can return from a buffered local recheck or buffered admission before durable sync; its source success alone is insufficient. Successful public subscription settles via catalog.admit_block before answering (`service/router.rs:380–391`).
- Canceling the superseded subscription releases its caller when observed and aborts unresolved acquisition only when every caller leaves. Already begun durable settlement continues (`service/subscriptions.rs:132–217`). Canceling a fetch removes its still-registered demand; it does not undo accepted staging (`backfill/waiter.rs:258–284`; `actor.rs:600–608`).
- Successful put waits for storage custody. Router completes that custody token before downstream admitted-block bookkeeping (`service/router.rs:301–327`), so no new peer acknowledgment or resolver notification becomes part of true's durability fence.

The existing canonical Marshal path independently retrieves bodies for ordered delivery. App's explicit verify acquisition is not a new finality/order interpreter. No extra trait, global resolver loop, callback origin field or body service was introduced. Focused reader/report diff checks passed.
