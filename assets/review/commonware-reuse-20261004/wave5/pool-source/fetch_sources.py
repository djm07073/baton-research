import json,urllib.request,hashlib,concurrent.futures,datetime
from pathlib import Path
base=Path(__file__).parent
repos={
'nunchi':('nunchi-labs/sdk','eea35ced709f68c15d6fbc8bcc754696a7e44374',['Cargo.toml','mempool/Cargo.toml','mempool/src/lib.rs','mempool/src/actor.rs','mempool/src/tx.rs','mempool/src/pool.rs','mempool/src/config.rs','mempool/src/status.rs','mempool/src/error.rs','mempool/src/metrics.rs','common/Cargo.toml','common/src/lib.rs','common/src/transaction.rs','common/src/module.rs','crypto/Cargo.toml','crypto/src/lib.rs']),
'native':('commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72',['Cargo.toml','macros/src/lib.rs','runtime/src/lib.rs','p2p/src/lib.rs','codec/src/codec.rs','cryptography/src/sha256/mod.rs','consensus/src/multimmit/actors/voter/executor.rs'])}
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Baton-pool-source-audit'}),timeout=90) as r:return r.read()
def tree(j):
 tag,(repo,pin,ps)=j;b=get(f'https://api.github.com/repos/{repo}/git/trees/{pin}?recursive=1');(base/f'{tag}-tree.json').write_bytes(b);t=json.loads(b);assert not t.get('truncated');return tag,{x['path']:x['sha'] for x in t['tree'] if x['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:trees=dict(ex.map(tree,repos.items()))
jobs=[(tag,p) for tag,(_,_,ps) in repos.items() for p in ps]
def fetch(j):
 tag,path=j;repo,pin,_=repos[tag];url=f'https://raw.githubusercontent.com/{repo}/{pin}/{path}'
 try:b=get(url)
 except Exception as e:return {'repo':repo,'pin':pin,'path':path,'url':url,'failure':str(e)}
 p=base/'sources'/tag/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);blob=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest();assert blob==trees[tag][path];return {'repo':repo,'pin':pin,'path':path,'url':url,'local':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'tree_blob':trees[tag][path],'git_blob_verified':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:rows=list(ex.map(fetch,jobs))
(base/'source-manifest.json').write_text(json.dumps({'fetched_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':rows},indent=2)+'\n');print('successful',sum('failure' not in x for x in rows),'failures',[x for x in rows if 'failure' in x])
