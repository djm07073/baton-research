# Architecture

**The system collects transactions, agrees on their order, and applies their results to state.** Four layers share this work. TxPool prepares candidates, consensus fixes the order, Baton schedules work ahead of consensus, Executor computes transaction changes, and Storage prepares roots and durably applies canonical state. Read the responsibilities first, then follow the interfaces below.

## Four layers

The Tx layer collects candidate transactions. Consensus commits to producer payloads and produces ordering evidence. Baton evaluates intended-order reports and shares direction for undecided blocks. Executor owns the execution tree and computes transaction changes. Baton delivers finalized exact input directly to Executor. Storage prepares selected roots and applies canonical changes using QMDB. Receiving a body/direction, finishing computation, fixing order, certifying a result and durably applying local state are distinct milestones.

Here, **custody** means durably retaining the body and required parent material for the requested producer context so they can be recovered after a restart. [Block storage and custody](../consensus/block-body.md#body-dissemination-lookup-and-custody) describes the storage, fetch, and recovery connections.

```mermaid
flowchart TB
    C[Client / Tx API] --> T[TxPool: candidates and static policy]
    T -->|candidate batch| B[BlockService: body / custody adapter]
    B <-->|bytes / fetch / durability| BP[Commonware buffer / resolver / archive]
    B -->|payload / custody| N[commonware_consensus::multimmit]
    N -->|exact evidence / history| O[Baton: direction and confirmed-order delivery]
    B -->|StoredBody| O
    N -. Reporter artifact .-> O
    O -. PreparedPolicy .-> H[Native policy hook]
    H -. recheck / freeze .-> N
    O -->|Direction| PE[Peer Baton]
    O <-->|execute / commit / results| E[Executor: tree, execution and certification]
    E -->|completed changes / selected commit| S[Storage: roots / canonical writer / recovery]
    S -->|batch / merkleize / apply / sync| Q[Commonware QMDB]
    E <-->|signatures / certificates / change sets| V[Peer Executor]
    E -->|canonical tx outcomes to internal maintenance| T
    NET[Commonware P2P: shared by all planes] --- N
    classDef reuse fill:#dbeafe,stroke:#2563eb,color:#172554;
    classDef adapt fill:#ffedd5,stroke:#ea580c,color:#431407;
    classDef new fill:#dcfce7,stroke:#16a34a,color:#14532d;
    class N,NET,BP,Q reuse;
    class T,B,H,S adapt;
    class O,PE,E,V new;
```

[Open full-size diagram](../assets/diagrams/diagram-01.svg)

Blue marks existing Commonware engines/algorithms to reuse. Orange marks thin integration around existing components; it does not prescribe changing underlying buffer, resolver, archive or QMDB algorithms. Green marks new Baton or application semantics. BlockService directly implements upstream callbacks. Storage directly uses QMDB batches/roots/durability without adopting glue Application. Pool backend and concrete internal static policy remain undecided; admission classifies selected/unselected candidates. [Real-chain assembly recipes](../reference/integration.md#copy-the-assembly-from-real-chains) show where these components connect.

| Role | Reuse underneath it | Write at the application boundary |
|---|---|---|
| TxPool | A fitting ecosystem pool actor; existing Commonware P2P/runtime/codec | Payload hooks, bounded body packing and canonical-outcome connection; [pool choice stays open](../tx/README.md#reuse-an-existing-pool-without-importing-the-wrong-lifecycle) |
| BlockService | Buffered broadcast, generic resolver and Archive | Exact body/header/context binding, custody and retention through [upstream callbacks](../consensus/block-body.md#reuse-the-same-body-components-as-tempo) |
| Baton | Clock/tasks/P2P plus native verification, Archive/Journal/Metadata and resolver | Report admission/direction scoring, native exact witness/history interpretation and recoverable confirmed-order delivery; [no second scheduler](../baton/README.md#commonware-primitives-in-the-baton-layer) |
| Executor | Runtime tasks, crypto certificate building blocks and shared P2P | Transaction computation, execution-tree selection, exact result verification and peer sync control; [result contract](../execution/interfaces.md#reuse-certificate-building-blocks) |
| Storage | QMDB batches/Shared/DatabaseSet/Barrier; existing metadata/journal primitives where selected | Root preparation, authorized writer and recoverable state/output/cursor linkage; [storage contract](../execution/qmdb.md#commit-a-branch-to-canonical-state) |

Green roles therefore reuse infrastructure too. The colors identify responsibility boundaries, not a requirement to build a new actor, server or engine for every box.

Baton joins a StoredBody with its authenticated native header reference to produce a CandidateBlock. Existing Reporter notices for accepted artifacts can supply the header reference. The body/notice join adapter needs implementation; a new native header export hook is not automatically required.

Ordered delivery and history recovery now belong inside Baton, connected through the native exact-source export bridge still to be implemented. They require no separate order-delivery module or archive server. Its verified evidence store and the body store should reuse Commonware storage and resolver components where their contracts fit.

## Inputs and outputs between layers

| Layer | Receives | Owns | Delivers |
|---|---|---|---|
| Tx: TxPool | Transaction bytes from clients or tx peers | Structural checks, internal static selected/unselected classification at admission, and candidate retention | A bounded candidate batch to BlockService |
| Consensus: BlockService + Multimmit | Candidate transactions and peer bodies, headers, and proofs | Body construction/custody, native DA/consensus and exact evidence export | Bodies and native evidence to Baton |
| Baton | Candidate blocks, native evidence/history, context, reports and direction | Advisory direction plus independently verified continuous order, gap backfill and recoverable delivery | Prepared policy to native hook; parent-linked execute blocks and confirmed ranges to Executor |
| Execution: Executor + Storage | Baton speculative blocks and confirmed ranges, peer certificates/material | Executor: effects, logical tree, certification and sync control. Storage: selected roots, canonical apply/flush, physical retention and recovery | Completed effects; peer results; durable result to Baton internal delivery tracking and tx outcomes to pool maintenance; optional advisory progress |

## Data, control, and canonical paths

| Path | Flow | What completion establishes |
|---|---|---|
| Tx / body data | Tx API → pool → builder → body store / P2P → peer custody | Admission, body bytes and digest, local durable custody |
| Native consensus | Authenticated native network → batcher → voter / Core owner → signed artifacts | Producer ancestry, DA, view votes, native finality, extension evidence |
| Baton control | Known input / intended order → reports → leader snapshot → Baton planning → direction → execute parent-linked branches | Advisory execution order and a completed prepared candidate |
| Canonical input | Exact native evidence / policy history → Baton → Executor::commit | A continuous, irreversible sequence of exact execution inputs |
| Execution result | Executor ↔ Executor: direct-execution signatures → f+1 result certificate verification | State finalization bound to irrevocable exact order and canonical input state |
| State preparation / application | Executor effects or verified peer material → Storage selected root / QMDB apply → durability and metadata linkage | Prepared commitment before signing; durable state/output/cursor/provenance before delivery ACK |

Receiving a body, collecting report support, authenticating an ordering decision, and applying state establish different facts. Completion on one path cannot stand in for evidence required by another.

## Workers and decision authority

| Module / native owner | State it may change | Next action |
|---|---|---|
| Native Core | Signing reservations, producer, DA, view, and finality state | Voter executes typed capabilities and publishes native artifacts |
| BlockService | Body/header correlation and custody/retention integration around primitive handles | Completes upstream Automaton requests; buffer/resolver/archive own generic work |
| Baton | Reports, prepared direction/context, verified history, terminal slots and recoverable delivery cursors | Broadcasts direction, passes prepared policy, independently delivers confirmed ranges to Executor and records durable completion |
| Executor | Execution tree, completed effects, logical branch pruning, signatures/certificates and sync switching | Exchanges peer results; selects exact canonical material; returns completed effects or durable receipts |
| Storage | QMDB bases/batches/roots, canonical writer/access fence, durable state and physical retention | Prepares selected commitments; applies authorized material; recovers state/outputs/cursor/provenance |

Baton workers evaluate direction candidates. Executor workers compute transaction effects and verify results. Native Core decides policy adoption in actual native context. Executor selects exact canonical paths and authorizes direct/imported material; Storage checks applicable ancestry/access and serializes database mutation. Logical branch management and the storage writer are separate authorities, even when they share one implementation. Wire-direction freshness, local worker generations and the stable signing subject use different identity rules.

**Executor owns state finalization and state sync, including peer communication.** Baton selects direction and requests parent-linked speculative execution, then receives local execution results. Executor handles branch changes through execute(block), then canonical promotion and conflicting-branch pruning through commit(range). Baton delivers verified finalized input to Executor; its internal delivery path observes durable completion directly, and tx outcomes feed internal pool maintenance. Report/direction handling and optional advisory progress notifications are not conditions for certification, sync or canonical application. Confirmed input delivery proceeds independently inside Baton, while native consensus supplies finality authority. Signatures, certificates, and change sets travel directly between Executors. State sync is an option on the normal validator execution path. See [Execution responsibilities](../execution/README.md#roles-and-responsibilities) and [State sync](../execution/state-sync.md#state-sync-from-certified-execution-results) for verification, switching, and storage requirements.
