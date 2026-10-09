# Connect the application to Multimmit

**Implement one application with a transaction pool, a Pre-cut or Baton scheduler, and transaction execution. Connect it through the existing `Automaton` and `Reporter` traits. Reuse Multimmit Marshal for block custody, body exchange and ordered delivery.**

The name `App` below means the application being designed. It is not a new Commonware trait. The native `AppExecutor` runs local `Automaton::propose/verify` jobs; it does not execute application transactions. Transaction execution runs in workers owned by App.

This design uses the current local Commonware checkout, [6233438](https://github.com/0xEyrie/monorepo/tree/6233438985d8249d2b2bc1204191d5d405652288). Earlier research against `534af0e` predates its Multimmit Marshal. Application scheduling, the transaction runtime and Baton policy integration described here remain to be implemented.

<a id="roles-and-responsibilities"></a>

## The smallest useful composition

| Component | Responsibility | Connection |
|---|---|---|
| Multimmit engine | Producer lanes, DA, leader proposals, votes and native finality | Calls App's `Automaton`; uses Marshal's relay and activity reporter |
| Multimmit Marshal | Full block custody, body broadcast/fetch, verified history, dense native order and delivery cursor | Its mailbox serves App; its delivery worker calls App's `Reporter<Update>` |
| [App transaction pool](../tx/interfaces.md) | Transaction admission, selected/unselected retention and bounded batch selection | `propose` selects from it; durable canonical outcomes update it internally |
| App scheduler | Eligible candidates, pending order, exact execution parents and worker dispatch | Pre-cut or Baton implementation selected at startup |
| App execution and state | Transaction effects, checkpoints, selected roots, result certification, state sync and durable application | Existing runtime, crypto, P2P and QMDB handles |

Pool, scheduler, execution and storage code can be separate files inside App. These responsibilities do not require separate public `TxPool`, `Baton`, `Executor`, `Storage`, `BlockService` or `Orderer` traits. Keep the existing Commonware interfaces at the actual engine boundary. [Architecture](../overview/architecture.md) shows this composition.

Pre-cut and Baton share application execution and storage. **Pre-cut has no Baton instance, reports, directions or native policy change.** Baton adds authenticated intended-order reports and direction selection to local speculative scheduling. Use two concrete scheduler implementations or a local mode enum; no generic scheduling framework is required.

<a id="report-connection"></a>

## What App implements

Follow the [assembly and callback handlers](interfaces.md#assemble-before-opening-the-engine) for the connection sequence.

| Existing entry point | App action | Completion means |
|---|---|---|
| `Automaton::propose(context)` | Select transactions; construct `TransactionBlock` for the producer context; stage it through Marshal | Resolve the returned receiver with the **body digest** after accepted staging; the subsequent local custody verification must still succeed |
| `Automaton::verify(context, body_digest)` | Obtain the exact full block; validate payload/context and durable custody; register usable local candidate metadata with the selected scheduler | Resolve the returned receiver with `true` for a valid, durably held/reconstructible payload; speculative execution is independent |
| Marshal `Reporter<Activity = Update<Block>>::report(update)` | Transfer the indexed full block and ACK token into App's retained delivery inbox | Synchronous local handoff only; a worker applies the exact canonical input and ACKs after durable completion |
| Optional native `Reporter<Activity = Activity<V,D>>::report(activity)` | Observe native admission, local proposal or finality hints used by optional scheduling | Best-effort observation; it does not replace Marshal's ordered `Update` stream |

Use Marshal's existing `Relay` implementation. Its broadcast key is the **full header/block digest**, which locates the staged full block; this differs from the body digest returned by `propose` and passed to `verify`. The native wire carries signed headers separately from the Marshal body broadcast. A receiver may therefore have the header before the body. [Body flow](../consensus/block-body.md) explains these identities and custody stages.

`Reporter` has an associated `Activity` type. One concrete Rust type cannot implement it twice with two different associated types. Give the same App owner two small typed handles if it needs both native observations and Marshal deliveries. This is ordinary mailbox wiring, not another service layer.

## When speculative execution begins

The useful trigger is **a valid, usable block becoming known to App**, often during successful `verify`. App records that candidate, and the scheduler runs it when the required execution parent and resources are ready. The callback does not wait for the run.

`verify` is not a network-receive notification. Current Multimmit invokes it in three places:

- **Remote producer path:** native authentication/eligibility admits a header before the voter asks App to verify its payload. Duplicates, malformed packets and not-yet-eligible headers do not map one-to-one to calls.
- **Local producer path:** after `propose`, native code calls `verify` as a custody check **before signing the local header**.
- **Recovery:** `Engine::open` rechecks retained payload obligations before actors start.

Interpret successful **live** verification according to the node's role:

| Role | Candidate interpretation |
|---|---|
| Validator with a local producer lane | `context.chain() != local producer chain` can identify other-lane work |
| Nonproducing validator | Live validation still exists; there is no local lane to exclude |
| `Role::Observer` | No live per-chain validation; normally enter through Marshal Update unless an explicit authenticated early-candidate intake is added |

`verify` still does not mean a new network receipt. Before speculative admission, check App's current lifecycle and deduplicate exact block identity, excluding already-applied work. Track startup explicitly: the callback has no origin or recovery flag. These checks filter speculation, not the native custody verdict.

A local pre-sign body can be prepared locally. If report eligibility requires an authenticated native header, promote it only when that evidence is available. `TransactionProposed` and `ProtocolAccepted` are useful best-effort observations; missed hints may reduce speculation but cannot block canonical processing.

The scheduler separates **candidate admission** from **dispatch**. A body can be valid while its execution predecessor is unfinished. Admission updates pending work; dispatch later checks the exact parent checkpoint. Producer-header ancestry is lane ancestry, not the merged application's execution-state parent. [Callback behavior](interfaces.md#automatonverify-validity-custody-and-scheduling) makes this sequence explicit.

<a id="confirmed-order-delivery"></a>

## When canonical application begins

Marshal reports continuous indexed blocks in its existing native order. App treats each `Update` as authoritative ordered input, reconciles the speculative path, and uses an exact matching completed result when available. Otherwise it finishes or repairs the required work. It then prepares/applies the selected state through the application's canonical writer.

The ACK token is completed **after durable application**, including enough applied-position/identity metadata to recover idempotently. If speculation already finished on the correct parent, this path may mainly select the result and perform storage I/O. ACK does not mandate rerunning transactions. It also cannot turn unfinished execution into durable state merely because the block entered a queue.

Marshal can deliver several blocks before earlier ACKs arrive, up to `max_pending_acks`. A full window holds further application delivery; the native consensus engine does not wait for these ACKs to vote or finalize. Marshal persists its own delivery cursor separately after acknowledged progress. App must handle redelivery after a crash between application durability and Marshal cursor durability. See [the complete Update/ACK flow](interfaces.md#marshal-reportupdate-canonical-input-and-ack).

<a id="commonware-primitives-in-the-baton-layer"></a>

## Baton-specific work stays inside the application

Baton scheduling owns the report window, intended-order snapshot, bounded candidate evaluation and advisory direction. Reports bind epoch, view, history, canonical parent, rule, window and frontier. They express intention, not execution completion. Reuse the existing Clock, runtime tasks, crypto, codec and authenticated P2P for this work. Bound both retained messages and submitted CPU work; an unordered future pool alone is not a capacity limit.

The ordinary local rule is `F ++ sort_G(S_pending)`: preserve completed/current execution order and sort only eligible work not yet started. Cut readiness never waits for reports, a timer, planning, speculative execution or a direction reply. Details and the remaining protected-prefix integration obligation are in [Scheduler behavior and direction](direction.md).

**An app-only Baton scheduler can guide speculation today; it cannot make its preferred order canonical by rearranging Marshal Updates.** The full research objective still needs an authenticated native policy/adoption mechanism and consistent history interpretation. Keep this explicit rather than adding a facade that makes the missing protocol work appear implemented.
