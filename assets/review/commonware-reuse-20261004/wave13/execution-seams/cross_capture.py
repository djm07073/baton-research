from pathlib import Path
import json,subprocess,hashlib,datetime
root=Path.cwd();out=root/'assets/review/commonware-reuse-20261004/wave13/execution-seams/cross-review';sha=lambda b:hashlib.sha256(b).hexdigest();blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();wave=root/'assets/review/commonware-reuse-20261004/wave13'
reports=[]
for p in ['body-seams/REPORT.md','body-seams/READER_DELTA.md','pool-orderer-seams/REPORT.md','pool-orderer-seams/READER_DELTA.md']:
 reports.append({'path':str((wave/p).relative_to(root)),'sha256':sha((wave/p).read_bytes())})
lineage=json.loads((wave/'body-seams/SOURCE_LINEAGE_RECEIPT.json').read_text());tree=json.loads((root/'assets/review/commonware-reuse-20261004/wave11/execution-coverage/native-tree.json').read_text());idx={r['path']:r['sha'] for r in tree['tree'] if r['type']=='blob'};sources=[]
for r in lineage['sources']:
 b=(root/r['local']).read_bytes();assert sha(b)==r['sha256'] and blob(b)==idx[r['path']]==r['git_blob'];sources.append({'repo':lineage['repo'],'pin':lineage['pin'],'path':r['path'],'local':r['local'],'sha256':sha(b),'git_blob':blob(b),'tree_blob':idx[r['path']],'matched':True,'scope':'Retained primary bytes independently rehashed against own retained complete authenticated native tree, not new retrieval'})
nbase=root/'assets/review/commonware-reuse-20261004/wave11/execution-coverage/cross-review';ntree=json.loads((nbase/'nunchi-tree.json').read_text());nidx={r['path']:r['sha'] for r in ntree['tree'] if r['type']=='blob'}
for p in ['mempool/src/actor.rs','mempool/src/pool.rs']:
 local=nbase/'sources/nunchi'/p;b=local.read_bytes();assert blob(b)==nidx[p];sources.append({'repo':'nunchi-labs/sdk','pin':'eea35ced709f68c15d6fbc8bcc754696a7e44374','path':p,'local':str(local.relative_to(root)),'sha256':sha(b),'git_blob':blob(b),'tree_blob':nidx[p],'matched':True,'scope':'Prior own independently fetched and now reread/rehashed primary bytes; not new retrieval'})
paths=['docs/tx/README.md','docs/tx/interfaces.md','docs/overview/interfaces.md','docs/overview/architecture.md','docs/overview/rust-interfaces.md','docs/consensus/block-body.md','docs/consensus/ordered-input.md','docs/e2e/normal.md','docs/e2e/block-body.md','docs/e2e/canonical.md','docs/e2e/recovery.md'];pages=[]
for p in paths:
 b=(root/p).read_bytes();baseline=subprocess.check_output(['git','show','78d5f2eca347b0fc04b7f7d31ff858cc2a69bee4:'+p]);expected=baseline
 if p=='docs/tx/README.md':expected=baseline.replace(b'Nunchi supplies the queue/selection actor; TxPool connects its payload and canonical lifecycle to Baton.',b'Nunchi supplies the queue/selection actor; TxPool adds payload hooks and connects durable Executor outcomes to that actor.')
 if p=='docs/overview/interfaces.md':expected=baseline.replace(b'`Executor::Block` is assembled',b'`CommitResult` is passed by value: use concrete cloneable receipt handles or recover copies of the same immutable receipt for multiple consumers; type equality and `Send` do not duplicate an owned value.\n\n`Executor::Block` is assembled')
 assert b==expected,p;pages.append({'path':p,'sha256':sha(b),'baseline_equal':b==baseline,'exact_proposed_draft':b==expected})
(out/'CROSS_EVIDENCE.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':'78d5f2eca347b0fc04b7f7d31ff858cc2a69bee4','reports':reports,'pages':pages,'sources':sources,'fresh_downloads':0,'scope':'Independent source/doc seam review using retained blob-checked primary evidence; no canonical edits/compile/tests/protocol execution/default choices'},indent=2)+'\n');print(json.dumps({'reports':reports,'pages':len(pages),'retained_sources':len(sources),'fresh_downloads':0}))
