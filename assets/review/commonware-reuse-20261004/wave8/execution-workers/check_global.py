from pathlib import Path
from collections import Counter
import re,json,subprocess,hashlib,datetime,urllib.request,concurrent.futures
root=Path.cwd();b=root/'assets/review/commonware-reuse-20261004/wave8/execution-workers';out=b/'global-review';out.mkdir(exist_ok=True);base='99dc2c456c4b318fefb368cb39a145298f7d86b7';pages=['docs/consensus/block-body.md','docs/consensus/ordered-input.md','docs/execution/qmdb.md','docs/execution/README.md'];tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',base,'docs']).decode().splitlines();md=[p for p in tracked if p.endswith('.md')];hashes={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in pages};fences=lambda s:re.findall(r'^```(?:rust[^\n]*|mermaid)\n[\s\S]*?^```',s,re.M);urls=lambda s:Counter(re.findall(r'\]\((https?://[^\s)]+)\)',s));introduced=[]
for p in md:
 old=subprocess.check_output(['git','show',base+':'+p]).decode();new=(root/p).read_text();assert re.findall(r'^#{1,6} .*$',old,re.M)==re.findall(r'^#{1,6} .*$',new,re.M),p+' headings';assert not (urls(old)-urls(new)),p+' citations';assert fences(old)==fences(new),p+' code';assert re.findall(r'<a id="[^"]+"',old)==re.findall(r'<a id="[^"]+"',new),p+' anchors';
 for u,c in (urls(new)-urls(old)).items(): introduced.extend([u]*c)
assets=[]
for p in tracked:
 if p.endswith('.md'):continue
 v=subprocess.check_output(['git','show',base+':'+p]);assert v==(root/p).read_bytes(),p+' asset changed';assets.append({'path':p,'sha256':hashlib.sha256(v).hexdigest()})
export=(root/'docs/assets/interfaces/baton.rs').read_text();traits=re.findall(r'^pub trait (\w+)',export,re.M);methods=re.findall(r'^    fn (\w+)',export,re.M);assert traits==['TxPool','Orderer','Baton','Executor','Storage'];assert len(methods)==30
blank=0
for p in md:
 active=False
 for line in (root/p).read_text().splitlines():
  if line.startswith('| Item | Decision |'):active=True;continue
  if not line.startswith('|'):active=False
  if active and line.startswith('|') and not line.startswith('|---'):
   cells=[x.strip() for x in line.strip('|').split('|')]
   if len(cells)==2:assert not cells[1];blank+=1
assert blank==39
existing=[]
for mf in [b/'source-manifest.json',b/'independent-cross-review/source-manifest.json']:
 existing+=json.loads(mf.read_text())['sources']
indexed={(x['repo'],x['pin'],x['path']):x for x in existing};newrefs=[]
for u in introduced:
 m=re.fullmatch(r'https://github.com/([^/]+/[^/]+)/blob/([0-9a-f]{40})/([^#]+)#L(\d+)',u);assert m,u;r,p,path,line=m.groups();newrefs.append((u,r,p,path,int(line)))
missing=set((r,p,path) for _,r,p,path,_ in newrefs)-set(indexed)
# Existing complete authenticated wave8 trees verified before retrieving these raw files.
trees={}
for r,p,path in missing:
 tag={'commonwarexyz/monorepo':'native','tempoxyz/tempo':'tempo'}[r];t=json.loads((b/(tag+'-tree.json')).read_text());assert not t.get('truncated');trees[(r,p)]={x['path']:x['sha'] for x in t['tree'] if x['type']=='blob'}
def fetch(k):
 r,p,path=k;u=f'https://raw.githubusercontent.com/{r}/{p}/{path}';v=urllib.request.urlopen(u,timeout=40).read();blob=hashlib.sha1(f'blob {len(v)}\0'.encode()+v).hexdigest();assert blob==trees[(r,p)][path];f=out/'sources'/r/p/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(v);return {'repo':r,'pin':p,'path':path,'url':u,'local':str(f),'sha256':hashlib.sha256(v).hexdigest(),'git_blob':blob,'tree_blob':trees[(r,p)][path]}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e:fetched=list(e.map(fetch,sorted(missing)))
indexed.update({(x['repo'],x['pin'],x['path']):x for x in fetched});anchors=[];used={}
for u,r,p,path,line in newrefs:
 x=indexed[(r,p,path)];ls=Path(x['local']).read_text().splitlines();assert 1<=line<=len(ls);used[(r,p,path)]=x;anchors.append({'url':u,'line_text':ls[line-1]})
check=subprocess.run(['python3','assets/tooling/check_docs.py','--migration'],capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr;(out/'docs-check.json').write_text(check.stdout)
receipt={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':base,'page_hashes':hashes,'changed_docs':subprocess.check_output(['git','diff','--name-only',base,'--','docs']).decode().splitlines(),'markdown_pages_preserved':len(md),'unchanged_headings':True,'old_external_url_occurrences_preserved':True,'rust_mermaid_blocks_preserved':True,'explicit_anchors_preserved':True,'public_traits':traits,'method_count':len(methods),'blank_policy_cells':blank,'non_md_docs_assets_unchanged':assets,'new_source_citation_occurrences':anchors,'fresh_matched_source_files_for_new_citations':list(used.values()),'additional_fetched_files':fetched,'docs_check':json.loads(check.stdout)}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'pages':hashes,'md':len(md),'assets':len(assets),'introduced_citations':len(anchors),'sources':len(used),'additional_fetches':len(fetched),'traits':traits,'methods':len(methods),'choices':blank,'docs_check':receipt['docs_check']},indent=2))
