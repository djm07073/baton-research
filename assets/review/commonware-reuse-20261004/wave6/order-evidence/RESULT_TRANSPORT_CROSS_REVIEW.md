# Independent review — Wave 6 result transport and architecture reuse table

**Verdict: no required correction found in the assigned final report or current architecture table.** The report distinguishes existing transport/storage APIs from Executor's result semantics, does not select a quorum/backend/codec, and preserves normal-path peer sync with direct/imported provenance and canonical writer control.

Reviewed report: `wave6/result-transport/REPORT.md`, SHA-256 `f534d220401cc8f05d4cc4c96e574c2861e1a9760753e53d83bdc457a3efbed3`. Reviewed architecture: `docs/overview/architecture.md`, SHA-256 `1e9a61fc4830cef9ff5e70710416bfd9cc7c5411411e8548d443ba0bbbee41db`. Receipt binds these and supporting execution/interface/sync pages; later edits require recheck. No canonical edits, implementation, build or protocol test were performed.

## Independent evidence

Freshly retrieved all 38 report source files and both complete, non-truncated native/release Git trees; every Git blob matches its pinned tree and every source hash matches the report's supplied manifest. Added three fresh native runtime/parallel/future-pool files for the architecture table: total 41 fresh files. All 41 report source anchors fall within the independently retrieved correct files. `result-cross-review/source-manifest.json` retains sources, identities and anchor receipts.

I independently compared the report's saved explicit `v2026.9.0` MCP mailbox response against my newly fetched release `d476a2361ce6840d2b9d0aa6fb30a924429046d4` bytes. All 66 displayed numbered lines match at a +1 GitHub line offset; the native mailbox bytes match the release. This corroborates the saved MCP receipt. I did not invoke MCP anew, and this one file's identity does not establish general package compatibility.

## Decisive API checks

| Claim reviewed | Independent result |
|---|---|
| Buffered cache is keyed by artifact digest, not a signature accumulator | Confirmed. Global `items` retains one Arc per digest, with per-peer deque references. Different responses using only a common execution-subject digest can collapse to the already resident object. Known-digest get/subscribe does not expose an arbitrary message stream or start fetch. Waiters are notified before residency eligibility, so transport/provider/cache membership cannot supply signer authority |
| Typed P2P preserves peer identity and decodes, without application signature verification | Confirmed. `wrap(config,pool,sender,receiver)` returns the wrappers; `recv` returns transport public key plus decode result, using complete `decode_cfg`. `send_ref` reports accepted transport peers, not delivered/certified/durable completion. Background wrapper is optional, bounds decode jobs by Strategy parallelism and drops decoded overflow; no unconditional thread offload claim |
| Collector count precedes application validation | Confirmed. Engine tracks commitment -> accepted recipient keys/responded keys, inserts the responding transport peer before calling synchronous Monitor::collected, and passes responded-set length. Invalid application content can occupy that peer's slot until cancellation/reissue. There is no validation callback result or automatic request retry/timeout. Response digest/commitment *types* matching request does not enforce full statement equality |
| Collector is optional pull solicitation, not required result infrastructure | Confirmed. Existing Originator send/cancel plus Handler process oneshot and Monitor collected uses two typed channel pairs. Outstanding commitments persist until explicit cancel; handler response futures Pool is unbounded. Executor must validate eligible distinct original signers independently of transport peers/count |
| QMDB P2P Actor and mailbox can be reused below Stateful | Confirmed conditionally on stated DB/Shared Source/Codec/Send/Sync/Family bounds. The public constructor/start/mailbox are independently usable. This does not require full Stateful/Application or make arbitrary changes/outputs QMDB operations |
| attach_database completion is enqueue, not readiness | Confirmed. Inherent method discards enqueue feedback; AttachableResolver returns immediately ready Future. Only actor processing replaces the serving DB. Retention, processed attachment and canonical writer authority are separate conditions |
| Numeric QMDB request is narrower than authenticated execution identity | Confirmed. Operations request contains size/start/max_ops, Boundary contains size/start. Map equality/ordering does not contain root/epoch/runtime/result/provenance. Equal numeric requests are coalesced and fan out a decoded response; actor awaits local proof approvals inline. Incompatible concurrent histories cannot be assumed interchangeable |
| Source proof feedback is separate from certificate/apply completion | Confirmed. Sync engine verifies exact proof shape/range against current or retained trusted roots, sends feedback before storing accepted operations. Actor awaiting that feedback can block its own mailbox/serve loop; holding it for f+1 collection or canonical apply adds unrelated delay |
| Generic resolver framing and subscriber semantics | Confirmed. Local subscribers are not sent on wire; response has u64 request ID, tag and length-prefixed Bytes without repeating the key. Complete/Ambiguous/Invalid/Ignored meanings match the report; Ignored retires without retry. Producer owns admission for the unbounded serve futures pool |

