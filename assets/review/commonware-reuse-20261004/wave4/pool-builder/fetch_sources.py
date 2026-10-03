import json,urllib.request,hashlib,concurrent.futures,datetime
from pathlib import Path
base=Path(__file__).parent
repos={
 'nunchi':('nunchi-labs/sdk','eea35ced709f68c15d6fbc8bcc754696a7e44374',['Cargo.toml','mempool/src/lib.rs','mempool/src/tx.rs','mempool/src/pool.rs','mempool/src/actor.rs','mempool/src/config.rs','mempool/src/status.rs','chain/src/application.rs','chain/src/execution.rs','common/src/transaction.rs']),
 'constantinople':('commonwarexyz/constantinople','3b6c92e76bf582855615844a4175b8304808f6a9',['Cargo.toml','crates/mempool/Cargo.toml','crates/mempool/src/lib.rs','crates/mempool/src/webserver/mailbox.rs','crates/mempool/src/webserver/actor.rs','crates/mempool/src/webserver/http.rs','crates/application/src/consensus/glue.rs','crates/application/src/consensus/lifecycle.rs','crates/primitives/src/transaction.rs']),
 'tempo':('tempoxyz/tempo','61c979a524f9af5de9c540a0088c429a44741e4c',['crates/node/src/node.rs','crates/transaction-pool/src/tempo_pool.rs','crates/transaction-pool/src/maintain.rs','crates/payload/builder/src/lib.rs','crates/consensus/src/consensus/application/impl.rs']),
 'reth':('paradigmxyz/reth','038edab20dfff017f7a7502e683c732e5628ad89',['crates/transaction-pool/src/traits.rs','crates/transaction-pool/src/pool/mod.rs','crates/transaction-pool/src/maintain.rs','crates/transaction-pool/src/lib.rs','crates/net/network/src/transactions/mod.rs']),
 'native':('commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72',['consensus/src/lib.rs','consensus/src/multimmit/actors/voter/executor.rs','consensus/src/multimmit/types/block.rs','broadcast/src/buffered/ingress.rs'])}
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Baton-source-audit'}),timeout=90) as r:return r.read()
def tree(job):
 tag,(repo,pin,paths)=job;url=f'https://api.github.com/repos/{repo}/git/trees/{pin}?recursive=1';b=get(url); (base/f'{tag}-tree.json').write_bytes(b);t=json.loads(b);assert not t.get('truncated');return tag,{e['path']:e['sha'] for e in t['tree'] if e['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex: trees=dict(ex.map(tree,repos.items()))
def fetch(job):
 tag,path=job;repo,pin,_=repos[tag];url=f'https://raw.githubusercontent.com/{repo}/{pin}/{path}';b=get(url);p=base/'sources'/tag/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);blob=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest();expected=trees[tag][path];assert blob==expected
 return {'repo':repo,'pin':pin,'path':path,'url':url,'local':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'tree_blob':expected,'git_blob_verified':True}
jobs=[(tag,p) for tag,(_,_,ps) in repos.items() for p in ps]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:sources=list(ex.map(fetch,jobs))
(base/'source-manifest.json').write_text(json.dumps({'fetched_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':sources},indent=2)+'\n');print(f'Freshly fetched {len(sources)} files; all Git blobs match pinned trees.')
