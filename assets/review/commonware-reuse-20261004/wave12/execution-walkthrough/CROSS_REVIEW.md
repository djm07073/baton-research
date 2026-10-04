# Wave 12 independent body/pool walkthrough review

**Pass for scoped documentation/source fit. Adopt the one TxPool select comment correction; no body reader delta is needed.** It resolves a concrete central-interface ambiguity while preserving existing ownership, cancellation, canonical processing and open backend choices. It does not change a method or make destructive selection a default.

Reviewer `/root/reuse_storage_types_v3`; reader baseline `d4915b310c0fd071d6c49b12754fd556f6879981`. Audit-only wave11 HEAD `a0fd3394b4a6c81e4abdcc4fb1f0865fc1c64970` does not change these reader bytes.

| Artifact reviewed | Exact SHA-256 |
|---|---|
| `wave12/pool-walkthrough/REPORT.md` | `8c7324b80584009ef8eece36a75b4caa143b0e09e4ed0e1216d3f20be1ac5a4f` |
| `wave12/pool-walkthrough/READER_DELTA.md` | `6a521ed8cf6b63276f5064ea4186b9be971d20cec3fabb05ba2d23785c665405` |
| `wave12/body-walkthrough/REPORT.md` | `0973b00917914aff3919c4d0d4b8dfdda779901ed4d9ae70840307cac20a3dc2` |
| `wave12/body-walkthrough/READER_DELTA.md` | `ae521a6219f73335abd5e23d5d90b3204c8f8613545b2c2f6bf3134be38b6e7b` |

`cross-review/CROSS_EVIDENCE.json` binds nine decisive current pages and the reports. Two Constantinople primary files were independently fetched and matched against a newly authenticated complete nontruncated pinned Git tree. Other unchanged body/native/Nunchi claims were checked within retained prior own source/reader review scope; this is not a fresh broad verification of every historical citation, new rendering or compiled assembly.

## TxPool select correction

The old central comment is `Selection alone does not retire transactions from the pool.` The proposed replacement is exactly:

```text
    /// Selection alone does not establish canonical retirement.
```

The correction is justified by actual source. Constantinople's private `pop_lane_proposal` (`crates/mempool/src/webserver/actor.rs:402–434`) calls `pop_front`, decrements candidate bytes, moves selected transaction material into the returned vector and records ProposedBatch digests/height. This is local destructive ownership transfer, not evidence that the selected transactions executed canonically or that unmatched material may be lost. Its public `try_submit` (`webserver/mailbox.rs:112–140`) returns eventual batch status; admission-only `try_ingest` (`:146`) is restricted. The detailed docs already expose those source/ownership differences.

Current `tx/README.md:26`, `tx/interfaces.md:9,30–40` and `consensus/block-body.md:87–93` require retained selected material, cancellation/reselection reconciliation and real durable canonical outcomes. A central prohibition on any pool removal can make that valid conditional adaptation appear excluded or encourage a second non-destructive pool. Naming **canonical retirement** aligns the short comment with the existing detailed contract. It authorizes neither permanent material loss nor selection-only success, and adopts neither Constantinople nor destructive selection.

Only that comment changes. The central page is the Rust authority; root should refresh the generated export from it. Five traits, all method/type/signature declarations, actor topology, backend/router/packing policies and diagrams remain unchanged. No new reconciliation actor or generalized builder is required.

## Body route and preserved boundaries

The body walkthrough correctly follows real component ownership, not an invented BlockService engine. Current pages distinguish native Context/Relay Plan and direct attachment callbacks from the registry Simplex Marshal reference; shared raw network channels from per-role networks; buffer cache get/subscribe from active generic resolver fetch; header/body/candidate join from verify completion; and cache/native publication/archive lifetimes from durable release.

Retained independently checked sources support those distinctions: native Engine callback bounds and recovered verification before actors; ingress pre-bind accepted submission with no bytes enqueued; Archive covering completion; and the release's specialized private standard Relay path. The report labels its earlier source bytes and diagram equality as retained checks rather than new retrieval or visual QA. Temporary missing/wrong peer material does not become proof of permanent expected-payload invalidity; exact retained body/parent validation and custody remain native adapter responsibilities. The candidate registry/native type graph, body codec/schema, retention, retry/publication integration and native custody proofs remain open.

Normal/canonical/recovery flows keep exact Orderer input direct to Executor, completed Executor changes to Storage, and durable Executor ACK/result handoffs outside Baton approval. No new body trait, duplicate cache/fetch/archive engine, full Stateful requirement or peer Ready/ACK is introduced by the body no-delta verdict.

## Scope and verdict

Adopt the single comment delta and the body no-delta conclusion at the bound hashes. This is documentation and actual source fit, not compiled compatibility, executed E2E, safety/liveness or benchmark evidence. All backend, workload, duplicate, codec, limit and lifecycle choices remain open. Implementing/proving engineering follow-ups remains outside the authorized documentation-research completion gate.

The original concrete assembly explanations, repeated independent research/review and verified publication/synchronization remain required. The six-hour window ends **2026-10-04 01:29:14 UTC** and is still active. This delegated cross-review does not close the goal. No canonical mutation, protocol implementation, build/test, dependency change, external checkout mutation or publication occurred here.
