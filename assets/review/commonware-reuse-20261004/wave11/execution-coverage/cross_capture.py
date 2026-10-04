from pathlib import Path
import subprocess,json,hashlib,datetime,urllib.request,concurrent.futures
root=Path.cwd(); out=root/'assets/review/commonware-reuse-20261004/wave11/execution-coverage/cross-review';out.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest(); blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
pins={'native':('commonwarexyz/monorepo','534af0ede48affd35b2111522527547b4cc9bf72'),'release':('commonwarexyz/monorepo','d476a2361ce6840d2b9d0aa6fb30a924429046d4'),'nunchi':('nunchi-labs/sdk','eea35ced709f68c15d6fbc8bcc754696a7e44374')}
files=[('native','consensus/src/multimmit/engine.rs'),('native','consensus/src/multimmit/machine/durability.rs'),('native','consensus/src/multimmit/machine/reducer.rs'),('native','p2p/src/authenticated/router/ingress.rs'),('native','storage/src/archive/mod.rs'),('native','storage/src/metadata/storage.rs'),('native','utils/src/acknowledgement.rs'),('release','consensus/src/marshal/standard/relay.rs'),('nunchi','mempool/src/actor.rs'),('nunchi','mempool/src/pool.rs')]
def tree(k):
 repo,pin=pins[k];raw=subprocess.check_output(['gh','api','--method','GET',f'repos/{repo}/git/trees/{pin}','-f','recursive=1']); data=json.loads(raw);assert data['sha']==pin and data['truncated'] is False
 (out/f'{k}-tree.json').write_bytes(raw);return k,{r['path']:r['sha'] for r in data['tree'] if r['type']=='blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:trees=dict(ex.map(tree,pins))
def fetch(spec):
 k,p=spec; repo,pin=pins[k];url=f'https://raw.githubusercontent.com/{repo}/{pin}/{p}'; b=urllib.request.urlopen(url,timeout=60).read(); h=blob(b);assert trees[k][p]==h
 dst=out/'sources'/k/p;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
 return {'id':k,'repo':repo,'pin':pin,'path':p,'url':url,'sha256':sha(b),'git_blob':h,'tree_blob':trees[k][p],'verified':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:rows=list(ex.map(fetch,files))
(out/'source-manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
base=root/'assets/review/commonware-reuse-20261004'; wave=base/'wave11'; identity=[]
for scope in ['goal-coverage','body-coverage','pool-orderer-coverage']:
 p=wave/scope/'COVERAGE_AUDIT.md';identity.append({'path':str(p.relative_to(root)),'sha256':sha(p.read_bytes())})
g=json.loads((wave/'goal-coverage/current-document-delivery-check.json').read_text()); delivery=[]
for r in g['files']:
 p=r['path'];b=(root/p).read_bytes();committed=subprocess.check_output(['git','show','d4915b310c0fd071d6c49b12754fd556f6879981:'+p]);mirror=Path('/Users/leojin/dev/baton')/p
 delivery.append({'path':p,'sha256':sha(b),'matches_claimed':sha(b)==r['sha256'],'matches_baseline':b==committed,'matches_mirror':b==mirror.read_bytes()})
ledger=json.loads((wave/'goal-coverage/prior-review-ledger-check.json').read_text()); previous=[]
for r in ledger['entries']:
 p=base/r['path'];h=sha(p.read_bytes());previous.append({'path':r['path'],'sha256':h,'matches_claimed':h==r['expected']==r['actual']})
assert all(all(r[k] for k in ['matches_claimed','matches_baseline','matches_mirror']) for r in delivery)
assert all(r['matches_claimed'] for r in previous)
origin=subprocess.check_output(['git','remote','get-url','origin']).decode().strip()
repo=origin.split(':',1)[1].removesuffix('.git') if origin.startswith('git@github.com:') else origin.split('github.com/',1)[1].removesuffix('.git')
remote=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/git/ref/heads/main']))['object']['sha']
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'report_hashes':identity,'docs':delivery,'prior_reports':previous,'origin_main':remote,'scope':'Independent exact-byte receipt audit plus focused fresh sources; not all historical source citations freshly fetched, not semantic proof, no compile/run/build'}
(out/'coverage-identity-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'source_files':len(rows),'trees':len(trees),'reports':identity,'docs':len(delivery),'ledger':len(previous),'origin_main':remote}))
