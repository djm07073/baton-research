from pathlib import Path
import json,hashlib,subprocess,datetime
root=Path.cwd();base='8c75c0486e1adb6e81dda9f50558fa75d2a5510b';out=root/'assets/review/commonware-reuse-20261004/wave14/execution-requirements';other=root/'assets/review/commonware-reuse-20261004/wave14/pool-orderer-requirements';sha=lambda b:hashlib.sha256(b).hexdigest();blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();r=json.loads((other/'requirements-receipt.json').read_text());sources=[]
for x in r['retained_source_rechecks']:
 p=Path(x['local']);b=p.read_bytes();t=root/x['complete_tree_path'];raw=t.read_bytes();assert sha(raw)==x['complete_tree_sha256'];tree=json.loads(raw);assert tree['sha']==x['pin'] and not tree['truncated'];idx={v['path']:v['sha'] for v in tree['tree'] if v['type']=='blob'};assert sha(b)==x['sha256'] and blob(b)==x['git_blob']==idx[x['path']];sources.append({'repo':x['repo'],'pin':x['pin'],'path':x['path'],'local':str(p.relative_to(root)),'sha256':sha(b),'git_blob':blob(b),'tree_blob':idx[x['path']],'matched':True,'scope':'Retained pinned primary bytes independently rehashed with retained complete-tree identity; not new downloads'})
rows=[]
for p in subprocess.check_output(['git','ls-files','docs']).decode().splitlines():
 b=(root/p).read_bytes();assert b==subprocess.check_output(['git','show',base+':'+p]) and b==(Path('/Users/leojin/dev/baton')/p).read_bytes();rows.append({'path':p,'sha256':sha(b),'baseline_equal':True,'mirror_equal':True})
reports=[{'path':str(p.relative_to(root)),'sha256':sha(p.read_bytes())} for p in [other/'REQUIREMENTS_AUDIT.md',other/'READER_DELTA.md',other/'requirements-receipt.json']]
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':base,'reports':reports,'docs':rows,'retained_sources':sources,'fresh_downloads':0,'scope':'Independent original Tx/pool/body/Orderer documentary requirement/source-boundary review, no code/build/test/external publication','goal_completion':False,'six_hour_end':'2026-10-04 01:29:14 UTC'}
(out/'POOL_CROSS_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'reports':reports,'docs':len(rows),'sources':len(sources)}))
