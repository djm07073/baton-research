from pathlib import Path
import json,subprocess,urllib.request,hashlib,concurrent.futures,datetime
p=Path(__file__).parent
src={}
for name in ['delivery-ack','body-receive']:
 for r in json.loads((p.parent/name/'source-manifest.json').read_text())['sources']:
  repo=r['repository'];pin=r.get('pin',r.get('revision'));path=r['path'];src[(repo,pin,path)]={'repo':repo,'pin':pin,'path':path}
keys=set((r['repo'],r['pin']) for r in src.values());tags={('commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72'):'native',('commonwarexyz/monorepo','d476a2361ce6840d2b9d0aa6fb30a924429046d4'):'release',('tempoxyz/tempo','61c979a524f9af5de9c540a0088c429a44741e4c'):'tempo',('commonwarexyz/alto','1d87569348b5560699465a72d691d90f18affb9c'):'alto'}
def tree(x):
 repo,pin=x;tag=tags[x];t=json.loads(subprocess.run(['gh','api','--method','GET',f'repos/{repo}/git/trees/{pin}','-f','recursive=1'],check=True,capture_output=True,text=True).stdout);assert t['sha']==pin and not t['truncated'];(p/f'cross-review-{tag}-tree.json').write_text(json.dumps(t,indent=2));return x,{r['path']:r['sha'] for r in t['tree'] if r['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:trees=dict(ex.map(tree,keys))
def fetch(r):
 repo,pin,path=r['repo'],r['pin'],r['path'];tag=tags[(repo,pin)];url=f'https://raw.githubusercontent.com/{repo}/{pin}/{path}';b=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Baton-independent-cross-review'}),timeout=60).read();f=p/'cross-review-sources'/tag/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert blob==trees[(repo,pin)][path];return {**r,'url':url,'local':str(f.relative_to(p)),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'tree_blob':trees[(repo,pin)][path],'blob_verified':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:rows=list(ex.map(fetch,src.values()))
(p/'cross-review-source-manifest.json').write_text(json.dumps(rows,indent=2));print({'fresh_files':len(rows),'trees':len(keys),'all_blobs_match':True})
