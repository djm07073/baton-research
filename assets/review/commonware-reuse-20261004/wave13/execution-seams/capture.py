from pathlib import Path
import subprocess,json,hashlib,datetime,re
root=Path.cwd();out=root/'assets/review/commonware-reuse-20261004/wave13/execution-seams';base='78d5f2eca347b0fc04b7f7d31ff858cc2a69bee4';sha=lambda b:hashlib.sha256(b).hexdigest();blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
paths=['docs/overview/interfaces.md','docs/overview/rust-interfaces.md','docs/overview/architecture.md','docs/execution/interfaces.md','docs/execution/README.md','docs/execution/qmdb.md','docs/execution/state-sync.md','docs/consensus/ordered-input.md','docs/tx/interfaces.md','docs/e2e/normal.md','docs/e2e/canonical.md','docs/e2e/results.md','docs/e2e/state-sync.md','docs/e2e/recovery.md'];rows=[]
for p in paths:
 b=(root/p).read_bytes();assert b==subprocess.check_output(['git','show',base+':'+p]);dest=out/'documents'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);rows.append({'path':p,'sha256':sha(b),'baseline_equal':True})
md=(root/'docs/overview/rust-interfaces.md').read_text();needles=['type CommitResult','type PreparedResult','fn acknowledge','fn on_commit','result: Self::CommitResult'];anchors=[{'line':i+1,'text':s} for i,s in enumerate(md.splitlines()) if any(n in s for n in needles)]
diagrams=[];manifest=json.loads((root/'docs/assets/diagrams/render-manifest.json').read_text())
for name in ['diagram-02','diagram-08','diagram-09','diagram-10','diagram-11','diagram-14','diagram-17','diagram-18']:
 d=next(v for v in manifest['diagrams'] if v['name']==name);m=(root/f'docs/assets/diagrams/{name}.mmd').read_bytes();s=(root/f'docs/assets/diagrams/{name}.svg').read_bytes();found=[]
 for p in paths:
  for x in re.finditer(r'```mermaid\n([\s\S]*?)\n```',(root/p).read_text()):
   if sha(x[1].encode())==d['source_sha256']:found.append({'page':p,'line':(root/p).read_text()[:x.start()].count('\n')+1})
 assert len(found)==1;diagrams.append({'name':name,'source_sha256':d['source_sha256'],'mmd_sha256':sha(m),'svg_sha256':sha(s),'canonical_source':found[0],'inline_match':True,'new_rendered_qa':False})
prev=root/'assets/review/commonware-reuse-20261004/wave11/execution-coverage';man=json.loads((prev/'source-manifest.json').read_text());tree=json.loads((prev/'native-tree.json').read_text());idx={v['path']:v['sha'] for v in tree['tree'] if v['type']=='blob'};src=[]
for p in ['glue/src/stateful/db/mod.rs','storage/src/qmdb/sync/engine.rs']:
 r=next(v for v in man if v['path']==p);b=(prev/r['local']).read_bytes();assert sha(b)==r['sha256'] and blob(b)==idx[p]==r['git_blob'];src.append({'path':p,'pin':r['pin'],'repo':r['repo'],'source':str((prev/r['local']).relative_to(root)),'sha256':sha(b),'git_blob':blob(b),'tree_blob':idx[p],'matched':True,'scope':'Retained wave11 primary source bytes rehashed/reread; not a new fetch'})
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':base,'pages':rows,'decisive_rust_signature_anchors':anchors,'diagrams':diagrams,'retained_source_checks':src,'scope':'Actual current document/diagram seam and owned-argument review, not compiled generic implementation or protocol execution'}
(out/'EVIDENCE.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'pages':len(rows),'diagrams':len(diagrams),'signature_anchors':anchors}))
