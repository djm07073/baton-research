# Commonware integration and development order

**Start with current `log-multimmit` and replace its synthetic App behavior with transaction handling and scheduling.** The existing Engine/Marshal graph already provides producer consensus, body custody, backfill and canonical delivery. Keep one App containing its pool, selected scheduler, execution workers and state backend.

## Commonware integration anchors

Current native source is [6233438985d8249d2b2bc1204191d5d405652288](https://github.com/0xEyrie/monorepo/tree/6233438985d8249d2b2bc1204191d5d405652288). These anchors describe that checkout, not the older research baseline.

| Read in this order | Existing code | App connection |
|---|---|---|
| 1. Node assembly | [node.rs](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/examples/log-multimmit/src/node.rs#L242) | Register four Engine planes, Marshal resolver and body-broadcast channels; construct typed App handles |
| 2. Marshal assembly | [marshal.rs](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/examples/log-multimmit/src/marshal.rs#L126) | Reuse buffered Engine, `marshal::open`, resolver bridge, supplied Relay and SchemeVerifier |
| 3. Application callbacks | [application/actor.rs](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/examples/log-multimmit/src/application/actor.rs#L70) | Replace synthetic body construction/checks with App pool and validity; register scheduling independently of execution completion |
| 4. Engine startup | [engine/mod.rs](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/engine/mod.rs#L446) | Service recovery `verify` callbacks during open; then start planes and await readiness |
| 5. Ordered input | [Update](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/types.rs#L128) | Retain canonical input and ACK, select/reuse/repair execution, durably apply, acknowledge |
| 6. Native policy boundary | [LeaderBlock](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/types/block.rs#L802), [Marshal order](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/protocol/order.rs) | Full Baton needs authenticated policy construction/validation/continuation/recovery; callbacks alone do not provide it |

### Body assembly to implement

Body lookup/fetch and custody completion are separate: `get_block` and `fetch_block` may expose buffered material before durability. For a true verification verdict use Marshal's successful `subscribe_block` or stage/put durability completion.

Use this connection sequence; names below are explanatory pseudocode around existing APIs, not a compiled constructor recipe:

```text
register native data, consensus, certificate, resolver channels
register Marshal body-broadcast and backfill channels
create App ingress handles; reopen App durable state
start network and buffered full-block broadcast
(service, bridge) = await marshal::open(runtime, config, buffer)
start existing resolver with bridge as Producer and Consumer
relay = service.relay(local_producer_chain)
(marshal, service_handle) = service.start(resolver, SchemeVerifier, app_output)
start App custody/output processing with marshal.clone()
engine = await Engine::open(config {
    automaton: app_automaton,
    relay,
    reporter: marshal,
    ...
})
running = engine.start(native_planes)
await running.ready()
```

`Engine::open` spawns no native actors. `marshal::open` already starts its catalog and optional promoter; `Service::start` starts the remaining Marshal actors. Own that entire startup attempt through the existing node/runtime lifetime so a later open failure does not leave earlier services unmanaged. [Marshal lifecycle](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/service/mod.rs#L1).

App processing must answer recovered-body requests while `Engine::open` is pending. Marshal can also begin redelivering old Updates when its service starts, so output ingress must retain them until App recovery is ready. Start in an explicit recovery lifecycle, deduplicate replay and enable fresh speculative admission after the relevant App/native startup fences. A new public callback is unnecessary for this local lifecycle state.

If App also consumes native Activity, use a separate typed handle from its `Reporter<Update<Block>>` and compose `Reporters::from((marshal, app_activity))`. Both App handles may reach the same owner, but Rust's associated Activity type prevents implementing both specializations on the same concrete type. The required output ingress retains Updates without dropping their ACKs. Its ordinary queue bound follows the active delivery window. Floor/import handoff must separately fence and reconcile old App-held Updates before allowing unaccounted overlap with a new window; Update carries no generation field and Marshal reset does not clear App queues. `Feedback::Backoff` does not make Marshal retry a rejected Update. See [delivery semantics](../consensus/ordered-input.md#delivery-backpressure-and-recovery).

Pass native Activity directly to the supplied Marshal mailbox; an optional App observer is a sibling, not a forwarding dependency. Use its existing [pressure policy](../consensus/README.md#native-activities). Configure `catalog_mailbox_size`, `resolver_mailbox_size` and `backfill_concurrency` through Marshal's existing capacities; these derive router jobs/subscription slots and backfill bounds. They do not make every hint reliable or convert service errors into invalid-payload verdicts. [Derived actor bounds](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/config.rs#L550).

<a id="service-lifetimes"></a>

Own service handles through existing runtime supervision. Engine and Marshal each supervise their own actors; the node owner coordinates failures and shutdown across Engine, App and transport lifetimes. Unexpected handle completion is a stop signal even when its result is Ok. Stop native callback producers and fence App work before tearing down body/state services. Abort/join is task termination, not an App flush barrier. Reopen matching native custody and application state on restart; native readiness is not durable application readiness. [Startup/recovery](../e2e/recovery.md), [Marshal supervisor](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/service/supervisor.rs#L64).

Use the callback response's existing cancellation signal to stop obsolete App waits, as the example does. Canceling a request does not undo accepted staging or a subscription's begun durable settlement. Stopping the service also does not guarantee those writes completed: only the successful custody/durable-apply boundary supports the corresponding promise. [Callback cancellation](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/examples/log-multimmit/src/application/actor.rs#L60), [subscription lifecycle](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/service/subscriptions.rs#L1).

For checkpoint bootstrap, `Start::Floor` only seeds a fresh namespace and requires caller authentication of its anchor and snapshot binding; recovered storage wins over Start. Open/config validation does not verify that anchor signature, and the later `Service::start` verifier does not retroactively authenticate it. Prefer the documented `Start::Genesis` plus `install_floor` path for peer-served floors, coordinated with App state import. [Existing startup contract](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/config.rs#L164), [floor and App authority](../consensus/ordered-input.md#reuse-proof-verification-and-storage).

<a id="orderer-assembly"></a>

### Baton confirmed-order assembly

Use Marshal's existing canonical `Update` stream for both PreCut and Baton. Marshal already implements the body/proof backfill, native order reconstruction, catalog and ACK cursor previously assigned to a proposed Baton Orderer. App's confirmed handler reconciles the scheduler and owns application-state apply. [Ordered input](../consensus/ordered-input.md).

The native extension for full Baton is narrower and still unresolved: prepared policy must be bound to the actual leader proposal and interpreted identically by native validation/recovery and Marshal. Sorting output Updates locally is invalid. [Policy TODO](../consensus/decisions.md#todo-bind-baton-prefix-and-policy-to-cut-proposals).

### Pool and storage assembly to evaluate

Keep admission/selection and cleanup inside App's chosen pool implementation. Reuse a compatible whole pool where appropriate; a queue or peer provider alone is not a complete transaction pool. Selection and proposal do not establish canonical retirement. [Pool choices](../tx/README.md).

Use QMDB primitives beneath App's state backend. Transaction execution produces changes; selected root preparation and canonical apply/durability remain separate work. Existing sealed-parent forks do not automatically provide root-deferred execution branching. Full `glue::stateful::Application` is optional and must not force hashing on every speculative attempt. [Storage details](../execution/qmdb.md).

## Development stages and validation flows

| Stage | Concrete work | Evidence required |
|---|---|---|
| 1 | Assemble existing Multimmit/Marshal with the App's body type and callback handles | Actual body custody, relay, native startup/recovery and ordered delivery |
| 2 | Add App-owned pool and deterministic transaction execution/backend | Bounded admission/selection, state effects and linked durable applied identity |
| 3 | Add App `Reporter<Update>` handling | Exact order, replay idempotence, ACK only after durable apply, lossless delivery window |
| 4 | Implement independent PreCut scheduler inside App | Pending-only sorting, exact-parent speculative reuse/repair, no Baton instance or traffic |
| 5 | Implement Baton scheduler report/direction work inside App | Authenticated report contexts, snapshot closure and completed bounded selection without blocking cut or confirmed processing |
| 6 | Implement native authenticated Baton policy extension | Proposal binding, pre-vote validation, inclusion/leading-order preservation, continuation and Marshal recovery |
| 7 | Compare Original / PreCut / Baton | Same pool/body/backend/resources/certification endpoint; actual E2E and performance evidence |

App execution certification and direct peer state sync belong with the shared execution/backend path, independent of report collection or direction selection. Retain `f+1` distinct valid signatures over the same irrevocable input, base state, runtime and result; imported state cannot be signed as locally executed. The native consensus quorum is not that execution certificate threshold. These contracts need implementation and tests; this documentation rewrite claims none.

## Primitive reuse catalog

| Responsibility | Existing building blocks | Application-specific work |
|---|---|---|
| Producer callbacks | `Automaton` | Pool selection, body validity and scheduler admission |
| Complete body custody/exchange | Multimmit Marshal, supplied Relay, buffered broadcast and resolver bridge | Body codec/digest, config and limits |
| Canonical input/replay | Marshal synchronizer/catalog/delivery, Update/Exact | Exact application-state apply and idempotent acknowledgement |
| Scheduling | Runtime clocks/tasks, actor mailboxes and future pools | Explicit work budgets, PreCut queue and Baton report/direction rules |
| Transaction state | QMDB batches/database and recovery primitives | Execution semantics, branch identity, selected root preparation and canonical writer |
| Result exchange | Commonware P2P, codecs and cryptography | Exact statements, provenance, distinct signer validation and result/state-sync coordination |

## Copy the assembly from real chains

The current native example is the primary connection reference. Earlier source-pinned ecosystem research remains useful for particular App internals, without importing a second consensus/body layer:

| Historical source | Useful comparison | Limitation |
|---|---|---|
| [Tempo engine](https://github.com/tempoxyz/tempo/blob/61c979a524f9af5de9c540a0088c429a44741e4c/crates/consensus/src/consensus/engine.rs) | Buffer/Marshal/execution handle composition | Simplex and Ethereum execution choices |
| [Alto engine](https://github.com/commonwarexyz/alto/blob/1d87569348b5560699465a72d691d90f18affb9c/chain/src/engine.rs) | Archive and actor ownership/startup | Simplex adapter and older dependency graph |
| [Constantinople pool](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/webserver/actor.rs) | Whole-pool admission/packing/tracking | Fixed transaction types and destructive-selection lifecycle |
| [Nunchi pool](https://github.com/nunchi-labs/sdk/blob/eea35ced709f68c15d6fbc8bcc754696a7e44374/mempool/src/actor.rs) | Generic nonce-lane actor and P2P | Payload/byte bounds, canonical cleanup and restart must fit App |
| [Constantinople execution](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/application/src/consensus/execution.rs) | Computation followed by selected root work | Historical source pattern, not an adopted runtime |

### Reference versions are not one compatible dependency graph

The earlier research inspected native `534af0...`, Commonware MCP `v2026.9.0`, and several ecosystem pins above. Current native integration follows `6233438...`. Those are different source/package graphs; matching Rust type names do not establish interoperability. Check concrete imports, codecs, runtime bounds and storage formats against the chosen current checkout before adapting an ecosystem component. No package upgrade or compiled actor port is made by this rewrite.

### Check native constructor inputs

Copy the current [Marshal constructor](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/examples/log-multimmit/src/marshal.rs#L126) and [node constructor](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/examples/log-multimmit/src/node.rs#L242). Their configs include body decode limits, peer provider/blocker, resolver timing, archive/cache sizes, committee verification and native strategy separation. Numeric example tuning and mock committee/key generation are not selected application production settings.

#### Source reading order

Read node → Marshal assembly → App callbacks → Engine open/start → Update/delivery → native proposal/order code. Read QMDB only after distinguishing transaction execution, root preparation and durable state apply. This order makes the existing owners visible before deciding whether an additional abstraction is needed.

### Source evidence from the indexed release

The [2026-10-04 reuse investigation](../../assets/review/commonware-reuse-20261004/README.md) preserves historical MCP queries, ecosystem inspections and cross-reviews. Its then-current finding that Multimmit lacked Marshal is superseded by the current source. Historical toy checks/publication receipts do not validate this App integration.
