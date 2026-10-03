from pathlib import Path
import json,hashlib,re,datetime
b=Path(__file__).parent;w=b.parent;o=b/'independent-cross-review';m=json.loads((o/'source-manifest.json').read_text());idx={(x['repo'],x['pin'],x['path']):x for x in m['sources']}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for x in m['sources']:
 v=Path(x['local']).read_bytes();assert digest(Path(x['local']))==x['sha256'];assert hashlib.sha1(f'blob {len(v)}\0'.encode()+v).hexdigest()==x['tree_blob']
anchors=[];names=['simulated-network','storage-fixtures','fixture-boundaries'];d=o/'reviewed-reports';d.mkdir(exist_ok=True)
for name in names:
 p=w/name/'REPORT.md';s=p.read_text();(d/(name+'-REPORT.md')).write_bytes(p.read_bytes())
 for r,pin,path,line in re.findall(r'https://github.com/([^/]+/[^/]+)/blob/([a-f0-9]{40})/([^\s)#]+)#L(\d+)',s):
  x=idx[(r,pin,path)];ls=Path(x['local']).read_text().splitlines();assert 1<=int(line)<=len(ls);anchors.append({'report':name,'repo':r,'pin':pin,'path':path,'line':int(line),'line_text':ls[int(line)-1]})
