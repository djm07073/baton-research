import json,urllib.request,hashlib,concurrent.futures,datetime,tomllib
from pathlib import Path
base=Path(__file__).parent;c=base.parent/'compatibility';m=json.loads((c/'source-manifest.json').read_text())['receipts']
chosen={'native':{'Cargo.toml','resolver/src/p2p/config.rs','p2p/src/lib.rs'},'release':{'Cargo.toml','resolver/src/p2p/config.rs','p2p/src/lib.rs','consensus/src/lib.rs'},'nunchi':{'Cargo.toml','Cargo.lock','mempool/Cargo.toml','common/Cargo.toml','crypto/Cargo.toml','mempool/src/tx.rs','mempool/src/actor.rs'},'tempo':{'Cargo.lock'},'alto':{'Cargo.lock'}}
def get(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Baton-independent-cross-review'}),timeout=90) as r:return r.read()
jobs=[x for x in m if x.get('status')==200 and x['path'] in chosen.get(x['label'],set())]
unique={(x['repository'],x['revision']) for x in jobs}
def tree(j):
 repo,pin=j;u=f'https://api.github.com/repos/{repo}/git/trees/{pin}?recursive=1';b=get(u);t=json.loads(b);assert not t.get('truncated');p=base/'compatibility-sources'/(repo.replace('/','-')+'-'+pin+'-tree.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);return j,{x['path']:x['sha'] for x in t['tree'] if x['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:trees=dict(ex.map(tree,unique))
def fetch(x):
 b=get(x['url']);p=base/'compatibility-sources'/x['label']/x['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);blob=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest();assert blob==trees[(x['repository'],x['revision'])][x['path']]==x['git_blob'];return {'label':x['label'],'repo':x['repository'],'pin':x['revision'],'path':x['path'],'url':x['url'],'local':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'matches_fresh_tree_and_review_manifest':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:rows=list(ex.map(fetch,jobs))
(base/'compatibility-source-manifest.json').write_text(json.dumps({'fetched_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'receipts':rows},indent=2)+'\n')
for label in ['nunchi','tempo','alto']:
 p=base/'compatibility-sources'/label/'Cargo.lock';a=tomllib.loads(p.read_text())['package'];cw=[x for x in a if x['name'].startswith('commonware-')];print(label,len(cw),sorted({(x['version'],x.get('source')) for x in cw}))
print('fresh files',len(rows),'all Git blobs matched')
