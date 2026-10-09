# Round 3: API and source binding

Source inspected: parent checkout `6233438985d8249d2b2bc1204191d5d405652288`, 2026-10-09. This is a source and documentation audit, not a compiled application integration or protocol test. Paths refer to the parent checkout unless prefixed with `docs/`.

## API excerpt check

All five `rust,ignore` blocks in `docs/overview/rust-interfaces.md` match the current declarations after whitespace normalization. The seven checked declarations are Automaton `propose`/`verify` (`consensus/src/lib.rs:155,179`), Reporter `report` (`:267`), Mailbox `stage_block`/`put_block` (`consensus/src/multimmit/marshal/mailbox.rs:337,354`), `Update` and its three public fields (`marshal/types.rs:130`), and Relay `broadcast` (`consensus/src/lib.rs:253`). Omitted enclosing trait/impl bounds, imports and derives are labeled. These excerpts and the generated reference are not standalone compilation targets.

The public open path is `multimmit::marshal::open`. `marshal/mod.rs` reexports `open`, `Service` and `ServiceHandle` from its private `service` module. The initial audit's private-path shorthand has been corrected. `Body<H>` is a blanket marker over the existing codec and digest traits; no additional application block trait is needed.

## Marshal operations and failure boundaries

This includes every Marshal method named by the main overview/Baton pages and the retention methods used by their linked integration/recovery pages.

| Operation | Actual behavior and boundary | Source |
|---|---|---|
| `marshal::open` | Validates actor bounds, opens storage/scratch and prepares actors; returns Service and BackfillBridge or OpenError. It is not the service-start step. | `marshal/service/mod.rs:93–191` |
| `Service::relay` | Obtain before start. Later calls share the first call's staged-cache settings. Retains recently staged blocks and subscribed own-producer blocks for native publication/recovery. | `service/mod.rs:194–210`; `marshal/relay.rs:21–64` |
| `Service::start` | Consumes Service after resolver transport attachment; starts actors and returns Mailbox plus ServiceHandle. Requires an LqcVerifier and `Reporter<Update<TransactionBlock>>`. Delivery can start before the App actor is running, so already-created App handles must retain early replay. | `service/mod.rs:213–248`; `examples/log-multimmit/src/node.rs:260–335` |
| `stage_block` | Accepted complete-block storage work, then a Custody token; acceptance also makes the block available to the relay cache. No broadcast and no durable-completion guarantee from acceptance alone. Accepted work survives token drop. Router saturation can return Busy; stopped endpoints return Closed; storage errors map to Failed. | `marshal/mailbox.rs:314–351`; `marshal/service/router.rs:302–325` |
| `Custody::wait` / `put_block` | Successful wait means the block is durably recoverable; `put_block` combines stage plus wait. The token can report failure or Closed. Neither operation executes application transactions. | `marshal/mailbox.rs:354–358`; `marshal/types.rs:308–318`; `actors/util/completion.rs` |
| `get_block` | Local admitted-body lookup, possibly None, without peer fetch. Buffered catalog material can be visible before sync. Catalog/promoter shutdown or failures propagate. | `marshal/mailbox.rs:396–401`; `marshal/bodies.rs:82–94` |
| `fetch_block` | Explicit local-or-peer retrieval. Dropping its future cancels that request. Backfill pending saturation maps to Busy, stopped backfill to Closed, other errors to Failed. A completed fetch is not necessarily a durable custody fence. | `marshal/mailbox.rs:409–417,223–230`; `marshal/actors/backfill/mailbox.rs:338–347` |
| `subscribe_block` | Waits for bounded subscription capacity, then races buffered ingress against local/backfill custody. Does not itself initiate peer fetch; accepted DA evidence can independently do so. Successful response follows durable catalog admission. No extra flush is needed to establish custody. | `marshal/mailbox.rs:420–446`; `marshal/service/router.rs:330–391` |
| `get_certificate` / `fetch_certificate` | Local admitted L-QC lookup versus explicit retrieval. Fetch cancellation and backfill error mapping apply. These do not substitute for block-body custody. | `marshal/mailbox.rs:361–388`; `marshal/actors/backfill/actor.rs:487–518` |
| `max_pending_acks` | Returns the configured ordinary active-generation delivery window. A reset can create new deliveries while old Updates remain in App; it is not an App-wide lifetime retention bound. | `marshal/mailbox.rs:308–311`; `marshal/actors/delivery/actor.rs:423–455` |
| `floor_at` | Highest retained durably committed floor at or below the requested index, or None. Does not import application state. | `marshal/mailbox.rs:449–457` |
| `install_floor` | Verifies/installs a native floor and resets native delivery generation/window, then retires covered certified backfill. Router can return Busy/Closed; validation/storage failures propagate. It neither imports App state nor reconciles old App-retained Updates. Accepted mutation is not canceled merely by dropping its reply. | `marshal/mailbox.rs:460–468`; `marshal/service/router.rs:410–424`; `marshal/actors/synchronizer/floor.rs` |
| `prune` | Uses a retained floor, clamps to acknowledged delivery progress, preserves that floor and later outputs, and observes producer custody-release bounds. This is Marshal retention, not permission to remove App state/results indiscriminately. | `marshal/mailbox.rs:471–483` |
| `progress` | Returns Marshal's durable floor generation/floor/committed/acknowledged progress; it is not App state or App execution progress. Catalog errors propagate. | `marshal/mailbox.rs:486–489`; `marshal/types.rs` |
| Mailbox `Reporter<Activity>` | CertificateRecorded uses the catalog's coalescing release lane. Other native activities enter asynchronous hint handling; application code cannot use reporter return as custody, canonical-apply or transaction-completion acknowledgement. | `marshal/mailbox.rs:492–522` |
| Existing Relay `broadcast` | Uses full header/block digest to find staged complete material, then requests buffered broadcast. Missing/evicted staged identity currently returns local Feedback::Ok without broadcasting; a successful local return never establishes remote receipt. | `marshal/relay.rs:73–112` |

