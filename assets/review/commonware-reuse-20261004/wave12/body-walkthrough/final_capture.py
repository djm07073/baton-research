from pathlib import Path
import hashlib,json,re,subprocess,datetime
root=Path.cwd();baseline='d4915b310c0fd071d6c49b12754fd556f6879981';old=b'Selection alone does not retire transactions from the pool.';new=b'Selection alone does not establish canonical retirement.'
sha=lambda b:hashlib.sha256(b).hexdigest()
paths=subprocess.check_output(['git','ls-files','docs']).decode().splitlines();expected_changed={'docs/overview/rust-interfaces.md','docs/assets/interfaces/baton.rs'};records=[]
for p in paths:
 b=(root/p).read_bytes();base=subprocess.check_output(['git','show',baseline+':'+p]);assert b==(base.replace(old,new) if p in expected_changed else base)
 records.append({'path':p,'sha256':sha(b),'baseline_sha256':sha(base),'changed':b!=base})
assert len(records)==88 and {e['path'] for e in records if e['changed']}==expected_changed
md=(root/'docs/overview/rust-interfaces.md').read_text();parts=re.findall(r'```rust\n([\s\S]*?)\n```',md);expected='// @generated from docs/overview/rust-interfaces.md; edit that Markdown source.\n// Application interface proposals only; no protocol implementation.\n\nuse std::future::Future;\n\n'+'\n\n'.join(re.sub(r'^use std::future::Future;\n\n','',p) for p in parts)+'\n';assert (root/'docs/assets/interfaces/baton.rs').read_bytes()==expected.encode()
traits=re.findall(r'^pub trait (\w+)',md,re.M);assert traits==['TxPool','Orderer','Baton','Executor','Storage']
diagrams=[]
for p in root.glob('docs/**/*.md'):
 text=p.read_text()
 for block in re.findall(r'```mermaid\n(.*?)```',text,re.S):diagrams.append({'page':str(p.relative_to(root)),'sha256':sha(block.strip().encode())})
assert len(diagrams)==18
blank=0
for p in root.glob('docs/**/*.md'):
 lines=p.read_text().splitlines();active=False
 for line in lines:
  if line.startswith('| Item | Decision |'):active=True;continue
  if active and not line.startswith('|'):active=False
  if active and re.fullmatch(r'\|[^|]+\|\s*\|',line):blank+=1
assert blank==39
out=root/'assets/review/commonware-reuse-20261004/wave12/body-walkthrough';record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),'baseline':baseline,'tracked_docs':records,'traits':traits,'blank_decisions':blank,'diagrams':diagrams,'export_matches':True,'scope':'Final reader bytes/source fit only; no build/runtime/remote-publication verification'};(out/'FINAL_READER_RECEIPT.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'tracked_docs':len(records),'changed':[e for e in records if e['changed']],'traits':traits,'blanks':blank,'diagrams':len(diagrams),'receipt_sha256':sha((out/'FINAL_READER_RECEIPT.json').read_bytes())},indent=2))
