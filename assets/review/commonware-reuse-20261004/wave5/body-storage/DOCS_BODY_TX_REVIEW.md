# Wave 5 reader review: body, Tx and integration

Reviewer `/root/reuse_network_v3`; baseline `b5747f6a28527a4507901f2e46b426b5ff2a4b7c` plus current root-authored changes. Source/API readback only; no canonical edits, selected schema/backend/policy, extra actor, compilation or protocol verification.

**Pass. No material source/API correction is required in these four pages.** The changes supply narrow existing-owner recipes and preserve undecided choices, native cut independence and application custody/canonical responsibilities.

## Exact reviewed pages

| Page | SHA-256 |
|---|---|
| `docs/consensus/block-body.md` | `240343de16701934f3210d861356cb8882c4c4b3ac8cacb9a6bbac2e9527d192` |
| `docs/tx/README.md` | `7d1b4d26320b1c487b03437b8123923040b6c0f8713eee43f27f11f52cf555ff` |
| `docs/tx/interfaces.md` | `64c74f0663712717cb12947addd329949b2d3636a7e19f87c5a99016c1a79a52` |
| `docs/reference/integration.md` | `754d6c0b411de8549eefc6a8242eca843a9deb981cdd4fb9f5269734c0ad6295` |

Machine receipt: [docs-review/page-hashes.json](docs-review/page-hashes.json).

## Evidence scope

Body changes were checked against this role's fresh native body-storage sources/report `90ab05469a72864c2d5596bd16e50250d7c50a55165f765d641ee7cfc24991a6`, plus independent pool-source/POOL_BODY_CROSS_REVIEW `c5972eb49636db11f963da4e07e7eda581fc10f4b22fbf1fe67de1d4d15154e9`.

Tx changes were checked against the final amended pool-source report `880481a271e4f4077d760d6e1378b68eae99d767ee89782eb5922d5346018ab6` and branch-access/BRANCH_POOL_CROSS_REVIEW, including its final hydration/TTL amendment. This role independently fetched **15 decisive SDK source files** for this readback and matched each Git blob to its fresh non-truncated `eea35ced709f68c15d6fbc8bcc754696a7e44374` tree. Separate receipts: [docs-review/source-manifest.json](docs-review/source-manifest.json); fresh sources: `docs-review/sources/sdk/`. Existing native body receipts were reused, not represented as newly fetched for this readback.

## Checked semantics

| Reader change | Verification and remaining boundary |
|---|---|
| Archive lookup and sync rows | Existing borrowed async index/key lookup and consuming mutation are accurate. Prunable implements MultiArchive; has_at confirms the full key at a chosen index without reading values. No immutable MultiArchive or Clone archive reader is implied. Covering sync and immutable Freezer/Ordinal metadata recovery are already supplied. |
| Index/key/schema paragraph | First stored index value, unbounded get_all and same-key lookup ambiguity match source. Native authenticated header identity/context/body commitment and parent-header lookup remain an application binding. Stable content/header binding versus unique complete records are explicitly alternatives, not a selected format. |
| One owner and Producer/Consumer | “Existing owner” means the attachment's ownership pattern; unchanged surrounding prose still excludes the private Simplex Marshal bridge. Producer clones a request handle, not Archive. The explicit unbounded resolver serves pool and Producer admission responsibility are accurately named. Storage failures remain separate from peer Invalid and custody success. |
| Nunchi source-local adaptation | actor/pool/config/status/error/metrics imports have no SDK chain dependency. SDK common/crypto payload imports are localized in tx.rs; its generic contract, SDK NonceKey/blanket Transaction implementation, lib.rs export and manifest dependencies require coordinated source adaptation. Private Pool is not described as externally callable. |
| Feature/dependency route | Keeping SDK payload types requires transitive common/crypto and compatible native identities; nunchi-common defaults to state and gates state/runtime exports. Reader text correctly requires checking the feature graph without claiming a resolved state-free crate, compiled port or dependency-default override. No chain builder/full Stateful actor is required by the pool sources. |
| Source-aware Features/Decision | Local submit and built-in peer ingress are distinct source sites. Existing private source metrics do not supply a public source-aware submit API. Admission filtering is conditional and must reach both sites; packing-only hooks may use pending candidates. Policy is not conflated with stateless cryptographic verification. |
| Canonical processing in same mailbox | Finalized has no responder; try_send is lossy; handler invokes Pool::finalize only when processed. Proposed context-bound responder/replay/readiness extends existing Message/handle/oneshot ownership rather than introducing a reconciler or ACK gate. Current pending/status do not prove nonce-context processing; healthy-empty versus shutdown remains an integration contract. |
| Hydration, TTL and seed semantics | Unknown lanes default to zero. Authoritative hydration before eligible selection is necessary for the selected nonce-lane contract. Existing finalize advances last_height and may scan TTL; Entry.admitted_at is the old pool height. Thus high-height hydration may expire pre-seed admissions. The text accurately makes admission order/lifetime reconciliation conditional and selects no TTL, seed format or native delay. |
| Stable selected payload | Entry caches digest once, pending/gossip clone T, while PoolTransaction's Clone/Send/Sync allows interior mutation. Stable encoding/identity material is an appropriate payload contract. Existing replacement cannot mutate already frozen producer body bytes; cloning does not by itself prove immutability. |
| Integration recipe | Existing Archive/resolver and selected pool owner remain singular connections. Whole actor/kernel source reuse is a conditional maintenance route, not an exported native-compatible crate or chosen backend. Exact packing, source/decision/watermark schemas, graph port, quotas and policies remain open. |

No new heading, public trait or actor was introduced. The canonical interface page still declares exactly TxPool, Orderer, Baton, Executor and Storage. Across canonical docs, the 39 Open decisions cells remain blank and all 18 Mermaid diagrams remain. The checked prose adds no report/direction approval, full-body receipt barrier, pool ACK on native cut, or claim that source inspection verifies protocol safety/liveness/build compatibility.

The scope is the current four-page reader delta and its directly related source meanings. Unchanged broad ecosystem comparisons retain their prior independent review; this readback does not claim a fresh re-audit of every historical external citation or executable integration.
