from pathlib import Path
import re,subprocess,json,hashlib,datetime
from collections import Counter
base=Path(__file__).parent;baseline='b5747f6a28527a4507901f2e46b426b5ff2a4b7c';changed=subprocess.check_output(['git','diff','--name-only',baseline,'--','docs']).decode().splitlines();assert len(changed)==8 and all(p.endswith('.md') for p in changed)
sha=lambda b:hashlib.sha256(b).hexdigest();old=lambda p:subprocess.check_output(['git','show',f'{baseline}:{p}']);allpages=subprocess.check_output(['git','ls-tree','-r','--name-only',baseline,'docs']).decode().splitlines();md=[p for p in allpages if p.endswith('.md')];rows=[];anchors=[]
source_index={}
for name in ['global-review-source-receipts.json','body-review-receipts.json']:
 m=json.loads((base/name).read_text());source_index.update({(r['repo'],r['pin'],r['path']):Path(r['local']) for r in m['sources']})
m=json.loads((base/'source-manifest.json').read_text())
for r in m['sources']:
 if not r.get('local'):continue
 source_index[(r['repo'],r['pin'],r['path'])]=Path(r['local'])
for p in md:
 b=old(p);c=Path(p).read_bytes();bt=b.decode();ct=c.decode();head=lambda s:re.findall(r'^#{1,6} .+$',s,re.M);urls=lambda s:Counter(re.findall(r'\]\((https?://[^\s)]+)\)',s));fence=lambda s,lang:re.findall(r'```'+lang+r'\n([\s\S]*?)\n```',s)
 assert head(bt)==head(ct),p
 assert not(urls(bt)-urls(ct)),p
 assert fence(bt,'mermaid')==fence(ct,'mermaid'),p
 assert fence(bt,'rust')==fence(ct,'rust'),p
 assert fence(bt,'rust,ignore')==fence(ct,'rust,ignore'),p
 new_urls=list((urls(ct)-urls(bt)).elements())
 for u in new_urls:
  match=re.fullmatch(r'https://github.com/([^/]+/[^/]+)/blob/([a-f0-9]{40})/([^#]+)#L(\d+)',u)
  if match:
   repo,pin,path,num=match.groups();src=source_index[(repo,pin,path)];lines=src.read_text().splitlines();n=int(num);assert 0<n<=len(lines);anchors.append({'page':p,'url':u,'line_text':lines[n-1],'source_sha256':sha(src.read_bytes()),'source_snapshot':str(src)})
 rows.append({'path':p,'baseline_sha256':sha(b),'current_sha256':sha(c),'changed':b!=c,'headings_preserved':True,'prior_external_citation_occurrences_preserved':True,'mermaid_fences_identical':True,'rust_fences_identical':True,'existing_library_excerpts_identical':True,'new_external_citation_occurrences':len(new_urls)})
rust=Path('docs/overview/rust-interfaces.md').read_text();blocks=re.findall(r'```rust\n([\s\S]*?)\n```',rust);traits=re.findall(r'pub trait (\w+)', '\n'.join(blocks));assert traits==['TxPool','Orderer','Baton','Executor','Storage']
exports='docs/assets/interfaces/baton.rs';assert old(exports)==Path(exports).read_bytes()
blank=filled=0
for p in md:
 in_table=False
 for line in Path(p).read_text().splitlines():
  if line.startswith(('| Item | Decision |','| 항목 | 결정 |')):in_table=True;continue
  if not line.startswith('|'):in_table=False
  if in_table and line.startswith('|') and not line.startswith('|---'):
   cells=[v.strip() for v in line.strip('|').split('|')]
   if len(cells)==2:
    if cells[1]:filled+=1
    else:blank+=1
assert blank==39 and filled==0
assets=[p for p in allpages if p.startswith('docs/assets/diagrams/')];assert all(old(p)==Path(p).read_bytes() for p in assets)
reports=[]
for p in list(base.parent.rglob('*REVIEW.md'))+list(base.parent.rglob('REPORT.md')):
 if p.name=='DOCS_GLOBAL_REVIEW.md':continue
 reports.append({'path':str(p),'sha256':sha(p.read_bytes())})
result={'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':baseline,'changed_pages':changed,'all_baseline_markdown_pages_checked':len(md),'pages':rows,'five_traits':traits,'application_rust_blocks_identical':True,'upstream_ignored_rust_blocks_identical':True,'export_sha256':sha(Path(exports).read_bytes()),'export_identical_to_baseline':True,'blank_policy_cells':blank,'filled_policy_cells':filled,'all_diagram_assets_unchanged':True,'diagram_assets_checked':len(assets),'introduced_source_citations':anchors,'reviewed_evidence_reports':reports}
(base/'global-page-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'changed_pages':len(changed),'all_pages_checked':len(md),'new_citations_checked':len(anchors),'blank':blank,'filled':filled,'traits':traits,'diagram_assets_checked':len(assets)}))
