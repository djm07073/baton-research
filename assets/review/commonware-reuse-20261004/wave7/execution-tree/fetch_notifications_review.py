from pathlib import Path
import json,urllib.request,hashlib,concurrent.futures,datetime,subprocess
out=Path(__file__).parent
rows=json.loads((out.parent/'notifications/source-manifest.json').read_text())['sources']
keys=set((x['tag'],x['repo'],x['pin']) for x in rows)
def tree(k):
 tag,repo,pin=k;v=json.loads(subprocess.run(['gh','api','--method','GET',f'repos/{repo}/git/trees/{pin}','-f','recursive=1'],capture_output=True,text=True,check=True).stdout);assert v['sha']==pin and not v['truncated'];f=out/f'notifications-review-{tag}-tree.json';f.write_text(json.dumps(v,indent=2));return tag,{x['path']:x['sha'] for x in v['tree'] if x['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:trees=dict(p.map(tree,keys))
def fetch(r):
 b=urllib.request.urlopen(urllib.request.Request(r['url'],headers={'User-Agent':'Baton-independent-review'}),timeout=60).read();f=out/'notifications-review-sources'/r['tag']/r['path'];f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert blob==trees[r['tag']][r['path']];return {'repo':r['repo'],'pin':r['pin'],'path':r['path'],'url':r['url'],'local':str(f.relative_to(out)),'git_blob':blob,'tree_blob':trees[r['tag']][r['path']],'sha256':hashlib.sha256(b).hexdigest(),'fetched_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'blob_verified':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as p:new=list(p.map(fetch,rows))
(out/'notifications-review-source-manifest.json').write_text(json.dumps(new,indent=2));print({'fresh':len(new),'all_blob_verified':True})
