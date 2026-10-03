from pathlib import Path
import re,json,urllib.request,hashlib,subprocess,datetime,concurrent.futures
b=Path(__file__).parent;w=b.parent;reports=['simulated-network','storage-fixtures','fixture-boundaries'];refs=[]
for name in reports:
 for repo,pin,path,line in re.findall(r'https://github.com/([^/]+/[^/]+)/blob/([0-9a-f]{40})/([^\s)#]+)#L(\d+)',(w/name/'REPORT.md').read_text()):refs.append((name,repo,pin,path,int(line)))
keys=sorted(set((r,p) for _,r,p,_,_ in refs));out=b/'independent-cross-review';out.mkdir(exist_ok=True)
def tree(k):
 r,p=k;v=subprocess.check_output(['gh','api',f'repos/{r}/git/trees/{p}?recursive=1']);t=json.loads(v);assert not t.get('truncated');f=out/(r.replace('/','__')+'__'+p+'-tree.json');f.write_bytes(v);return k,{x['path']:x['sha'] for x in t['tree'] if x['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:trees=dict(e.map(tree,keys))
def fetch(k):
 r,p,path=k;u=f'https://raw.githubusercontent.com/{r}/{p}/{path}';v=urllib.request.urlopen(u,timeout=45).read();f=out/'sources'/r/p/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(v);blob=hashlib.sha1(f'blob {len(v)}\0'.encode()+v).hexdigest();assert blob==trees[(r,p)][path];return {'repo':r,'pin':p,'path':path,'local':str(f.resolve()),'url':u,'sha256':hashlib.sha256(v).hexdigest(),'git_blob':blob,'tree_blob':trees[(r,p)][path],'bytes':len(v)}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as e:rows=list(e.map(fetch,sorted(set((r,p,path) for _,r,p,path,_ in refs))))
indexed={(r['repo'],r['pin'],r['path']):r for r in rows};anchors=[]
for name,r,p,path,line in refs:
 ls=Path(indexed[(r,p,path)]['local']).read_text().splitlines();assert 1<=line<=len(ls);anchors.append({'report':name,'repo':r,'pin':p,'path':path,'line':line,'line_text':ls[line-1]})
m={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'trees':len(trees),'sources':rows,'anchors':anchors,'report_hashes':{name:hashlib.sha256((w/name/'REPORT.md').read_bytes()).hexdigest() for name in reports},'reader_delta_hashes':{name:hashlib.sha256((w/name/'READER_DELTA.md').read_bytes()).hexdigest() for name in reports if (w/name/'READER_DELTA.md').exists()}}
(out/'source-manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(len(rows),'fresh matched blobs;',len(trees),'complete trees;',len(anchors),'anchors');print(m['report_hashes'])
