from pathlib import Path
import hashlib,json,subprocess,urllib.request,concurrent.futures,datetime
r=Path(__file__).parent/'independent-cross-review';r.mkdir(exist_ok=True)
pins={'native':('commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72'),'nunchi':('nunchi-labs/sdk','eea35ced709f68c15d6fbc8bcc754696a7e44374'),'reth':('paradigmxyz/reth','038edab20dfff017f7a7502e683c732e5628ad89'),'constantinople':('commonwarexyz/constantinople','3b6c92e76bf582855615844a4175b8304808f6a9')}
paths={'native':['glue/src/stateful/db/mod.rs','glue/src/stateful/db/any.rs','storage/src/qmdb/any/batch.rs'],'nunchi':['mempool/src/actor.rs','mempool/src/pool.rs','mempool/src/lib.rs'],'reth':['crates/transaction-pool/src/traits.rs','crates/transaction-pool/src/pool/best.rs'],'constantinople':['crates/mempool/src/webserver/mailbox.rs','crates/mempool/src/webserver/actor.rs']}
trees={}
for k,(repo,pin) in pins.items():
 b=subprocess.check_output(['gh','api',f'repos/{repo}/git/trees/{pin}?recursive=1']);d=json.loads(b);assert not d.get('truncated'),k
 (r/'trees').mkdir(exist_ok=True);(r/'trees'/f'{k}.json').write_bytes(b);trees[k]={x['path']:x for x in d['tree']}
def get(item):
 k,p=item;repo,pin=pins[k];url=f'https://raw.githubusercontent.com/{repo}/{pin}/{p}';b=urllib.request.urlopen(url,timeout=60).read()
 blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert blob==trees[k][p]['sha'],(k,p)
 f=r/'sources'/k/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
 return {'kind':k,'repository':repo,'revision':pin,'path':p,'url':url,'sha256':hashlib.sha256(b).hexdigest(),'git_blob_sha1':blob,'bytes':len(b),'lines':len(b.splitlines()),'status':'fresh-independent-wave10-tree-blob-matched'}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(get,[(k,p) for k,ps in paths.items() for p in ps]))
out={'reviewer':'/root/reuse_network_v3','fetched_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fresh_complete_trees':len(trees),'sources':rows,'tree_receipts':[{'kind':k,'sha256':hashlib.sha256((r/'trees'/f'{k}.json').read_bytes()).hexdigest(),'entries':len(t)} for k,t in trees.items()]}
(r/'source-manifest.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'files':len(rows),'trees':len(trees),'all_blobs_matched':True}))
