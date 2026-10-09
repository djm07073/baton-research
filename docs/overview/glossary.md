# Roles and terminology

**The App owns application state and work; Multimmit and Marshal supply the existing consensus connections.** TxPool, the selected scheduler, execution workers and storage are internal responsibilities of one App. The names below do not require separate public traits, actors or crates.

## Roles and terms

| Owner or internal part | Responsibility |
|---|---|
| Multimmit Engine | Native producer signing, DA, leader proposal/voting, finality and safety recovery |
| Multimmit Marshal | Complete-block custody/broadcast/backfill, ordinary native total-order interpretation, indexed delivery and durable ACK cursor |
| App | Implement existing Automaton callbacks and the application Update reporter; own transaction and execution semantics |
| App TxPool | Validate/admit, retain selected/unselected candidates, select bounded bodies, reconcile canonical transaction outcomes |
| App Pre-cut scheduler | Admit eligible pre-cut candidates, preserve started prefix and sort pending work, reconcile finalized input |
| App Baton scheduler | The same local scheduling foundation plus intended-order reports, bounded direction selection and advisory handling |
| App execution/storage code | Execute exact parent-linked work, prepare selected roots, certify results, import verified peer material, and apply through one durable canonical writer |

The scheduler mode is chosen for the application configuration. Pre-cut has no Baton instance, report windows, direction messages or native prefix-policy modification. Both modes use the same body, pool, execution backend and storage resources. The concrete global comparator, scheduler resource limits and backend remain open.

`Automaton`, `Relay` and `Reporter` are existing Commonware traits. Marshal provides the reusable body Relay and a native-activity Reporter. The App implements Automaton and an Update Reporter; an optional native-activity handle can observe additional native activity. Different `Reporter::Activity` types require different concrete handle types when forwarding into the same App.

Engine [derives Validator when the configured scheme's `me()` returns a participant, or Observer otherwise](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/engine/mod.rs#L615); the epoch's separate [`producer_chain(participant)` mapping](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/config/protocol.rs#L202) supplies an optional local producer lane, so a validator need not be a producer.

| Data or term | Meaning and completion condition |
|---|---|
| Body digest | Hash commitment to the application payload returned by `Automaton::propose` |
| Producer header | Native epoch/chain/height/parent plus body digest; does not contain the transaction body |
| Header digest | Hash of the full producer header, including epoch/context and body digest; this is the digest requested by Relay |
| `BlockRef` | Structured producer chain, chain-local height and header digest used for exact block lookup; epoch is committed by that digest, not a separate field |
| `TransactionBlock` | Complete header plus application body; Marshal stores and broadcasts this value |
| `Custody` | Token returned after accepted `stage_block` work; its successful wait establishes durable recovery |
| `verify(true)` | Valid payload with required local custody; it does not establish execution completion or finality |
| Eligible candidate | App-retained exact validated block facts satisfying its authentication, ancestry and scheduling requirements |
| Global rule | Shared deterministic ordering for eligible not-yet-started work; preserve the started/completed prefix `F` |
| Report / direction | Authenticated intended order / leader's advisory scheduling suggestion; neither is execution proof or finality |
| Prepared policy candidate | Completed bounded planning result for possible future native authenticated adoption; current native policy integration is missing |
| `Update` | Marshal's complete finalized block with canonical `OutputIndex` and `Exact` acknowledgement |
| Execution checkpoint | Completed work for an exact base state, ordered prefix and runtime; reusable only under the same context |
| Execution result | Computed changes and outputs with provenance; a root may be deferred and canonical durability is not implied |
| Applied record | App's durable state/output/applied-index/block-identity/provenance linkage |
| Delivery ACK | Local completion signal issued after durable application; Marshal persists its cursor separately |
| Execution statement / result certificate | Full exact input/base/runtime/result subject / f+1 eligible distinct signatures on that same subject |

A producer lane's header parent is distinct from an execution predecessor across lanes. The body digest, header digest, leader proposal identity, canonical output index and application state root identify different facts. A native [`View`](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/types.rs#L257) counts consensus attempts within one epoch, producer height counts blocks in one lane, and Marshal's [`OutputIndex`](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/marshal/types.rs#L53) counts blocks in the finalized output stream. An integer output index alone is not a state root or a cryptographic block identity.

The immutable ordering frontier ends the input prefix that future direction cannot rearrange. The local started prefix `F` can include speculation and is not canonical finality. Marshal's delivery cursor and the App's applied record are also separate: a crash can require redelivery of input already durably applied.

<details>
<summary>Mapping earlier names to the current composition</summary>

| Earlier design name | Current location |
|---|---|
| BlockService / body custody adapter | Existing Multimmit Marshal plus App body codec and validity logic |
| Orderer / Baton confirmed delivery | Existing Multimmit Marshal for ordinary native order |
| Public TxPool / Executor / Storage / Baton traits | Concrete App-internal pool, work, persistence and scheduling code |
| Planner / ResultService / Runtime | Internal bounded planning, result handling and transaction computation; Commonware runtime still supplies task/I/O primitives |
| StoredBody / CandidateBlock events | Internal retained custody and eligibility facts; no mandatory new public event API |
| Executor::commit / CommitResult | Internal processing of Marshal Update through the App canonical writer and durable applied record |
| Baton::on_block / on_commit | Internal candidate admission and optional scheduling progress handling |

</details>

The historical paper and preserved reviews retain their original terminology and source pin. Current connection details are in [Baton integration](../baton/README.md), [body flow](../e2e/block-body.md), and [canonical delivery](../e2e/canonical.md).
