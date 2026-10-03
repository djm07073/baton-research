from pathlib import Path
import json,urllib.request,subprocess,concurrent.futures,hashlib,datetime
out=Path(__file__).parent
repos={'native':('commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72',['storage/src/qmdb/mod.rs','storage/src/qmdb/batch_chain.rs','storage/src/qmdb/any/batch.rs','storage/src/qmdb/any/db.rs','storage/src/qmdb/current/batch.rs','storage/src/qmdb/current/db.rs','storage/src/merkle/batch.rs','storage/src/journal/authenticated.rs','glue/src/stateful/db/mod.rs','glue/src/stateful/db/any.rs','glue/src/stateful/db/current.rs','glue/src/stateful/actor/core/verifications.rs','glue/src/stateful/actor/processor/mod.rs']), 'constantinople':('commonwarexyz/constantinople','3b6c92e76bf582855615844a4175b8304808f6a9',['crates/application/src/consensus/db.rs','crates/application/src/consensus/glue.rs','crates/application/src/consensus/execution.rs']), 'alto':('commonwarexyz/alto','1d87569348b5560699465a72d691d90f18affb9c',['chain/src/engine.rs','chain/src/application.rs'])}
trees={}
def tree(name):
 repo,pin,paths=repos[name];r=subprocess.run(['gh','api','--method','GET',f'repos/{repo}/git/trees/{pin}','-f','recursive=1'],capture_output=True,text=True,check=True);d=json.loads(r.stdout);assert not d.get('truncated') and d['sha']==pin;(out/(name+'-tree.json')).write_text(json.dumps(d,indent=2));return name,{x['path']:x['sha'] for x in d['tree'] if x['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for n,t in pool.map(tree,repos):trees[n]=t
def fetch(x):
 name,path=x;repo,pin,_=repos[name];u=f'https://raw.githubusercontent.com/{repo}/{pin}/{path}'
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Baton-source-review'}),timeout=60).read();f=out/'sources'/name/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();return {'repository':repo,'pin':pin,'path':path,'url':u,'local':str(f.relative_to(out)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'tree_blob':trees[name][path],'blob_matches':blob==trees[name][path],'fetched_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 except Exception as e:return {'repository':repo,'pin':pin,'path':path,'error':str(e),'tree_path_present':path in trees[name]}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(fetch,[(n,s) for n,(r,p,ps) in repos.items() for s in ps]))
(out/'source-manifest.json').write_text(json.dumps(rows,indent=2));print({'files':len(rows),'errors':[x for x in rows if 'error'in x],'mismatch':[x for x in rows if not x.get('blob_matches',True)]})
