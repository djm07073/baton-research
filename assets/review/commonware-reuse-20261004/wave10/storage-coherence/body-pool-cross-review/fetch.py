from pathlib import Path
import subprocess,json,urllib.request,hashlib,datetime,concurrent.futures
p=Path(__file__).parent
spec={'native':('commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72',['broadcast/src/buffered/ingress.rs','broadcast/src/buffered/engine.rs','consensus/src/marshal/mod.rs','resolver/src/p2p/engine.rs']), 'release':('commonwarexyz/monorepo','d476a2361ce6840d2b9d0aa6fb30a924429046d4',['consensus/src/marshal/standard/relay.rs','consensus/src/marshal/core/actor.rs','consensus/src/marshal/standard/variant.rs']), 'nunchi':('nunchi-labs/sdk','eea35ced709f68c15d6fbc8bcc754696a7e44374',['mempool/src/actor.rs','mempool/src/pool.rs']), 'tempo':('tempoxyz/tempo','61c979a524f9af5de9c540a0088c429a44741e4c',['crates/consensus/src/consensus/engine.rs'])}
def tree(tag):
 repo,pin,_=spec[tag];b=subprocess.check_output(['gh','api','--method','GET',f'repos/{repo}/git/trees/{pin}','-f','recursive=1']);t=json.loads(b);assert t['sha']==pin and not t['truncated'];(p/(tag+'-tree.json')).write_bytes(b);return tag,{x['path']:x['sha'] for x in t['tree'] if x['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:trees=dict(ex.map(tree,spec))
def fetch(item):
 tag,path=item;repo,pin,_=spec[tag];u=f'https://raw.githubusercontent.com/{repo}/{pin}/{path}';b=urllib.request.urlopen(u,timeout=60).read();f=p/'sources'/tag/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);g=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert g==trees[tag][path];return {'tag':tag,'repo':repo,'pin':pin,'path':path,'url':u,'local':str(f.relative_to(p)),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':g,'tree_blob':trees[tag][path],'blob_verified':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:rows=list(ex.map(fetch,[(tag,path) for tag,(_,_,paths) in spec.items() for path in paths]))
(p/'source-manifest.json').write_text(json.dumps(rows,indent=2));root=p.parents[1];h={}
for name in ['pool-coherence','body-coherence','intro-coherence']:
 b=(root/name/'REPORT.md').read_bytes();(p/(name+'-REPORT.md')).write_bytes(b);h[name]=hashlib.sha256(b).hexdigest()
(p/'report-hashes.json').write_text(json.dumps(h,indent=2));print({'fresh_files':len(rows),'hashes':h})
