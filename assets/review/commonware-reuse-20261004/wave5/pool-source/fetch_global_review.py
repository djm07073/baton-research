import json,urllib.request,hashlib,concurrent.futures,datetime
from pathlib import Path
base=Path(__file__).parent;pins={'native':['commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72'],'kora':['refcell/kora','446b4c7aba80e8358486ddb43a276c5bfa183102'],'constantinople':['commonwarexyz/constantinople','3b6c92e76bf582855615844a4175b8304808f6a9']};choose={'native':['parallel/src/lib.rs','utils/src/futures.rs','macros/src/lib.rs','macros/impl/src/lib.rs','runtime/src/lib.rs','runtime/src/tokio/runtime.rs','runtime/src/utils/handle.rs','glue/src/stateful/db/any.rs','storage/src/qmdb/any/batch.rs','storage/src/qmdb/batch_chain.rs'],'kora':['crates/storage/qmdb/src/store.rs'],'constantinople':['crates/application/src/consensus/execution.rs','crates/application/src/consensus/db.rs']}
def get(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Baton-independent-global-reader-review'}),timeout=90) as r:return r.read()
def tree(tag):
 repo,pin=pins[tag];b=get(f'https://api.github.com/repos/{repo}/git/trees/{pin}?recursive=1');t=json.loads(b);assert not t.get('truncated');f=base/'global-review-sources'/f'{tag}-tree.json';f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);return tag,{x['path']:x['sha'] for x in t['tree'] if x['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:trees=dict(ex.map(tree,pins))
def fetch(j):
 tag,path=j;repo,pin=pins[tag];u=f'https://raw.githubusercontent.com/{repo}/{pin}/{path}';b=get(u);f=base/'global-review-sources'/tag/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);blob=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest();assert blob==trees[tag][path];return {'repo':repo,'pin':pin,'path':path,'url':u,'local':str(f),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'tree_blob':trees[tag][path],'git_blob_verified':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:rows=list(ex.map(fetch,[(tag,path) for tag,ps in choose.items() for path in ps]))
(base/'global-review-source-receipts.json').write_text(json.dumps({'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':rows},indent=2)+'\n');print('fresh global sources',len(rows),'all pinned blobs matched')
