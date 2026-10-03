import json,urllib.request,hashlib,concurrent.futures,datetime
from pathlib import Path
p=Path(__file__).parent;m=json.loads((p/'source-manifest.json').read_text());repos={'nunchi':('nunchi-labs/sdk','eea35ced709f68c15d6fbc8bcc754696a7e44374'),'native':('commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72')};trees={tag:{e['path']:e['sha'] for e in json.loads((p/f'{tag}-tree.json').read_text())['tree'] if e['type']=='blob'} for tag in repos};jobs=[('nunchi',x) for x in ['common/src/account.rs','common/src/events.rs','common/src/runtime.rs','common/src/state_db.rs']]+[('native',x) for x in ['runtime/src/utils/mod.rs','runtime/src/utils/cell.rs','runtime/src/utils/handle.rs','runtime/src/telemetry/metrics/mod.rs','runtime/src/telemetry/metrics/histogram.rs','macros/impl/src/lib.rs']]
def fetch(j):
 tag,path=j;repo,pin=repos[tag];url=f'https://raw.githubusercontent.com/{repo}/{pin}/{path}'
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Baton-pool-source-audit'}),timeout=90) as r:b=r.read()
 f=p/'sources'/tag/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);h=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest();assert h==trees[tag][path];return {'repo':repo,'pin':pin,'path':path,'url':url,'local':str(f),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':h,'tree_blob':trees[tag][path],'git_blob_verified':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:m['sources']+=list(ex.map(fetch,jobs))
m['last_fetched_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(p/'source-manifest.json').write_text(json.dumps(m,indent=2)+'\n');print('verified successful sources',sum('failure' not in e for e in m['sources']))
