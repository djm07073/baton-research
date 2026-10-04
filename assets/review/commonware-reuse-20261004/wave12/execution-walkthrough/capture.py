from pathlib import Path
import json,hashlib,subprocess,datetime,re
root=Path.cwd(); out=root/'assets/review/commonware-reuse-20261004/wave12/execution-walkthrough';sha=lambda b:hashlib.sha256(b).hexdigest();blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
pages=['docs/overview/interfaces.md','docs/overview/rust-interfaces.md','docs/execution/README.md','docs/execution/interfaces.md','docs/execution/qmdb.md','docs/execution/state-sync.md','docs/e2e/canonical.md','docs/e2e/results.md','docs/e2e/state-sync.md','docs/e2e/recovery.md','docs/consensus/ordered-input.md','docs/reference/integration.md','docs/reference/verification.md']
receipt=[]
for p in pages:
 b=(root/p).read_bytes();base=subprocess.check_output(['git','show','d4915b310c0fd071d6c49b12754fd556f6879981:'+p]);assert b==base
 receipt.append({'path':p,'sha256':sha(b),'baseline_equal':True})
prev=root/'assets/review/commonware-reuse-20261004/wave11/execution-coverage';manifest=json.loads((prev/'source-manifest.json').read_text());tree=json.loads((prev/'native-tree.json').read_text());index={r['path']:r['sha'] for r in tree['tree'] if r['type']=='blob'}
wanted=['glue/src/stateful/db/mod.rs','glue/src/stateful/db/any.rs','storage/src/qmdb/any/batch.rs','storage/src/qmdb/sync/mod.rs','storage/src/qmdb/sync/engine.rs'];sources=[]
for p in wanted:
 row=next(v for v in manifest if v['path']==p);src=prev/row['local'];b=src.read_bytes();assert row['sha256']==sha(b) and row['git_blob']==blob(b)==index[p]
 sources.append({'repo':row['repo'],'pin':row['pin'],'path':p,'retained_source':str(src.relative_to(root)),'sha256':sha(b),'git_blob':blob(b),'tree_blob':index[p],'matched':True,'original_fetch_utc':row['utc'],'scope':'Prior wave11 independently fresh primary source bytes rehashed and reread for decisive actual API boundaries; not a new download'})
rust=(root/'docs/overview/rust-interfaces.md').read_text();blocks=re.findall(r'```rust\n([\s\S]*?)\n```',rust);body='\n\n'.join(re.sub(r'^use std::future::Future;\n\n','',s) for s in blocks);expected='// @generated from docs/overview/rust-interfaces.md; edit that Markdown source.\n// Application interface proposals only; no protocol implementation.\n\nuse std::future::Future;\n\n'+body+'\n';export=(root/'docs/assets/interfaces/baton.rs').read_bytes();assert expected.encode()==export
(out/'EVIDENCE.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':'d4915b310c0fd071d6c49b12754fd556f6879981','current_head':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),'pages':receipt,'sources':sources,'rust_export_sha256':sha(export),'rust_export_matches':True,'public_traits':re.findall(r'pub trait (\w+)',rust),'scope':'Adversarial source/document walkthrough, no compile/build/E2E/protocol execution or new dependency decisions'},indent=2)+'\n')
print(json.dumps({'pages':len(receipt),'decisive_retained_sources':len(sources),'public_traits':re.findall(r'pub trait (\w+)',rust),'all_match':True}))