The newly corrected get/fetch boundary is implementation-proven: backfill stages through `catalog.stage_blocks`; that route uses `AdmissionReply::Buffered` (`catalog/mailbox.rs:861–885`), and `backfill/actor.rs:551–570` completes fetched callers after the staged admission. In contrast, subscription `router::on_found` awaits durable `catalog.admit_block` before replying (`router.rs:380–391`). The callback/body/integration pages now say that fetched bytes alone cannot justify `verify(true)`.

## Header, body, and engine terminology

- `SignedTransactionBlock` contains signed header plus attestation, not the complete body (`types/block.rs:461`; `wire.rs:170–172,250`). The native Data Block message can therefore arrive before the full body.
- `TransactionBlock` stores header plus Arc body; construction checks header body commitment against `body.digest()`, while `reference()` computes full header identity (`types/block.rs:274–322`). Its codec writes both header and body (`:372–398`). Body digest passed to Automaton differs from full header digest used by Relay and BlockRef. Different producer contexts can bind the same body digest to different block identities.
- Local Relay submission before header transmission does not imply peer arrival order. Native header channels and Marshal complete-body channels are independent. No duplicate App body service is justified by header-first arrival.
- `Engine::open` validates config, recovers native storage and can call App verify before ingress/voter actors run (`engine/mod.rs:437–496`; `storage/recovery.rs:466–496`). Body/App services must already answer those requests.
- `Engine::start` attaches the four planes and starts ingress/resolver/voter, returning Running (`engine/mod.rs:517–561`). `Running::ready` covers startup durable work and initial producer wake submission; it is not App transaction completion or an application ACK barrier (`engine/mod.rs:193,515`; `actors/voter/actor/startup.rs:188–227`).

## Diagram and correction status

Viewed the actual rendered `docs/assets/diagrams/diagram-16.png` after the root's target render. The previous long dashed-policy label crowded the custody edge. Source plus embedded Mermaid now combine the App-to-Marshal label as `custody calls / ACK` and shorten the dashed future-policy label. The refreshed PNG has readable separate labels and no visible overlap. Edge meanings match source: native runtime calls Automaton, native activity/Relay requests reach Marshal, Marshal delivers ordered Updates to App, App uses custody and ACK, and the dashed Baton-policy edge is explicitly future protocol work. Marshal body exchange and native proof resolution remain separate.

`native-audit.md` now explicitly corrects the private service path, remote callback retry shorthand, active-generation window bound, and buffered fetch distinction. Round 2 retains source evidence for remote Unavailable rescheduling, parent-Pending eligibility and floor overlap. No native changes, protocol tests or new integration guarantees were introduced by these checks.
