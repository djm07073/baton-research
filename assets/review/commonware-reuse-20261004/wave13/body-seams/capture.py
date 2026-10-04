from pathlib import Path
import hashlib,json,re,subprocess,datetime
root=Path.cwd();out=root/'assets/review/commonware-reuse-20261004/wave13/body-seams';sha=lambda b:hashlib.sha256(b).hexdigest();head=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip();assert head=='78d5f2eca347b0fc04b7f7d31ff858cc2a69bee4'
paths=['docs/overview/architecture.md','docs/overview/glossary.md','docs/overview/interfaces.md','docs/overview/rust-interfaces.md','docs/overview/networking.md','docs/tx/interfaces.md','docs/tx/README.md','docs/consensus/block-body.md','docs/consensus/ordered-input.md','docs/consensus/README.md','docs/baton/interfaces.md','docs/baton/direction.md','docs/execution/interfaces.md','docs/e2e/block-body.md','docs/e2e/native-consensus.md','docs/e2e/normal.md','docs/e2e/canonical.md','docs/e2e/recovery.md','docs/reference/integration.md'];record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':head,'pages':[]}
for p in paths:
 b=(root/p).read_bytes();assert b==subprocess.check_output(['git','show',head+':'+p]);dst=out/'reviewed-docs'/p;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b);record['pages'].append({'path':p,'sha256':sha(b),'baseline_equal':True})
record['tracked_docs']=[]
for p in subprocess.check_output(['git','ls-files','docs']).decode().splitlines():
 b=(root/p).read_bytes();assert b==subprocess.check_output(['git','show',head+':'+p]);record['tracked_docs'].append({'path':p,'sha256':sha(b)})
record['diagrams']=[]
for p in root.glob('docs/**/*.md'):
 text=p.read_text()
 for m in re.finditer(r'```mermaid\n(.*?)```\s*\n\[Open full-size diagram\]\(([^)]+)\)',text,re.S):
  block=m[1].strip();svg=(p.parent/m[2]).resolve();mmd=svg.with_suffix('.mmd');assert mmd.read_text().strip()==block
  record['diagrams'].append({'page':str(p.relative_to(root)),'source':str(mmd.relative_to(root)),'source_sha256':sha(mmd.read_bytes()),'svg_sha256':sha(svg.read_bytes()),'inline_matches':True})
assert len(record['diagrams'])==18
md=(root/'docs/overview/rust-interfaces.md').read_text();record['traits']=re.findall(r'^pub trait (\w+)',md,re.M);assert record['traits']==['TxPool','Orderer','Baton','Executor','Storage']
record['blank_decisions']=0
for p in root.glob('docs/**/*.md'):
 active=False
 for line in p.read_text().splitlines():
  if line.startswith('| Item | Decision |'):active=True;continue
  if active and not line.startswith('|'):active=False
  if active and re.fullmatch(r'\|[^|]+\|\s*\|',line):record['blank_decisions']+=1
assert record['blank_decisions']==39
(out/'CURRENT_READER_RECEIPT.json').write_text(json.dumps(record,indent=2)+'\n')
treepath=root/'assets/review/commonware-reuse-20261004/wave11/body-coverage/trees/native.json';tree=json.loads(treepath.read_text());assert not tree['truncated'];index={e['path']:e['sha'] for e in tree['tree']}
sources=[('wave7/body-codec/sources/native','consensus/src/multimmit/types/block.rs'),('wave7/body-codec/sources/native','consensus/src/multimmit/machine/admission.rs'),('wave7/body-codec/cross-review-sources/native','consensus/src/multimmit/types/activity.rs'),('wave7/body-codec/cross-review-sources/native','consensus/src/multimmit/actors/voter/actor.rs'),('wave11/body-coverage/independent-cross-review/sources','consensus/src/multimmit/machine/reducer.rs'),('wave8/body-receive/sources/native','broadcast/src/buffered/engine.rs'),('wave8/body-receive/sources/native','resolver/src/p2p/engine.rs'),('wave5/body-storage/sources/native','storage/src/archive/prunable/storage.rs'),('wave5/body-storage/sources/native','storage/src/archive/immutable/storage.rs')]
manifest={'pin':'534af0ede48affd35b2111522527547b4cc9bf72','repo':'commonwarexyz/monorepo','tree':str(treepath.relative_to(root)),'tree_sha256':sha(treepath.read_bytes()),'scope':'Previously independently fetched pinned primary bytes and complete tree reread/rehashed; no fresh wave13 retrieval, no new API claim','sources':[]}
for folder,p in sources:
 local=root/'assets/review/commonware-reuse-20261004'/folder/p;b=local.read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert blob==index[p];manifest['sources'].append({'path':p,'local':str(local.relative_to(root)),'sha256':sha(b),'git_blob':blob,'tree_blob':index[p]})
(out/'SOURCE_LINEAGE_RECEIPT.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'pages':len(record['pages']),'tracked':len(record['tracked_docs']),'diagrams':len(record['diagrams']),'sources':len(sources),'reader_receipt_sha':sha((out/'CURRENT_READER_RECEIPT.json').read_bytes()),'source_receipt_sha':sha((out/'SOURCE_LINEAGE_RECEIPT.json').read_bytes())},indent=2))
