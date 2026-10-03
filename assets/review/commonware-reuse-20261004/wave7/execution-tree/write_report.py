from pathlib import Path
import json,re,hashlib,datetime
p=Path(__file__).parent
pin='534af0ede48affd35b2111522527547b4cc9bf72'
def s(path,line,label):return f'[{label}](https://github.com/commonwarexyz/monorepo/blob/{pin}/{path}#L{line})'
def c(path,line,label):return f'[{label}](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/{path}#L{line})'
def a(path,line,label):return f'[{label}](https://github.com/commonwarexyz/alto/blob/1d87569348b5560699465a72d691d90f18affb9c/{path}#L{line})'
b='storage/src/qmdb/any/batch.rs';cb='storage/src/qmdb/current/batch.rs';chain='storage/src/qmdb/batch_chain.rs';proc='glue/src/stateful/actor/processor/mod.rs';g='glue/src/stateful/db/mod.rs'
report=f'''# Wave 7 — reuse existing branch handles beneath the execution tree

Reviewer: `/root/reuse_storage_types_v3`. Source/API audit only; no compilation, protocol implementation, backend selection, or integration proof. Baseline: published wave 6 `f2973dd` / GitBook `NFuXtAIdglYgcndKT0Ly`. Actual native pin `{pin}` remains authoritative. Constantinople and Alto are distinct dependency graphs; this report extracts ownership patterns, not drop-in actor/type compatibility.

## Finding

Reuse the existing sealed QMDB handles and owned one-shot drafts. Executor needs an application-context-to-handle association and lifetime authority, not another implementation of QMDB ancestor diffs, Merkle nodes or bitmap layers. **Public ancestry metadata does not supply application ancestry or automatic branch garbage collection.** Deferred roots still require the already-documented unsealed-effects/read/replay connection; there is no newly found public unsealed multi-child fork API.

The small new reader delta is explicit retained-ancestor ownership plus the distinction between `Current::root()` and the ops-root in its public `Bounds`. Current docs already cover keyed/staged access, sealed-only forking, replay conditions, shared fencing and canonical recovery; do not repeat those sections or add a new public trait.

## Exact public surface and private boundary

`commonware_storage::qmdb::batch_chain` is a public module. In this inspected module there is no public `BatchChain` owner type. Its public structures are `Commitment<F,D>`, `AncestorBounds<F,D>` and `Bounds<F,D>`, with `F: Family`, `D: Digest`. `Commitment` equality compares **both** operation size and authenticated root. `Bounds` exposes `base`, `db`, `tip`, newest-first `ancestors`, and `inactivity_floor`. These are storage commitments/floors, not execution block hashes, runtime identities, result provenance, or membership certificates. {s('storage/src/qmdb/mod.rs',85,'Public module')}, {s(chain,30,'Public projections')}.

The live object walk (`ancestors`, `parent_and_ancestors`), bound collection, inherited-boundary adjustment and validators are all `pub(crate)`. `Bounds::validate_apply_to` is not an externally callable preflight. The Weak walk stops on a failed upgrade. Consumers should call concrete public DB `validate_batch`; they cannot import these private helpers as an external application API. {s(chain,98,'Private validation')}, {s(chain,120,'Private live ancestor walk')}, {s(chain,173,'Private effective boundary')}.

Source signatures, not a compiled assembly:

```rust
// Native Any, F: Family, H: Hasher, U: Update, S: Strategy;
// database methods also require Context, operation journal/index and Codec bounds.
Db::to_batch(&self) -> Arc<MerkleizedBatch<F, H::Digest, U, S>>
MerkleizedBatch::new_batch<H>(self: &Arc<Self>) -> UnmerkleizedBatch<F, H, U, S>
// new_batch: H: Hasher<Digest = D>, Operation<F,U>: Codec.
MerkleizedBatch::bounds(&self) -> &Bounds<F, D>
Db::validate_batch(&self, batch: &MerkleizedBatch<F, H::Digest, U, S>)
    -> Result<(), crate::qmdb::Error<F>>
Db::apply_batch(self, batch: Arc<MerkleizedBatch<F, H::Digest, U, S>>)
    -> Result<(Self, Range<Location<F>>), crate::qmdb::Error<F>>
// Native Current adds F: Graftable and const N: usize to the relevant types.
CurrentMerkleizedBatch::root(&self) -> D
CurrentMerkleizedBatch::ops_root(&self) -> D
CurrentMerkleizedBatch::bounds(&self) -> &Bounds<F, D>
```

The above uses `Db::...` labels for readability; these are method signatures copied from generic impls, **not executable Rust or selected aliases**. Any `to_batch` requires `F: Family`, `E: Context`, `C: Contiguous<Item=Operation<F,U>>`, `I: UnorderedIndex<Value=Location<F>>`, `H: Hasher`, `U: Update`, `S: Strategy`, `Operation<F,U>: Codec`. Its validate/apply impl requires `C: Mutable<...>`; sealed `new_batch` requires `H::Digest=D`. Current uses `F: Graftable` with the same operation/journal/digest pattern and bitmap `N`. {s(b,2718,'Any validation/apply bounds')}, {s(b,2867,'Any anchor bounds')}, {s(cb,1078,'Current child bounds')}, {s(cb,1138,'Current anchor bounds')}.

Both concrete `to_batch` methods construct an initial sealed handle of the **already computed committed state**, rather than executing/sealing a new pending change batch. This can supply an owned fork anchor without another root computation on an abandoned execution attempt. The anchor is still a branch-scoped view, not a durable historical snapshot across divergent DB changes. {s(b,2894,'Any existing-state anchor')}, {s(cb,1151,'Current existing-state anchor')}.

**Current `bounds()` delegates to its Any inner batch. Its `tip.root` is the ops-only root; `Current::root()` returns the canonical root.** Existing `ops_root()` makes this distinction explicit. Application result-root schema is still undecided; neither public bounds nor `validate_batch` chooses or verifies the full execution statement. Current preflight delegates to Any's storage applicability test. {s(cb,1052,'Distinct roots and delegated bounds')}, {s('storage/src/qmdb/current/db.rs',776,'Current storage preflight')}.

If glue DB wrappers fit, retain their existing `AnyMerkleized`/`CurrentMerkleized` clones. `AnyMerkleized` owns a private inner `Arc` and cloned `Shared<Db>`; its public `Deref` exposes the concrete batch's `root/bounds` methods. No public accessor exports that inner `Arc`, live parent objects, or internal refcount. The generic `Merkleized` trait exposes only `root/new_batch`; `DatabaseSet::fork_batches` takes a sealed parent and its associated sealed type is `Clone`. `DatabaseSet` itself is reusable without `Application`, but its tuple sealing/durability constraints remain those of earlier waves. {s('glue/src/stateful/db/any.rs',153,'Wrapper ownership/clone')}, {s('glue/src/stateful/db/any.rs',213,'Concrete Deref')}, {s(g,307,'Generic sealed contract')}, {s(g,508,'Existing DatabaseSet and sealed fork')}.

## Minimum handle ownership recipe

This is proposed wiring, not a new public module, actor, retention policy or compiled sketch:

1. Resolve Executor's exact execution-parent context to an existing applied-state or prepared sealed handle. Associate it with the exact execution identity/base/runtime/order and direct/imported provenance already required by the docs. Native producer-header parent identity alone cannot perform this association.
2. Fork from the selected sealed handle through its existing `new_batch`, or through `DatabaseSet::fork_batches`. Give each owned unsealed draft to one execution attempt; do not clone it or extract its private mutation map. When continuing root-deferred effects, keep the previous wave's separate validated effects/read/replay route; an unsealed draft cannot be passed as this sealed parent.
3. Retain strong handles for every **still-needed unapplied ancestor**, alongside child handles. An unsealed Any child holds its immediate sealed parent strongly; sealed parent links are Weak. The private merkleization machinery temporarily collects ancestor handles strongly. Keeping a leaf alone is not a substitute for the needed live ancestors during later read-through, child construction and merkleization. {s(b,202,'Child base ownership')}, {s(b,338,'Weak sealed parent')}, {s(b,1313,'Temporary strong collection')}, {s(b,2587,'Public child retention contract')}.
4. On selected root preparation, consume only the relevant draft/material through existing merkleize. Sealed data internally retain ancestor diff/Merkle data for apply; this does **not** mean every original ancestor object stays alive or that future get/fork remains valid after those objects are discarded. The lower Merkle docs distinguish retained ancestor data, Weak lookups and invalid use; invalid batch methods can return incorrect data without an error. {s('storage/src/merkle/batch.rs',33,'Data retention versus object liveness')}, {s('storage/src/merkle/batch.rs',59,'Invalid batch methods')}.
5. Under the shared canonical access/writer authority, verify full application context and perform public DB `validate_batch` before consuming apply. Native applicability accepts exact `(size,root)` at the initial DB boundary or an ancestor commitment and checks applicable commit floors. It rejects a divergent committed sibling, but neither authorizes worker access nor verifies an execution certificate, application ancestry or provenance. Validation and use must remain fenced together. `apply_batch` also validates and consumes the DB; it returns local operation range, not a durable execution ACK. {s(chain,188,'Exact storage applicability')}, {s(chain,206,'Floor validation')}, {s(b,2733,'Public retaining preflight')}, {s(b,2743,'Apply and durability boundary')}.
6. Remove rejected application-context entries and adoption authority only after worker/access fencing. Drop their existing batch handles when no legitimate owner or recovery/query/sync retention needs them. Arc/wrapper cloning and dropping reuse ownership; they do not compute safe application retention or revoke shared database access. Compatible descendant handles can remain while canonical advances through their actual storage ancestors. Required durable state/output/cursor/provenance linkage remains Storage's responsibility.

No new `get_parent`, `is_ancestor`, `retain_tree`, `prune_tree` or reference-count API is implied. Public `Bounds.ancestors` is a commitment projection; applications can inspect it, but it does not replace the existing DB validator or identify original executed-order parents. Wrapping an existing glue wrapper in another `Arc` does not expose its internal reference count or identify all active worker/state-sync owners.

## Existing actor and chain examples do not supply a public execution tree

Native Stateful already implements a parent-index ownership pattern: private `PendingEntry` stores parent/round/prepared material; `compatible_pending` builds children-by-parent and traverses descendants; finalization retains the winner clone while applying another, removes incompatible pending entries, then releases the retained winner. Its private `fork_batches` resolves pending/finalizing/applied anchors. **These helpers are private, depend on `Application`, and use its certified block context.** They demonstrate using existing batch handles under an owner, not a public generic tree to import or a requirement to adopt the full actor. {s(proc,188,'Private pending/context association')}, {s(proc,222,'Private descendant traversal')}, {s(proc,992,'Winner clone and compatible retention')}, {s(proc,1173,'Private parent resolution')}.

Constantinople's actual app uses glue batch aliases, produces `StateStaged + StateUpdates`, and separately runs `finalize_execution` to seal state/history batches. Its propose/verify methods obtain block ancestry while accepting DB batches supplied by Stateful; those two inputs are deliberately separate. This corroborates reuse of branch material and cleanup ownership, not native Multimmit producer ancestry being the desired execution-parent relation. It does not contribute a public rootless tree primitive. {c('crates/application/src/consensus/db.rs',58,'Concrete state batch alias')}, {c('crates/application/src/consensus/db.rs',118,'Separate sealing')}, {c('crates/application/src/consensus/execution.rs',159,'Rootless computation')}, {c('crates/application/src/consensus/glue.rs',64,'Separate ancestry and batch inputs')}.

Alto's inspected `chain::Application` implements consensus `Application`, consumes parent block ancestry and makes timestamp/load-data blocks. It does not use QMDB execution branching in these inspected files. Its block-parent interface and Marshal wiring cannot be presented as a state checkpoint/tree implementation. This is a finding about inspected application/engine sources, not an exhaustive repository claim. {a('chain/src/application.rs',51,'Actual consensus app')}, {a('chain/src/application.rs',70,'Block parent use')}.

## Memory drop versus physical retention

In-memory `Arc` ownership releases batch data when its owners release it. Current's private bitmap chain `trim_committed` collapses committed layers during child construction; that optimization is not an application tree prune API. No explicit caller-visible `strong_count` threshold, auto-prune policy, worker barrier or durable ancestry export was found in these audited public batch surfaces. {s(cb,935,'Private bitmap chain')}, {s(cb,975,'Private committed-layer trimming')}.

Physical history deletion reuses consuming DB `prune(prune_loc)` with native floor/sync-boundary limits. Any pruning leaves root/snapshot unaffected, but uncommitted operations are not guaranteed after a crash; Current further commits its log before advancing persisted pruning metadata and rejects a prune beyond safe sync boundary. These limits protect DB recovery, not every application-required certificate/output/cursor/query/history material. Storage must still keep the selected durable recovery contract and required material; no numerical boundary or GC schedule is chosen here. {s('storage/src/qmdb/any/db.rs',457,'Any physical prune')}, {s('storage/src/qmdb/current/db.rs',538,'Current prune and persistence order')}.

Native Stateful's verification quiescence/full-prune barrier and private prune-target cadence are reference lifecycle code; adopting those private owners or their retention defaults is not required. Access fencing still covers all cloned handles. Background hashing over retained snapshots can outlive caller cancellation without granting stale-result adoption; this does not permit live invalid branch reads. {s('glue/src/stateful/actor/core/verifications.rs',158,'Private prune barrier')}, {s(proc,489,'Private history-target coordination')}.

## Evidence and limits

`source-manifest.json` contains 18 freshly fetched pinned raw files, SHA-256 and Git blob IDs checked against three freshly retrieved, complete, nontruncated Git trees. All 18 match. Native actual graph remains the pinned git workspace; Constantinople/Alto graphs are not silently unified or upgraded.

`release-batch-chain-mcp.json` is a fresh explicit `v2026.9.0` Commonware MCP `get_file` response, lines 25–215 (server numbering is zero-based). It corroborates the public projection/private walker distinction for the indexed release. Its SHA-256 is recorded in `verification.json`; it does not replace actual native evidence or establish crate identity compatibility.

Only source/API fit is established. No protocol compile, runtime trace, pruning test, safety proof, performance result or implementation was produced. Existing five public Baton traits/signatures, direct/imported provenance, root-before-own-sign, root deferral, no-wait cut, exact shared writer/access fencing and open storage/schema/codec/sealing/prune choices remain unchanged.
'''
(p/'REPORT.md').write_text(report)
delta=f'''# Minimal proposed reader delta

Source/API clarification only. No public trait/signature change; no new diagram, actor, backend or policy. Current docs already cover deferred-root read/replay, live-DB fencing and logical-versus-physical pruning. Do not duplicate those sections.

## docs/execution/qmdb.md — after the branch-scoped-view paragraph

Suggested prose:

> Retain the existing prepared batch handles for each still-needed unapplied ancestor. A child draft holds its immediate sealed parent strongly, while sealed parent links are Weak; keeping only the leaf does not preserve every ancestor object needed for later reads, forks and merkleization. Public `bounds()` exposes storage commitments and ancestor bounds, not live parent handles or execution-node identity. With Current, these bounds carry the ops-only root; `root()` returns the canonical root. Use the existing DB applicability checks alongside Executor's exact-context association and shared access fence. Release unused handles separately from Storage's durable-history pruning.

Suggested citations: {s(b,2587,'Child lifetime')}, {s(b,338,'Weak sealed parent')}, {s(chain,65,'Public bounds')}, {s(cb,1052,'Current root distinction')}.

The phrase “still-needed” preserves open retention/sealing choices. It does not promise that all callers can discard an ancestor immediately on child merkleization, or that Arc strong counts prove worker quiescence/durable recovery.

## docs/execution/interfaces.md

No additional prose needed. The existing internal completed/prepared handoff and Storage ownership already fit concrete handles. Do not add a public tree/view trait or require Stateful Application.
'''
(p/'READER_DELTA.md').write_text(delta)
rows=json.loads((p/'source-manifest.json').read_text());anchors=[]
for repo,pin,path,line in re.findall(r'https://github.com/([^/]+/[^/]+)/blob/([^/]+)/([^#)]+)#L(\d+)',report+delta):
 matches=[x for x in rows if x['repository']==repo and x['pin']==pin and x['path']==path]
 assert matches,(repo,path);r=matches[0];lines=(p/r['local']).read_text().splitlines();n=int(line);assert 0<n<=len(lines)
 anchors.append({'repository':repo,'pin':pin,'path':path,'line':n,'line_text':lines[n-1],'source_sha256':r['sha256']})
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_count':len(rows),'errors':[x for x in rows if 'error'in x],'blob_matches':all(x.get('blob_matches') for x in rows),'report_sha256':hashlib.sha256((p/'REPORT.md').read_bytes()).hexdigest(),'reader_delta_sha256':hashlib.sha256((p/'READER_DELTA.md').read_bytes()).hexdigest(),'release_mcp_sha256':hashlib.sha256((p/'release-batch-chain-mcp.json').read_bytes()).hexdigest(),'anchors':anchors,'compiled':False}
(p/'verification.json').write_text(json.dumps(receipt,indent=2));print({k:v for k,v in receipt.items() if k!='anchors'});print('anchors',len(anchors))
