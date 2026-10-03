from pathlib import Path
import json,urllib.request,hashlib,subprocess,re,concurrent.futures,datetime
b=Path(__file__).parent/'global-cross-review';b.mkdir(parents=True,exist_ok=True);pages=['docs/consensus/block-body.md','docs/consensus/ordered-input.md','docs/e2e/recovery.md','docs/execution/interfaces.md','docs/execution/qmdb.md','docs/execution/state-sync.md','docs/overview/architecture.md','docs/reference/integration.md'];d=subprocess.check_output(['git','diff','8b61492','--',*pages],text=True);added='\n'.join(l[1:] for l in d.splitlines() if l.startswith('+') and not l.startswith('+++'));refs=re.findall(r'https://github.com/([^/]+/[^/]+)/blob/([^/]+)/([^\s)#]+)(?:#L(\d+))?',added);ps={(r,p,path) for r,p,path,n in refs};pin='61c979a524f9af5de9c540a0088c429a44741e4c';ps.update({('tempoxyz/tempo',pin,p) for p in ['crates/consensus/src/consensus/engine.rs','crates/consensus/src/alias.rs','Cargo.lock']});repos={(r,p) for r,p,path in ps}
def get(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Baton-final-reader-independent-audit'}),timeout=60) as r:return r.read()
def tree(x):
 r,p=x;v=subprocess.check_output(['gh','api',f'repos/{r}/git/trees/{p}?recursive=1']);t=json.loads(v);assert not t.get('truncated');(b/(r.replace('/','--')+'-'+p+'-tree.json')).write_bytes(v);return x,{a['path']:a['sha'] for a in t['tree'] if a['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as e:trees=dict(e.map(tree,repos))
def fetch(x):
 r,p,path=x;u=f'https://raw.githubusercontent.com/{r}/{p}/{path}';v=get(u);f=b/'sources'/r.replace('/','--')/p/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(v);blob=hashlib.sha1(f'blob {len(v)}\0'.encode()+v).hexdigest();assert blob==trees[(r,p)][path];return {'repo':r,'pin':p,'path':path,'url':u,'local':str(f.resolve()),'sha256':hashlib.sha256(v).hexdigest(),'git_blob':blob,'tree_blob':trees[(r,p)][path],'bytes':len(v),'blob_verified':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as e:rows=list(e.map(fetch,sorted(ps)))
s={(x['repo'],x['pin'],x['path']):x for x in rows};anchors=[]
for r,p,path,n in refs:
 if n:ls=Path(s[(r,p,path)]['local']).read_text().splitlines();assert int(n)<=len(ls);anchors.append({'repo':r,'pin':p,'path':path,'line':int(n),'text':ls[int(n)-1]})
(b/'source-manifest.json').write_text(json.dumps({'fresh_fetched_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':'8b61492','sources':rows,'new_citation_anchors':anchors},indent=2)+'\n');print('Fresh',len(rows),'files,',len(trees),'complete trees,',len(anchors),'added anchors; all blobs match')
