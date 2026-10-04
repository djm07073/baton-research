from pathlib import Path
import hashlib,json,urllib.request,datetime,re,subprocess
root=Path.cwd(); out=root/'assets/review/commonware-reuse-20261004/wave12/body-walkthrough/independent-cross-review';out.mkdir(exist_ok=True)
h=lambda b:hashlib.sha256(b).hexdigest()
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),'scope':'Independent source/document review, no compilation or implementation'}
reports=['pool-walkthrough/REPORT.md','pool-walkthrough/READER_DELTA.md','execution-walkthrough/REPORT.md','execution-walkthrough/READER_DELTA.md','ROOT_REVIEW.md']
record['reports']=[{'path':'assets/review/commonware-reuse-20261004/wave12/'+p,'sha256':h((root/'assets/review/commonware-reuse-20261004/wave12'/p).read_bytes())} for p in reports]
treepath=root/'assets/review/commonware-reuse-20261004/wave10/body-coherence/independent-cross-review/trees/constantinople.json';tree=json.loads(treepath.read_text());assert not tree['truncated'];index={e['path']:e['sha'] for e in tree['tree']}
record['constantinople_tree']={'path':str(treepath.relative_to(root)),'sha256':h(treepath.read_bytes()),'scope':'Own retained authenticated complete wave10 tree, not freshly fetched in wave12'}
record['fresh_sources']=[]
for p in ['crates/mempool/src/webserver/actor.rs','crates/mempool/src/webserver/mailbox.rs']:
 url='https://raw.githubusercontent.com/commonwarexyz/constantinople/3b6c92e76bf582855615844a4175b8304808f6a9/'+p
 b=urllib.request.urlopen(url).read();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert blob==index[p]
 dst=out/'sources'/p;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
 record['fresh_sources'].append({'repo':'commonwarexyz/constantinople','pin':'3b6c92e76bf582855615844a4175b8304808f6a9','path':p,'url':url,'sha256':h(b),'git_blob':blob,'tree_blob':index[p],'local':str(dst.relative_to(root))})
evidence=json.loads((root/'assets/review/commonware-reuse-20261004/wave12/execution-walkthrough/EVIDENCE.json').read_text())
record['retained_execution_sources']=[]
for e in evidence['sources']:
 b=(root/e['retained_source']).read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert blob==e['tree_blob'] and h(b)==e['sha256']
 record['retained_execution_sources'].append({'path':e['retained_source'],'sha256':h(b),'git_blob':blob,'scope':'Independently rehashed/reread retained pinned bytes, not new retrieval'})
record['execution_reader_receipt']=[]
for e in evidence['pages']:
 b=(root/e['path']).read_bytes();baseline=subprocess.check_output(['git','show','d4915b310c0fd071d6c49b12754fd556f6879981:'+e['path']]);assert h(baseline)==e['sha256'];record['execution_reader_receipt'].append({'path':e['path'],'report_baseline_sha256':e['sha256'],'current_sha256':h(b),'current_equal':b==baseline})
md=(root/'docs/overview/rust-interfaces.md').read_text();parts=re.findall(r'```rust\n(.*?)```',md,re.S);body='\n\n'.join(p.strip().removeprefix('use std::future::Future;\n\n') for p in parts)
expected='// @generated from docs/overview/rust-interfaces.md; edit that Markdown source.\n// Application interface proposals only; no protocol implementation.\n\nuse std::future::Future;\n\n'+body+'\n';export=(root/'docs/assets/interfaces/baton.rs').read_bytes();assert expected.encode()==export
record['current_export']={'sha256':h(export),'canonical_sha256':h(md.encode()),'matches':True,'traits':re.findall(r'^pub trait (\w+)',md,re.M)}
record['scope_of_current_diff']=subprocess.check_output(['git','diff','--','docs/overview/rust-interfaces.md','docs/assets/interfaces/baton.rs']).decode()
(out/'CROSS_REVIEW_RECEIPT.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'reports':record['reports'],'canonical':record['current_export'],'fresh_files':len(record['fresh_sources']),'retained_files':len(record['retained_execution_sources'])},indent=2))
