from pathlib import Path
import json,subprocess,urllib.request,hashlib,datetime,re,concurrent.futures
p=Path(__file__).parent
root=p.parents[1]
reports={x:root/x/'REPORT.md' for x in ['simulated-network','native-fixtures','fixture-boundaries']}
pins={'native':('commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72'),'release':('commonwarexyz/monorepo','d476a2361ce6840d2b9d0aa6fb30a924429046d4'),'tempo':('tempoxyz/tempo','61c979a524f9af5de9c540a0088c429a44741e4c'),'alto':('commonwarexyz/alto','1d87569348b5560699465a72d691d90f18affb9c')}
def tree(tag):
 repo,pin=pins[tag];b=subprocess.check_output(['gh','api','--method','GET',f'repos/{repo}/git/trees/{pin}','-f','recursive=1']);t=json.loads(b);assert t['sha']==pin and not t['truncated'];(p/(tag+'-tree.json')).write_bytes(b);return tag,{x['path']:x['sha'] for x in t['tree'] if x['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:trees=dict(ex.map(tree,pins))
lookup={v:k for k,v in pins.items()};paths=set();anchors=[]
for name,f in reports.items():
 b=f.read_bytes();(p/(name+'-REPORT.md')).write_bytes(b)
 for repo,pin,path,line in re.findall(r'https://github.com/([^/]+/[^/]+)/blob/([0-9a-f]{40})/([^\s)#]+)#L(\d+)',b.decode()):
  tag=lookup[(repo,pin)];paths.add((tag,path));anchors.append({'report':name,'tag':tag,'path':path,'line':int(line)})
paths.update([('native','runtime/src/storage/memory.rs'),('release','runtime/src/deterministic.rs')])
def fetch(item):
 tag,path=item;repo,pin=pins[tag];u=f'https://raw.githubusercontent.com/{repo}/{pin}/{path}';b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Baton-independent-fixture-review'}),timeout=60).read();f=p/'sources'/tag/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);g=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert g==trees[tag][path];return {'tag':tag,'repo':repo,'pin':pin,'path':path,'url':u,'local':str(f.relative_to(p)),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':g,'tree_blob':trees[tag][path],'blob_verified':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:rows=list(ex.map(fetch,sorted(paths)))
for a in anchors:
 lines=(p/'sources'/a['tag']/a['path']).read_text().splitlines();assert 1<=a['line']<=len(lines);a['line_text']=lines[a['line']-1]
(p/'source-manifest.json').write_text(json.dumps(rows,indent=2));(p/'anchor-receipts.json').write_text(json.dumps(anchors,indent=2));(p/'report-hashes.json').write_text(json.dumps({n:hashlib.sha256(f.read_bytes()).hexdigest() for n,f in reports.items()},indent=2));print({'files':len(rows),'anchors':len(anchors)})
