from pathlib import Path
import hashlib,json,subprocess,urllib.request,concurrent.futures,datetime
r=Path(__file__).parent
pins={'native':('commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72'),'tempo':('tempoxyz/tempo','61c979a524f9af5de9c540a0088c429a44741e4c')}
paths={'native':['consensus/src/multimmit/engine.rs','p2p/src/authenticated/discovery/network.rs','p2p/src/authenticated/router/ingress.rs','storage/src/archive/mod.rs'],'tempo':['crates/consensus/src/storage/hybrid/mod.rs']}
trees={}
for k,(repo,pin) in pins.items():
 b=subprocess.check_output(['gh','api',f'repos/{repo}/git/trees/{pin}?recursive=1'])
 d=json.loads(b);assert not d.get('truncated'),k
 (r/'trees').mkdir(exist_ok=True)
 (r/'trees'/f'{k}.json').write_bytes(b)
 trees[k]={x['path']:x for x in d['tree']}
def get(item):
 k,p=item;repo,pin=pins[k];url=f'https://raw.githubusercontent.com/{repo}/{pin}/{p}'
 b=urllib.request.urlopen(url,timeout=60).read()
 blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert blob==trees[k][p]['sha'],(k,p)
 f=r/'sources'/k/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
 return {'kind':k,'repository':repo,'revision':pin,'path':p,'url':url,'sha256':hashlib.sha256(b).hexdigest(),'git_blob_sha1':blob,'bytes':len(b),'lines':len(b.splitlines()),'status':'fresh-own-wave11-complete-tree-blob-matched'}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(get,[(k,p) for k,ps in paths.items() for p in ps]))
out={'reviewer':'/root/reuse_network_v3','fetched_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fresh_complete_trees':len(trees),'sources':rows,'tree_receipts':[{'kind':k,'sha256':hashlib.sha256((r/'trees'/f'{k}.json').read_bytes()).hexdigest(),'entries':len(t)} for k,t in trees.items()]}
(r/'source-manifest.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'fresh_files':len(rows),'trees':len(trees),'all_blob_matched':True}))
