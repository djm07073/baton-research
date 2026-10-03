import json,urllib.request,hashlib,concurrent.futures,datetime
from pathlib import Path
out=Path(__file__).parent
pin='534af0ede48affd35b2111522527547b4cc9bf72'
def get(url):
 return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Baton-source-audit'}),timeout=60).read()
tree=json.loads(get(f'https://api.github.com/repos/commonwarexyz/monorepo/git/trees/{pin}?recursive=1'))
(out/'native-tree.json').write_text(json.dumps(tree,indent=2));assert not tree.get('truncated')
entries={x['path']:x for x in tree['tree'] if x['type']=='blob'}
paths=['storage/src/qmdb/sync/'+p+'.rs' for p in ['mod','database','engine','source','target','journal','requests','error']]+['storage/src/qmdb/'+p for p in ['any/sync/mod.rs','any/db.rs','any/batch.rs','current/sync/mod.rs','current/proof/mod.rs','current/db.rs','current/batch.rs']]+['glue/src/stateful/'+p for p in ['db/mod.rs','db/any.rs','db/current.rs','db/p2p/mod.rs','db/p2p/actor.rs','db/p2p/handler.rs','db/p2p/mailbox.rs','actor/core/syncing.rs','actor/syncer/actor.rs','actor/syncer/plan.rs']]
def fetch(p):
 u=f'https://raw.githubusercontent.com/commonwarexyz/monorepo/{pin}/{p}'
 try:
  b=get(u);blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();s=out/'sources/native'/p;s.parent.mkdir(parents=True,exist_ok=True);s.write_bytes(b)
  return {'path':p,'repository':'commonwarexyz/monorepo','pin':pin,'url':u,'local':str(s.relative_to(out)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'tree_blob':entries[p]['sha'],'blob_matches':blob==entries[p]['sha'],'fetched_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 except Exception as e:return {'path':p,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(fetch,paths))
(out/'source-manifest.json').write_text(json.dumps(rows,indent=2));print(json.dumps({'files':len(rows),'errors':[x for x in rows if 'error'in x],'mismatch':[x for x in rows if not x.get('blob_matches',True)]}))
