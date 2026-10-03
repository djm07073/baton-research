import json,urllib.request,hashlib,concurrent.futures,datetime
from pathlib import Path
base=Path(__file__).parent;orig=base.parent/'body-storage';m=json.loads((orig/'source-manifest.json').read_text());pins=m['pins'];choose={
'native':['storage/src/archive/mod.rs','storage/src/archive/immutable/mod.rs','storage/src/archive/immutable/storage.rs','storage/src/archive/prunable/mod.rs','storage/src/archive/prunable/storage.rs','storage/src/freezer/mod.rs','storage/src/freezer/storage.rs','consensus/src/marshal/store.rs','consensus/src/marshal/core/mailbox.rs','consensus/src/marshal/resolver/handler.rs','resolver/src/lib.rs','resolver/src/p2p/mod.rs','resolver/src/p2p/engine.rs','resolver/src/p2p/wire.rs','utils/src/sequence/mod.rs','codec/src/codec.rs','consensus/src/multimmit/types/block.rs','consensus/src/marshal/core/actor.rs','consensus/src/lib.rs'],
' tempo':[],
'alto':['follower/src/archive.rs','follower/src/engine.rs','chain/src/engine.rs'],
'release':['consensus/src/marshal/core/actor.rs','consensus/src/marshal/store.rs','consensus/src/marshal/resolver/handler.rs']}
choose['tempo']=['crates/consensus/src/storage/hybrid/mod.rs','crates/consensus/src/storage/mod.rs','crates/consensus/src/alias.rs']
def get(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Baton-independent-body-review'}),timeout=90) as r:return r.read()
used={tag for tag,ps in choose.items() if ps}
def tree(tag):
 repo,pin=pins[tag];b=get(f'https://api.github.com/repos/{repo}/git/trees/{pin}?recursive=1');t=json.loads(b);assert not t.get('truncated');f=base/'body-review-sources'/f'{tag}-tree.json';f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);return tag,{x['path']:x['sha'] for x in t['tree'] if x['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:trees=dict(ex.map(tree,used))
def fetch(j):
 tag,path=j;repo,pin=pins[tag];u=f'https://raw.githubusercontent.com/{repo}/{pin}/{path}';b=get(u);f=base/'body-review-sources'/tag/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);blob=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest();assert blob==trees[tag][path];return {'repo':repo,'pin':pin,'path':path,'url':u,'local':str(f),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'tree_blob':trees[tag][path],'git_blob_verified':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:rows=list(ex.map(fetch,[(tag,path) for tag,ps in choose.items() for path in ps]))
(base/'body-review-receipts.json').write_text(json.dumps({'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':rows},indent=2)+'\n');print('fresh decisive files',len(rows),'all pinned blobs matched')
