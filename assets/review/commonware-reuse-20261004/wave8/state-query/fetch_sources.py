from pathlib import Path
import json,urllib.request,concurrent.futures,hashlib,datetime
p=Path(__file__).parent
spec={'native':('commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72',['storage/src/qmdb/mod.rs','storage/src/qmdb/any/db.rs','storage/src/qmdb/current/db.rs','storage/src/qmdb/current/proof/mod.rs','storage/src/qmdb/current/ordered/db.rs','storage/src/qmdb/current/unordered/db.rs','storage/src/qmdb/current/ordered/mod.rs','storage/src/qmdb/current/unordered/mod.rs','storage/src/qmdb/any/ordered/mod.rs','storage/src/qmdb/any/unordered/mod.rs','storage/src/qmdb/any/batch.rs','storage/src/qmdb/current/batch.rs','glue/src/stateful/db/mod.rs','glue/src/stateful/db/any.rs','glue/src/stateful/db/current.rs','storage/src/merkle/proof.rs']), 'constantinople':('commonwarexyz/constantinople','3b6c92e76bf582855615844a4175b8304808f6a9',['crates/mempool/src/webserver/account_reader.rs','crates/mempool/src/webserver/http.rs','crates/mempool/src/webserver/actor.rs','crates/mempool/src/webserver/mailbox.rs','crates/application/src/consensus/db.rs','crates/application/src/consensus/glue.rs','bin/validator/src/state_reader.rs','bin/validator/src/run.rs','crates/engine/src/types.rs','crates/indexer/src/publisher/qmdb.rs','crates/indexer/src/publisher/block.rs'])}
spec['release']=('commonwarexyz/monorepo','d476a2361ce6840d2b9d0aa6fb30a924429046d4',['storage/src/qmdb/current/unordered/db.rs','storage/src/qmdb/current/ordered/db.rs','storage/src/qmdb/current/proof/mod.rs'])
# Exact complete tree is authoritative for pin and file presence.
for tag in spec:
 repo,pin,paths=spec[tag];tree=json.loads((p/(tag+'-tree.json')).read_text());spec[tag]=(repo,tree['sha'],paths)
trees={tag:{x['path']:x['sha'] for x in json.loads((p/(tag+'-tree.json')).read_text())['tree'] if x['type']=='blob'} for tag in spec}
def fetch(x):
 tag,path=x;repo,pin,_=spec[tag];u=f'https://raw.githubusercontent.com/{repo}/{pin}/{path}'
 if path not in trees[tag]:return {'tag':tag,'repo':repo,'pin':pin,'path':path,'tree_path_present':False}
 b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Baton-state-query-review'}),timeout=60).read();f=p/'sources'/tag/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert blob==trees[tag][path];return {'tag':tag,'repo':repo,'pin':pin,'path':path,'url':u,'local':str(f.relative_to(p)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'tree_blob':trees[tag][path],'blob_verified':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:rows=list(ex.map(fetch,[(tag,path) for tag,(_,_,paths) in spec.items() for path in paths]))
(p/'source-manifest.json').write_text(json.dumps(rows,indent=2));print({'files':len(rows),'missing':[x for x in rows if not x.get('blob_verified')]})
