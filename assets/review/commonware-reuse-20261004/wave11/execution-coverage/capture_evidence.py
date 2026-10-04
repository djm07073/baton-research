from pathlib import Path
import json,hashlib,re,subprocess,datetime
root=Path.cwd(); out=root/'assets/review/commonware-reuse-20261004/wave11/execution-coverage'
sha=lambda b:hashlib.sha256(b).hexdigest()
pages=['README.md','AGENTS.md','BATON_HANDOFF.md','baton-paper.md','docs/README.md','docs/SUMMARY.md','docs/overview/architecture.md','docs/overview/rust-interfaces.md','docs/overview/glossary.md','docs/execution/README.md','docs/execution/interfaces.md','docs/execution/qmdb.md','docs/execution/state-sync.md','docs/baton/README.md','docs/baton/direction.md','docs/consensus/ordered-input.md','docs/e2e/normal.md','docs/e2e/canonical.md','docs/e2e/results.md','docs/e2e/state-sync.md','docs/e2e/recovery.md','docs/reference/integration.md','docs/reference/verification.md','docs/assets/interfaces/baton.rs']
pages += [p for p in ['docs/'+v for v in re.findall(r'\]\(([^)]+\.md)\)',(root/'docs/SUMMARY.md').read_text())] if p not in pages]
anchors={
'docs/overview/rust-interfaces.md':['The five application declarations','Canonical call order:','pub trait Executor','pub trait Storage','fn execute(','fn commit(','fn prepare(','fn apply(','fn on_execution(','fn on_commit(','Never sign imported material','Return a certificate once f+1','PreparedResult is a retained/cloneable','The concrete Storage attachment','These declarations do not claim a complete state-sync API'],
'docs/execution/README.md':['Executor computes transaction changes','Executor peer communication','Completion delivery','Do not require','Root calculation is deferred','Fencing covers','## Open decisions'],
'docs/execution/interfaces.md':['execute(block)` returns completed','If ExecutionResult owns','commit(range)` validates','Complete effects','The result threshold remains f+1','assemble` is not signature validation'],
'docs/execution/qmdb.md':['Executor produces changes','Reuse guarded reads','DatabaseSet has no single root','Storage supplies a valid working batch','Generic Unmerkleized only','owned, non-Clone','Keep existing prepared handles','Public `bounds()`','Before taking the canonical DB','A separate generic read-view','Replay must use base-bound','Flattening several prefixes','result commitment must exist','exact predecessor state','Fencing worker access','Canonical promotion is more','Metadata already implements','Do not connect it as a durable-completion callback','No ACK before'],
'docs/execution/state-sync.md':['normal validator path','f+1 distinct eligible','ImportedVerified','public sync engine can be reused','Reached-target is progress','OpsRootWitness','Two handles pointing','attach_database','both certificate and applicable material'],
'docs/e2e/canonical.md':['Executor acknowledges delivery','OrderedRange(predecessor','prepare / apply exact','Durable CommitResult after','Completed ExecutionResult, hashing','Physically reclaim'],
'docs/e2e/results.md':['Computed commitment','full ExecutionStatement','No Baton gate','Do not aggregate signatures'],
'docs/e2e/state-sync.md':['normal validator path','Applicable target and material verified','Fence unfinished work','Preserve imported provenance','No own direct-execution signature','certificate alone does not stop'],
'docs/e2e/recovery.md':['State / outputs / AppliedCursor / provenance','Existing matching durable CommitResult','Delivery acknowledgement alone','Native checkpoint compaction','Idempotence verifies exact commit identity'],
'docs/consensus/ordered-input.md':['durable','export','Exact','oneshot'],
'docs/baton/direction.md':['Never await this background future','4f+1','2f+1','no direction-receipt vote','A cut does not wait'],
'docs/reference/verification.md':['completion_delayed','Auditor::state','Not run']}
rows=[]
for p in pages:
 b=(root/p).read_bytes(); target=out/'documents'/p; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(b)
 lines=b.decode().splitlines(); found=[]
 for needle in anchors.get(p,[]):
  hits=[{'line':i+1,'text':s} for i,s in enumerate(lines) if needle.lower() in s.lower()]
  found.append({'needle':needle,'hits':hits})
 rows.append({'path':p,'sha256':sha(b),'lines':len(lines),'anchors':found})
summary=(root/'docs/SUMMARY.md').read_text(); listed=re.findall(r'\]\(([^)]+\.md)\)',summary)
manifest=json.loads((root/'docs/assets/diagrams/render-manifest.json').read_text()); diagrams=[]
for d in manifest['diagrams']:
 mmd=root/f"docs/assets/diagrams/{d['name']}.mmd"; svg=root/f"docs/assets/diagrams/{d['name']}.svg"
 matches=[]
 for p in listed:
  fp=root/'docs'/p
  for match in re.finditer(r'```mermaid\n([\s\S]*?)\n```',fp.read_text()):
   if sha(match[1].encode())==d['source_sha256']:
    matches.append({'page':'docs/'+p,'line':fp.read_text()[:match.start()].count('\n')+1})
 assert len(matches)==1,(d['name'],matches)
 assert mmd.read_text().rstrip('\n')==re.findall(r'```mermaid\n([\s\S]*?)\n```',(root/matches[0]['page']).read_text())[next(i for i,v in enumerate(re.findall(r'```mermaid\n([\s\S]*?)\n```',(root/matches[0]['page']).read_text())) if sha(v.encode())==d['source_sha256'])]
 diagrams.append({**d,'canonical_match':matches[0],'mmd_sha256':sha(mmd.read_bytes()),'svg_sha256':sha(svg.read_bytes()),'source_equal':True,'render_inspected':False})
text=(root/'docs/overview/rust-interfaces.md').read_text(); blocks=re.findall(r'```rust\n([\s\S]*?)\n```',text)
body='\n\n'.join(re.sub(r'^use std::future::Future;\n\n','',b) for b in blocks)
expected='// @generated from docs/overview/rust-interfaces.md; edit that Markdown source.\n// Application interface proposals only; no protocol implementation.\n\nuse std::future::Future;\n\n'+body+'\n'
assert expected==(root/'docs/assets/interfaces/baton.rs').read_text()
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),'scope':'Read-only canonical source/hash/diagram equality audit; no build, Rust compile, E2E or visual rendering','pages':rows,'diagrams':diagrams,'rust_export_exact':True,'application_traits':re.findall(r'pub trait (\w+)',text)}
(out/'document-diagram-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
previous=['wave5/branch-access/REPORT.md','wave6/repeated-sync/REPORT.md','wave7/execution-tree/REPORT.md','wave8/state-query/REPORT.md','wave9/storage-fixtures/REPORT.md','wave4/compatibility/CERTIFICATION_CROSS_REVIEW.md','wave10/storage-coherence/REPORT.md']
lineage=[]
for p in previous:
 fp=root/'assets/review/commonware-reuse-20261004'/p
 if fp.exists():lineage.append({'path':'assets/review/commonware-reuse-20261004/'+p,'sha256':sha(fp.read_bytes()),'scope':'Previously source-checked evidence; not claimed freshly refetched in wave11'})
(out/'retained-review-lineage.json').write_text(json.dumps(lineage,indent=2)+'\n')
print(json.dumps({'head':receipt['head'],'pages':len(rows),'diagrams':len(diagrams),'traits':receipt['application_traits'],'export':True,'unmatched_anchors':[{'page':r['path'],'needle':a['needle']} for r in rows for a in r['anchors'] if not a['hits']]}))
