from pathlib import Path
import hashlib,json,subprocess,re,datetime
root=Path.cwd();out=root/'assets/review/commonware-reuse-20261004/wave14/execution-requirements';base='8c75c0486e1adb6e81dda9f50558fa75d2a5510b';sha=lambda b:hashlib.sha256(b).hexdigest();rows=[]
for p in subprocess.check_output(['git','ls-files','docs']).decode().splitlines():
 b=(root/p).read_bytes();assert b==subprocess.check_output(['git','show',base+':'+p]) and b==(Path('/Users/leojin/dev/baton')/p).read_bytes();rows.append({'path':p,'sha256':sha(b),'baseline_equal':True,'mirror_equal':True})
authority=[{'path':p,'sha256':sha((root/p).read_bytes())} for p in ['AGENTS.md','README.md','BATON_HANDOFF.md','baton-paper.md','docs/README.md','docs/SUMMARY.md']]
summary=(root/'docs/SUMMARY.md').read_text();pages=['docs/'+v for v in re.findall(r'\]\(([^)]+\.md)\)',summary)];manifest=json.loads((root/'docs/assets/diagrams/render-manifest.json').read_text());diagrams=[]
for d in manifest['diagrams']:
 found=[]
 for p in pages:
  s=(root/p).read_text()
  for x in re.finditer(r'```mermaid\n([\s\S]*?)\n```',s):
   if sha(x[1].encode())==d['source_sha256']:found.append({'page':p,'line':s[:x.start()].count('\n')+1})
 assert len(found)==1;diagrams.append({'name':d['name'],'source_sha256':d['source_sha256'],'canonical_source':found[0],'mmd_sha256':sha((root/f"docs/assets/diagrams/{d['name']}.mmd").read_bytes()),'svg_sha256':sha((root/f"docs/assets/diagrams/{d['name']}.svg").read_bytes()),'scope':'Source/artifact hashes, not new rendered visual QA'})
md=(root/'docs/overview/rust-interfaces.md').read_text();blocks=re.findall(r'```rust\n([\s\S]*?)\n```',md);body='\n\n'.join(re.sub(r'^use std::future::Future;\n\n','',s) for s in blocks);ex='// @generated from docs/overview/rust-interfaces.md; edit that Markdown source.\n// Application interface proposals only; no protocol implementation.\n\nuse std::future::Future;\n\n'+body+'\n';assert ex==(root/'docs/assets/interfaces/baton.rs').read_text()
prior=[]
for p in ['wave3/storage-types/REPORT.md','wave4/compatibility/REPORT.md','wave4/compatibility/CERTIFICATION_CROSS_REVIEW.md','wave5/branch-access/REPORT.md','wave6/repeated-sync/REPORT.md','wave7/execution-tree/REPORT.md','wave8/state-query/REPORT.md','wave9/storage-fixtures/REPORT.md','wave11/execution-coverage/COVERAGE_AUDIT.md','wave12/execution-walkthrough/REPORT.md','wave13/execution-seams/REPORT.md','wave13/execution-seams/FINAL_READER_ACK.md']:
 fp=root/'assets/review/commonware-reuse-20261004'/p;prior.append({'path':str(fp.relative_to(root)),'sha256':sha(fp.read_bytes()),'scope':'Retained source/API or reader review, not new primary retrieval'})
r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':base,'authority':authority,'tracked_docs':rows,'diagrams':diagrams,'rust_export_exact':True,'traits':re.findall(r'pub trait (\w+)',md),'methods':re.findall(r'^    fn (\w+)\(',md,re.M),'retained_review_lineage':prior,'source_scope':'Current documentary/API fit checked against retained pinned primary receipts; no new API uncertainty or fresh broad retrieval','tests_build_implementation':False,'six_hour_window_end':'2026-10-04 01:29:14 UTC','goal_completion':False}
assert len(rows)==88 and len(diagrams)==18 and len(r['traits'])==5 and len(r['methods'])==30
(out/'REQUIREMENTS_RECEIPT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'docs':len(rows),'diagrams':len(diagrams),'traits':len(r['traits']),'methods':len(r['methods']),'retained_reviews':len(prior)}))
