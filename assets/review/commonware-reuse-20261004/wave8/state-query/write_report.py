from pathlib import Path
import json,re,hashlib,datetime
p=Path(__file__).parent;native='534af0ede48affd35b2111522527547b4cc9bf72';cp='3b6c92e76bf582855615844a4175b8304808f6a9'
def s(path,n,label):return f'[{label}](https://github.com/commonwarexyz/monorepo/blob/{native}/{path}#L{n})'
def c(path,n,label):return f'[{label}](https://github.com/commonwarexyz/constantinople/blob/{cp}/{path}#L{n})'
u='storage/src/qmdb/current/unordered/db.rs';o='storage/src/qmdb/current/ordered/db.rs';proof='storage/src/qmdb/current/proof/mod.rs';db='storage/src/qmdb/current/db.rs';anydb='storage/src/qmdb/any/db.rs';g='glue/src/stateful/db/mod.rs'
report=f'''# Wave 8 — reuse state read and proof APIs inside Storage

Reviewer: `/root/reuse_storage_types_v3`. Baseline published wave 7 / repository `99dc2c456c4b318fefb368cb39a145298f7d86b7`. Native remains `{native}`. Source/API investigation only: no implementation, compile, query protocol, backend/schema choice or proof of certified-query integration.

## New useful reader detail

Storage's existing `read` boundary can call public QMDB keyed reads and, **if a fitting Current variant is selected**, its existing active-value and exclusion proof methods/codecs. There is no need to write a second Merkle/proof implementation or create a public query actor/trait. The new detail is the precise public proof route and trusted-root/readiness binding; prior waves already cover canonical durability and sync operation proofs.

**A database proof authenticates data against a caller-trusted root. It does not certify execution, exact irrevocable order, runtime, f+1 eligible signatures, local durability or direct/imported provenance.** Executor owns the execution certificate/full statement. Storage owns canonical state/read readiness and the read/proof/root association under the existing writer/access and recoverable checkpoint contract. This report does not adopt Current, its root schema or an additional root at every speculative attempt.

## Actual public inputs and outputs

Native source method signatures; labels simplify generic impl paths and are not compilable declarations:

| Existing API | Exact input → output | Meaning/limit |
|---|---|---|
| Any keyed `get`, Current ordered/unordered `get` | `&self, &K` → `Result<Option<V::Value>, Error<F>>` (generic Any uses `U::Key/U::Value`) | Value at the applied DB's current state; None is a local lookup outcome, not an absence proof |
| Current unordered `key_value_proof` | `&self, key: K` → `Result<KeyValueProof<F,H::Digest,N>, Error<F>>` | Existing alias of `OperationProof`; fails `KeyNotFound` for absence; value itself is obtained separately |
| Current unordered `verify_key_value_proof` | `key:K, value:V::Value, &KeyValueProof, &H::Digest` → `bool` | Builds the update operation and authenticates its active bit and content against the trusted canonical Current root |
| Current ordered `key_value_proof` | `&self, key:K` → `Result<KeyValueProof<F,K,H::Digest,N>, Error<F>>` | Proof adds `next_key`, required to authenticate the ordered update |
| Current ordered `verify_key_value_proof` | `key:K, value:V::Value, &KeyValueProof, &H::Digest` → `bool` | Existing verifier supplies authenticated `next_key` from proof |
| Current ordered `exclusion_proof` | `&self, &K` → `Result<ExclusionProof<F,K,V,H::Digest,N>, Error<F>>` | Existing span/empty-commit proof; fails `KeyExists` if key exists |
| Current ordered `verify_exclusion_proof` | `&K, &ExclusionProof, &H::Digest` → `bool` | Authenticates absence against the same trusted Current canonical root |

{s(anydb,204,'Any lookup')}, {s(u,52,'Unordered get/verifier')}, {s(u,91,'Unordered proof generation')}, {s(o,103,'Ordered get/verifier')}, {s(o,144,'Ordered exclusion verifier')}, {s(o,204,'Ordered proof generation')}.

Exact native generic bounds matter. Current unordered uses `F:Graftable`, `E:Context`, `K:commonware_utils::Array`, `V:ValueEncoding`, `I:UnorderedIndex<Value=Location<F>>`, `H:Hasher`, `const N:usize`, `S:Strategy`, `Operation<F,K,V>:Codec`. Ordered uses `K:qmdb::operation::Key` and `I:OrderedIndex<Value=Location<F>>` instead. Read/verifier impls require `C:Contiguous<Item=Operation<F,K,V>>`; public key/exclusion proof generation requires `C:Mutable<...>` even though the method takes `&self`. This is a concrete journal type bound, not permission to take a canonical writer. {s(u,36,'Native unordered bounds')}, {s(u,69,'Generation journal bound')}, {s(o,87,'Ordered read bounds')}, {s(o,182,'Ordered generation bounds')}.

`OperationProof::verify` explicitly checks that the operation's bitmap bit is active before the range proof. An old operation included in the log is not sufficient to establish the key's present value. Ordered absence uses its existing authenticated next-key/span machinery or an empty commit; no corresponding public unordered exclusion method was found in this inspected unordered module. This is a scope finding, not a claim about every possible storage backend. {s(proof,577,'Active-operation verification')}, {s('storage/src/qmdb/current/ordered/mod.rs',29,'Existing exclusion variants')}.

These proof types already implement upstream codecs. Unordered key proof is `OperationProof` with `Read::Cfg=usize` (Merkle digest cap); ordered key proof uses `(usize,K::Cfg)`, and ordered exclusion uses `(usize,Update<K,V>::Cfg,V::Value::Cfg)`. Apply selected peer/frame bounds and complete decoding without copying the proof algorithm or choosing numeric limits here. {s(proof,593,'Operation codec')}, {s(o,35,'Ordered key proof codec')}, {s('storage/src/qmdb/current/ordered/mod.rs',98,'Exclusion codec')}.

Current's DB helper `operation_proof(&self,loc)` is **pub(super)**, not a directly importable external method. Public per-key APIs above are the smallest keyed route. `proof::OperationProof::new` is itself public but takes bitmap/Merkle-storage/floor/location/ops-root inputs; no need to assemble that low-level context manually just to use public key proofs. {s(db,338,'Private DB location helper')}, {s(proof,553,'Public low-level proof constructor')}.

## Minimal read/proof connection beneath the current Storage trait

1. Establish that the selected local checkpoint is available and meets the query's canonical/durable readiness contract. If a certified answer is requested, resolve the exact retained execution statement/certificate through Executor and match its selected result commitment to this checkpoint; a received peer root or a locally readable yet unflushed DB is insufficient.
2. Reuse `DatabaseSet::readers()` and `Reader<DB>::read`, or existing authorized `Shared<DB>::read`, then call the **guarded DB's inherent methods directly**. Obtain value, proof and selected root under one valid DB access authority, so canonical apply cannot interleave between those components. Associate the checkpoint/cursor/output readiness under Storage's existing multi-store contract; a single DB lock does not make separate metadata stores crash-atomic or establish f+1 certification.
3. Serve existing proof material plus the key/value/outcome and exact checkpoint/statement identity as permitted by the selected query/codec contract. A caller verifies the full trusted execution statement separately, then calls the matching QMDB proof verifier against its authorized root. No additional signature or own direct-execution evidence is inferred from a read/import.
4. Release the DB read authority once the answer material is captured. Do not retain a live guard while waiting for certificate collection, network response or another reacquisition of the same write-preferring cell. Select query/stream budgets separately; no new observer ACK or cut/report-window barrier is implied.

`Reader` has no public write-slot API; its `read` returns `ReadGuard` which publicly Derefs to `&DB`. Thus inherent `&self` DB methods, including proof generation and even raw `new_batch`, remain reachable through a guard. Do not overclaim that this generic Reader mechanically forbids all draft construction. By-value canonical apply cannot be obtained from its read guard. Query adapters should expose the desired read contract and leave canonical authorization inside Storage; no new public trait is necessary. {s(g,187,'Reader ownership')}, {s(g,205,'Public guard/Deref')}, {s(g,751,'Public set reader construction')}, {s(db,329,'Reachable raw draft construction')}.

The guard avoids an interleaved DB writer; it is **not** a retained historical snapshot. Nor should a guarded canonical query be routed through a batch wrapper `get` that reacquires the same Shared cell: writer preference can deadlock nested reacquisition. Existing fencing and selected multi-DB lock/metadata alignment continue to apply. Proof creation at a current checkpoint is distinct from root-deferred execution on unsealed effects. {s(g,142,'Write-preferring lock contract')}.

## Operation proofs are a separate query

Any `historical_proof(historical_size,start_loc,max_ops)` returns `(merkle::Proof, Vec<Operation>)` for a retained commit-boundary operation size. It rejects invalid/pruned governing commit floors; it is not a historical key-value snapshot/query engine. `proof(loc,max_ops)` uses current log size. Current `ops_historical_proof` delegates to that ops-only proof path for sync; its proof must not be checked as an active-key Current canonical-root proof. Current's public `range_proof(start_loc,max_ops)` instead returns existing `RangeProof`, operations and bitmap chunks, and `verify_range_proof` checks supplied activity status/content. It does not produce a complete proof for an arbitrary key-range query. {s(anydb,477,'Historical operation contract')}, {s(anydb,501,'Historical operation output')}, {s(db,376,'Current range material')}, {s(db,241,'Current range verifier')}, {s(db,410,'Ops-only historical path')}.

Current's ops-root/canonical-root distinction and existing `OpsRootWitness` connection are already documented by wave 6. No need to repeat them in another sync section. Pruning/retention govern available material; a historical proof does not recover deleted evidence or a missing application cursor/certificate. Preserve the existing Storage retention/recovery contract.

## Actual chain query connection

Constantinople provides a small real-chain connection: its validator `StateDbReader` adapter holds an existing `StateSyncDb=Shared<StateDb>`, acquires its read guard, maps the HTTP public key to a DB key and performs `get`. Its already-existing webserver stores this adapter in a OnceLock; requests return unavailable until the DB is attached, then return account fields. This is a thin existing DB-to-service mapping, not a separate generic query/result engine. Do **not** adopt its Account/Bank workload or full Stateful bootstrap. {c('crates/engine/src/types.rs',102,'Shared DB alias')}, {c('bin/validator/src/state_reader.rs',33,'Direct read adapter')}, {c('bin/validator/src/run.rs',957,'Attachment readiness')}, {c('crates/mempool/src/webserver/http.rs',392,'Existing HTTP lookup')}.

That example is **not a certified query**: its response has no execution certificate/root/proof and its adapter turns DB errors into None with `.ok().flatten()`, which the HTTP path treats as not found. Do not copy that conflation into Storage's `Result<ReadResult,Error>` or mistake a service-attachment signal for durable canonical readiness.

Its indexer also uses an existing `Reader` guard and `historical_proof` to extract a finalized operation range; it discards the returned proof while exporting encoded operations. This corroborates native material/query reuse, not a proof-bearing client endpoint or arbitrary historical state snapshot. Its uploader/task/service and schema are not required by Baton. {c('crates/indexer/src/publisher/qmdb.rs',1342,'Guarded operation extraction')}, {c('crates/indexer/src/publisher/qmdb.rs',1428,'Existing historical proof call')}.

## Version and source receipts

Thirty freshly fetched raw files match three fresh complete nontruncated Git trees: native, Constantinople and explicit release `v2026.9.0` resolved to `d476a2361ce6840d2b9d0aa6fb30a924429046d4`. Manifest records hashes, matching blobs and UTC. Release reference files do not replace native graph identities.

Ordered query/proof files are byte-identical between the inspected native and release pins; unordered Current differs: native `K:Array`, release `K:Key`. The MCP explicit-release `get_file` returns real numbered Rust corroborating **release** input/output and `K:Key` only. `verification.json` checks its numbered content against fresh release bytes (including the tool's terminal empty EOF line) and records hashes. No universal type compatibility claim follows.

Only the concrete public query/proof route and read/root/readiness association warrant a reader addition. Existing five traits/signatures remain unchanged. Backend/variant, root, certificate/query envelope, codecs, budgets, historical retention policy and certified-query availability semantics remain open. No compiler or protocol tests were run.
'''
(p/'REPORT.md').write_text(report)
delta=f'''# Minimal proposed reader delta — state query

Keep five public traits/signatures, policies and query/result types open. No new actor, query module, HTTP API, certified-answer format or historical snapshot abstraction is needed.

## docs/execution/qmdb.md — a short paragraph beside durability/read readiness

Suggested prose:

> Storage can reuse guarded QMDB reads and the selected variant's existing proof APIs. If Current fits the chosen root scheme, ordered/unordered `key_value_proof` authenticates an active value against its canonical root; ordered also supplies `exclusion_proof`. Their verifiers and bounded codecs already exist. Capture value, proof and root under the same valid DB read authority, then bind the retained canonical checkpoint and readiness metadata through Storage's existing contract. Local `None` and historical operation inclusion do not prove current absence. A DB proof does not supply the f+1 full execution certificate, runtime/order checks or local durability; certificate queries remain in Executor. Reader handles are guarded access, not arbitrary historical snapshots.

Citations: {s(u,58,'Current value verifier')}, {s(o,144,'Ordered absence verifier')}, {s(o,204,'Public proof generation')}, {s(g,205,'Reader guard')}, {s(anydb,477,'Historical operation scope')}.

No interface changes or additional state-sync inventory needed. A real-chain example may be omitted from reader prose: Constantinople's small lookup adapter is useful evidence but its account/error-flattening/HTTP contract is not adopted.
'''
(p/'READER_DELTA.md').write_text(delta)
rows=json.loads((p/'source-manifest.json').read_text());anchors=[]
for repo,pin,path,n in re.findall(r'https://github.com/([^/]+/[^/]+)/blob/([^/]+)/([^#)]+)#L(\d+)',report+delta):
 r=next(x for x in rows if x['repo']==repo and x['pin']==pin and x['path']==path);lines=(p/r['local']).read_text().splitlines();n=int(n);assert 0<n<=len(lines);anchors.append({'repo':repo,'pin':pin,'path':path,'line':n,'line_text':lines[n-1],'source_sha256':r['sha256']})
m=json.loads((p/'release-key-value-mcp.json').read_text());mt='\n'.join(x.get('text','') for x in m['result']['content']);ls=(p/'sources/release'/u).read_text().split('\n');pairs=re.findall(r'^([0-9]+): ?(.*)$',mt,re.M);assert pairs;diff=[(n,s) for n,s in pairs if int(n)>=len(ls) or s!=ls[int(n)]];assert not diff,diff
v={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':len(rows),'all_blob_matches':all(x['blob_verified'] for x in rows),'report_sha256':hashlib.sha256((p/'REPORT.md').read_bytes()).hexdigest(),'reader_delta_sha256':hashlib.sha256((p/'READER_DELTA.md').read_bytes()).hexdigest(),'release_mcp_sha256':hashlib.sha256((p/'release-key-value-mcp.json').read_bytes()).hexdigest(),'mcp_numbered_lines_verified':len(pairs),'anchors':anchors,'compiled':False};(p/'verification.json').write_text(json.dumps(v,indent=2));print({k:v for k,v in v.items() if k!='anchors'});print('anchors',len(anchors))
