from pathlib import Path
import urllib.request,hashlib,json,concurrent.futures,datetime,re
base=Path(__file__).parent/'result-cross-review';base.mkdir(parents=True,exist_ok=True);report=Path(__file__).parent.parent/'result-transport'/'REPORT.md';m=json.loads((report.parent/'source-manifest.json').read_text());ps={x['revision'] for x in m['sources']};repo='commonwarexyz/monorepo'
def get(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Baton-independent-result-audit'}),timeout=60) as r:return r.read()
def tree(pin):
 b=get(f'https://api.github.com/repos/{repo}/git/trees/{pin}?recursive=1');t=json.loads(b);assert not t.get('truncated');(base/(pin+'-tree.json')).write_bytes(b);return pin,{x['path']:x['sha'] for x in t['tree'] if x['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as e:trees=dict(e.map(tree,ps))
def fetch(x):
 pin=x['revision'];p=x['path'];u=f'https://raw.githubusercontent.com/{repo}/{pin}/{p}';b=get(u);f=base/'sources'/pin/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);blob=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest();assert blob==trees[pin][p];return {'repo':repo,'pin':pin,'path':p,'url':u,'local':str(f.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'tree_blob':trees[pin][p],'blob_verified':True,'matches_report_manifest':hashlib.sha256(b).hexdigest()==x['sha256']}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as e:rows=list(e.map(fetch,m['sources']))
assert all(x['matches_report_manifest'] for x in rows);reportbytes=report.read_bytes();s={(x['repo'],x['pin'],x['path']):x for x in rows};anchors=[]
for r,p,path,n in re.findall(r'https://github.com/([^/]+/[^/]+)/blob/([^/]+)/([^\s)#]+)#L(\d+)',reportbytes.decode()):
 x=s[(r,p,path)];ls=Path(x['local']).read_text().splitlines();assert int(n)<=len(ls);anchors.append({'repo':r,'pin':p,'path':path,'line':int(n),'anchor_text':ls[int(n)-1]})
(base/'source-manifest.json').write_text(json.dumps({'fresh_fetched_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'report_sha256':hashlib.sha256(reportbytes).hexdigest(),'sources':rows,'anchors':anchors},indent=2)+'\n');print('Fresh independent',len(rows),'files,',len(trees),'complete trees,',len(anchors),'anchors; all blobs and report manifest hashes match')