m['anchors']=anchors;m['report_hashes']={name:digest(w/name/'REPORT.md') for name in names};m['reader_delta_hashes']={name:digest(w/name/'READER_DELTA.md') for name in names};m['final_report_readback_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(o/'source-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
text='''# Wave 9 network, storage and root fixture independent cross-review

Reviewer `/root/reuse_orderer_v3`. **Pass: no remaining actionable source correction found in these three reports or their proposed reader contributions.** Review is bound to the identities below; public handle availability is not compiled integration or executed test evidence.

| Reviewed report | SHA-256 |
|---|---|
'''+''.join(f'| `{name}/REPORT.md` | `{m["report_hashes"][name]}` |\n' for name in names)+'''
## Fresh evidence

Independently retrieved 40 pinned primary raw files and five newly authenticated complete nontruncated trees (native, explicit release, Tempo, Alto, Constantinople). Every raw Git blob and SHA-256 was rechecked; all 78 report source anchors resolve within the matched raw source. The corrected root report binds Alto TestFixture constructor at L94. Final immutable peer report copies and source/anchor receipts are under independent-cross-review/. Previous agent receipts and historical local files were not substituted for fresh retrieval.

## Verified reuse and limits

- Native public deterministic Runner/Context/Checkpoint and simulated Network/Oracle/Control exports, raw Sender/Receiver construction, two-argument channel registration, directed links, loss/jitter/bandwidth controls and peer Provider/Manager/Blocker signatures fit. Simulated identities/channels do not exercise encrypted socket handshake or deployment discovery. Per-link ordering remains a simulator constraint, not arbitrary reorder/duplication machinery.
- Native mocks are public under mocks/test, with non-wasm Cluster; Committee uses real but deliberately public deterministic test keys/roster/shares. Fixed Cluster type and launch_with install MockApplication/NoopReporter/Sequential even with caller transports. Mock verify and Relay are configured/no-op without full-body custody, pool/order/execution/QMDB/durable receipts. cfg(test) recording reporter/relay and checkpoint/per-plane helpers are not exposed by mocks alone. Public EngineConfig/Engine::start permit the actual application attachment without a new simulator.
- Per-node Cluster crash aborts/joins under an enclosing live runtime/network and re-registers node planes on restart; whole runtime Runner checkpoint recovery instead clears tasks/root, retains supported runtime state and reconstructs network/shutdown state. Its panic cleanup resumes the panic rather than returning a checkpoint. Escaped runtime/context references are rejected. These mechanisms do not prove single-writer application recovery or preserve escaped external tasks.
- DelayedSyncContext publicly forwards Spawner and lower-level runtime capabilities. PendingSyncs default parks started sync completions before inner sync; completion_delayed starts the inner operation first and parks its completion waiter. A blocking sync is only held by its separately armed one-shot gate; default PendingSyncs does not gate every plain sync/write. In deterministic memory, inner start_sync synchronously updates retained partition content, while arbitrary inner backends may still be running. Native-only constructor absence from release is exact. Queue/start/entered/completion counts and release controls do not provide a Baton commit receipt or all-store durability.
- Native WriteFault/SyncFault wrappers lack Spawner in the inspected file; no unsupported drop-in QMDB context claim remains. FaultConfig native Option<f64>/partial rate and release Probability/WriteConfig/ResizeConfig differences are explicit. Native partial write/resize may sync effects before error, and a failed synchronous write can change its open buffer. An error is not side-effect-free. Runtime memory partition/audit scope differs from open live buffers and filesystem/device crash guarantees.
- QMDB apply_batch, commit/start_sync/sync and Barrier failure boundaries fit actual source: apply is not durability; awaited handles cover their supplied work; ordinary deferred I/O errors panic after DB advancement, while Closed/Aborted yield false. Shared interrupted by-value writer may leave its DB empty/fatal; fixture recovery must reopen, not put back obsolete ownership or assert rollback. Existing state/output/cursor/provenance and direct/imported certificate/material/fencing obligations remain application-level.
- Existing glue::simulate EngineDefinition and Plan/Crash are feature-gated reusable fixture machinery with explicit State:ProcessedHeight and channel/lifecycle contracts. No full Stateful dependency, backend, generic framework or new public production trait is adopted. QMDB/Constantinople held-ACK property suites remain private/test-gated source examples; same-runtime DB reopen is not whole-process crash evidence.
- Tempo public workspace E2E setup really starts simulated consensus channels with actual Simplex/body/Marshal assembly and a separate OS-thread Tokio/Reth runtime/database. Returning audit.state is not by itself a two-run comparison or application invariant. Native Context strategy uses a single executor-thread Rayon pool; manually external VM/thread/I/O futures do not inherit deterministic scheduling. Pacer is external-feature gated and can block/deadlock if work needs its own current thread; no blanket external determinism claim is made.
- Alto chain replay test is cfg(test), starts validators with deliberately held uploads, obtains checkpoint, re-registers validators without relinking peers, then checks recovered uploads and durable queue draining. Follower TestFixture is private cfg(test), four seeded identities with Simplex/VRF certificate material; source pattern only, not adopted native n=5f+1 or Baton import/custody/canonical receipt proof. Root's L94 constructor correction is source-fit.

No report claims executed results, proof closure, selected fixture workload/topology/fault defaults or a compatible compiled native/registry graph. Every proposed reader case stays Not run. Direct Orderer→Executor→Storage and verified f+1/applicable-material-before-stop/provenance/writer-fence/durable cursor semantics remain intact.

## Reader precision follow-up

A separate reader review found the table shorthand `multimmit::mocks::Cluster` was not an exported exact path; root was asked to use `multimmit::mocks::cluster::Cluster`, as mocks/mod.rs exports pub mod cluster without reexporting Cluster. The same shorthand in this reviewer's own native-fixtures introduction/delta has been corrected to report29eb5f5.../delta507f653d.... That exact-path correction does not change these three report conclusions, their public attachment boundaries or policy choices. Final canonical reader review binds its post-correction page hash separately.

No canonical edits, implementation, dependency changes, compile/test/fuzz execution or benchmark were performed. Any changed report hash requires checking that revision.
'''
(b/'NETWORK_STORAGE_ROOT_CROSS_REVIEW.md').write_text(text)
r={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':'pass_no_remaining_report_corrections','report_hashes':m['report_hashes'],'reader_delta_hashes':m['reader_delta_hashes'],'source_manifest_sha256':digest(o/'source-manifest.json'),'fresh_files':40,'complete_trees':5,'anchors':78,'cross_review_sha256':digest(b/'NETWORK_STORAGE_ROOT_CROSS_REVIEW.md'),'canonical_edits':False,'compile_test_implementation':False}
(b/'NETWORK_STORAGE_ROOT_CROSS_REVIEW_RECEIPT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
