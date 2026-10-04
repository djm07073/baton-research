from pathlib import Path
import hashlib,json,re,subprocess,datetime
root=Path.cwd();out=root/'assets/review/commonware-reuse-20261004/wave10/body-coherence'
files=['docs/overview/architecture.md','docs/overview/glossary.md','docs/overview/networking.md','docs/overview/rust-interfaces.md','docs/consensus/block-body.md','docs/e2e/normal.md','docs/e2e/block-body.md','docs/e2e/native-consensus.md','docs/e2e/recovery.md','docs/e2e/canonical.md']
receipts=[]
for p in files:
 b=(root/p).read_bytes();dest=out/'reviewed-docs'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 receipts.append({'path':p,'sha256':hashlib.sha256(b).hexdigest()})
md=[p for p in (root/'docs').rglob('*.md') if 'assets' not in p.parts]
diagrams=[]
for p in md:
 t=p.read_text()
 for m in re.finditer(r'```mermaid\n(.*?)```\s*\n\s*\[Open full-size diagram\]\(([^)]+)\)',t,re.S):
  f=(p.parent/m.group(2)).with_suffix('.mmd').resolve();b=f.read_bytes()
  assert m.group(1).strip()==b.decode().strip(),p
  diagrams.append({'page':str(p.relative_to(root)),'path':str(f.relative_to(root)),'sha256':hashlib.sha256(b).hexdigest(),'inline_matches':True})
traits=(root/'docs/overview/rust-interfaces.md').read_bytes()
base=subprocess.check_output(['git','show','01cf73b41dedd81614237977e4edf150c7d19a81:docs/overview/rust-interfaces.md'])
assert traits==base
blanks=0
for p in md:
 ls=p.read_text().splitlines()
 for i,l in enumerate(ls):
  if l.strip()=='| Item | Decision |':
   for row in ls[i+2:]:
    if not row.startswith('|'):break
    if not row.split('|')[-2].strip():blanks+=1
assert blanks==39,blanks
assert len(diagrams)==18,len(diagrams)
result={'reviewer':'/root/reuse_network_v3','recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':'01cf73b41dedd81614237977e4edf150c7d19a81','pages':receipts,'reader_pages_excluding_summary':len(md)-1,'traits':re.findall(r'^pub trait (\w+)',traits.decode(),re.M),'rust_interface_bytes_unchanged':True,'blank_decisions':blanks,'diagrams':diagrams}
(out/'docs-receipts.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'pages_bound':len(receipts),'reader_pages':len(md)-1,'blank_decisions':blanks,'diagrams':len(diagrams),'traits_unchanged':True}))
