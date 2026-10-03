import json,urllib.request,hashlib,concurrent.futures,datetime,re
from pathlib import Path
out=Path(__file__).parent;wave=out.parent;targets=set()
for x in json.loads((wave/'order-evidence/source-manifest.json').read_text())['sources']:
 match=re.match(r'https://raw.githubusercontent.com/([^/]+/[^/]+)/([^/]+)/(.+)',x['url']);targets.add(tuple(match.groups()))
for x in json.loads((wave/'commit-metadata/source-manifest.json').read_text())['sources']:targets.add((x['repo'],x['pin'],x['path']))
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Baton-independent-cross-review'}),timeout=60).read()
trees={}
def tree(pair):
 repo,pin=pair
 f=out/'cross-sources'/(repo.replace('/','--')+'-tree.json');f.parent.mkdir(parents=True,exist_ok=True)
 try:
  d=json.loads(get(f'https://api.github.com/repos/{repo}/git/trees/{pin}?recursive=1'));provenance='fresh GitHub tree request'
 except Exception as e:
  candidates={'commonwarexyz/monorepo':out/'native-tree.json','commonwarexyz/constantinople':out/'constantinople-tree.json','commonwarexyz/alto':out/'alto-tree.json','refcell/kora':wave.parent/'wave5/branch-access/kora-tree.json','tempoxyz/tempo':wave.parent/'wave4/compatibility/tempo-tree.json'}
  cached=candidates[repo];d=json.loads(cached.read_text());provenance=f'Previously independently fetched pinned complete tree {cached}; current fresh tree HTTP failure: {e}'
 assert not d.get('truncated') and d['sha']==pin
 f.write_text(json.dumps(d,indent=2));(f.with_suffix('.receipt.txt')).write_text(provenance)
 return pair,{x['path']:x['sha'] for x in d['tree'] if x['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 for pair,t in pool.map(tree,sorted({(r,p) for r,p,s in targets})):trees[pair]=t
def fetch(x):
 repo,pin,path=x;u=f'https://raw.githubusercontent.com/{repo}/{pin}/{path}'
 try:
  b=get(u);f=out/'cross-sources'/repo.replace('/','--')/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();return {'repository':repo,'pin':pin,'path':path,'url':u,'local':str(f.relative_to(out)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'tree_blob':trees[(repo,pin)][path],'blob_matches':blob==trees[(repo,pin)][path],'fetched_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 except Exception as e:return {'repository':repo,'pin':pin,'path':path,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:rows=list(pool.map(fetch,sorted(targets)))
(out/'cross-review-source-manifest.json').write_text(json.dumps(rows,indent=2));print({'files':len(rows),'errors':[x for x in rows if 'error'in x],'mismatch':[x for x in rows if not x.get('blob_matches',True)]})