Decisive source locations (fresh copies have these same line numbers): buffered engine L299–375; typed codec L16–133 and L194–255; collector engine L141–235/lib L22–92; QMDB P2P actor L93–206/L231–367 and mailbox L124–173; Source L21–110/L385–420; QMDB sync engine L558–657; resolver lib L114–173/p2p engine L77–115/wire L16–151. Exact URLs and line text are bound in the source receipt.

## Execution and architecture responsibilities

The report retains the required verification before stopping unfinished execution: irrevocable exact ordered range and canonical input state, matching full statement/runtime/result, f+1 valid signatures from eligible distinct original epoch validators, and applicable verified material. The connected canonical interface/sync pages explicitly bind epoch/range/base/runtime/rule/result/output/material commitments and separate correctness certification from durability. Transport relays can carry original certificates; applying imported material cannot create the importing node's own DirectExecuted signature for that same range. Future directly executed ranges may produce own signatures. No transport/provider/collector count replaces these checks.

The architecture reuse table is appropriately conditional:

- TxPool names a fitting ecosystem actor and keeps backend/static-analysis placement open. It does not claim Commonware provides a ready-made bank mempool.
- BlockService names existing buffer/resolver/Archive and assigns exact body/context/custody retention to the application adapter.
- Orderer names native verification and existing storage/resolver where material fits, and explicitly retains exact witness handoff, merged order and durable delivery work. My separate Wave 6 native-evidence report supports why that handoff is missing; current native safety replay is not an external history archive.
- Baton names existing Clock/runtime/future pools/optional Strategy/P2P while retaining report admission/scoring/context responsibilities. No extra scheduler or direction approval round appears.
- Executor names runtime/crypto/P2P reuse and owns computation/tree/result verification/peer-sync control. Generic certificate reuse remains conditional on exact application quorum semantics, without adopting a cryptographic scheme or ordinary quorum threshold.
- Storage names public QMDB Shared/DatabaseSet/Barrier and existing journal/metadata connections, while preserving root preparation, authorized mutation and recoverable state/output/cursor ownership. Public types were confirmed in freshly retrieved native db/mod.rs; sealed-parent/rootless limits remain documented in the linked storage page.

The prose following the colors expressly says green does not require a new actor/server/engine per box, and the diagram keeps Executor-to-Executor result exchange independent of Baton. The new table does not turn an unimplemented prefix hook, sync switch or body join into an already available guarantee.

## Actionable corrections and publication limits

Required fixes: **none** for the exact reviewed report/table hashes. No new schema, service, policy or quorum is recommended through this review.

Preserve the report's adjacent caveats when applying its small reader delta: artifact identity versus full statement; collector transport count versus verified eligible original signers; attach enqueue versus processed serving readiness; numeric Source requests versus certified compatible root/history/output context. Do not shorten these into unconditional “broadcast collects signatures,” “collector creates f+1,” or “attach means ready.” This is source/API consistency review, not compiled integration, demonstrated recovery/liveness, or completion of the six-hour goal.
