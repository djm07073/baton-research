from pathlib import Path
import json,hashlib,subprocess,re,collections,datetime
from html.parser import HTMLParser
root=Path.cwd();out=root/'assets/review/commonware-reuse-20261004/wave14/body-requirements';sha=lambda b:hashlib.sha256(b).hexdigest();baseline='8c75c0486e1adb6e81dda9f50558fa75d2a5510b';assert subprocess.check_output(['git','rev-parse','HEAD']).decode().strip()==baseline
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':baseline,'docs':[],'publication_scope':'Independently re-evaluated saved wave13 readbacks/metadata; no fresh remote request or raw remote attachment-byte proof','source_scope':'Retained own source-pin/tree/blob receipts rehashed; no fresh broad wave14 source catalogue'}
for p in subprocess.check_output(['git','ls-files','docs']).decode().splitlines():
 b=(root/p).read_bytes();assert b==subprocess.check_output(['git','show',baseline+':'+p]);assert b==(Path('/Users/leojin/dev/baton')/p).read_bytes();record['docs'].append({'path':p,'sha256':sha(b),'baseline_equal':True,'mirror_equal':True})
record['authority']=[]
for p in ['AGENTS.md','README.md','BATON_HANDOFF.md','assets/review/commonware-reuse-20261004/run.json']:
 record['authority'].append({'path':p,'sha256':sha((root/p).read_bytes())})
previous=json.loads((root/'assets/review/commonware-reuse-20261004/wave13/body-seams/CURRENT_READER_RECEIPT.json').read_text());record['diagrams']=previous['diagrams']
for e in record['diagrams']:
 assert sha((root/e['source']).read_bytes())==e['source_sha256'];assert sha((root/Path(e['source']).with_suffix('.svg')).read_bytes())==e['svg_sha256']
record['traits']=previous['traits'];record['blank_choices']=previous['blank_decisions'];assert record['blank_choices']==39
class Text(HTMLParser):
 def __init__(self):super().__init__();self.fragments=[]
 def handle_data(self,s):self.fragments.append(s)
def plain(s):
 p=Text();p.feed(s);return re.sub(r'\s+',' ',''.join(p.fragments)).strip()
def fences(md):return re.findall(r'^```([^\n]*)\n(.*?)^```',md,re.M|re.S)
def links(md,pid):
 md=re.sub(r'^```[^\n]*\n.*?^```[^\n]*$','',md,flags=re.M|re.S);return collections.Counter('/pages/'+pid+x if x.startswith('#') else x for x in re.findall(r'\]\(([^)]+)\)',md))
record['saved_publication']=[];pairs=json.loads((out/'SAVED_PUBLICATION_PAIRS.json').read_text())
for e in pairs:
 a,b=e['sourceMarkdown'],e['readMarkdown'];assert plain(e['sourceHTML'])==plain(e['readHTML']),e['source'];assert fences(a)==fences(b);assert links(a,e['pageId'])==links(b,e['pageId']);assert re.findall(r'\{#(section-\d+)\}',a)==re.findall(r'id="(section-\d+)"',b);assert sha(b.encode())==e['savedCheck']['markdown_sha256'];assert e['documentId']==e['savedCheck']['documentId'];record['saved_publication'].append({'source':e['source'],'pageId':e['pageId'],'documentId':e['documentId'],'markdown_sha256':sha(b.encode()),'text_fences_links_anchors_match':True})
record['saved_publication_counts']={'pages':len(pairs),'links':sum(sum(links(e['readMarkdown'],e['pageId']).values()) for e in pairs),'mermaid':sum(e['readMarkdown'].count('```mermaid') for e in pairs)};assert record['saved_publication_counts']=={'pages':38,'links':580,'mermaid':18}
pub=root/'assets/review/commonware-reuse-20261004/wave13/publication';record['saved_receipts']=[]
for p in ['gitbook-verification.json','gitbook-live-verification.json','published-revision.json','anchor-checks.json','draft-delta-check.json']:
 record['saved_receipts'].append({'path':str((pub/p).relative_to(root)),'sha256':sha((pub/p).read_bytes())})
run=json.loads((root/'assets/review/commonware-reuse-20261004/run.json').read_text());record['review_window']={k:run[k] for k in ['objective','started_at_utc','review_window_end_utc','status','requirements']};record['prior_report_ledger']=[]
for wave in run['waves']:
 for r in wave.get('reports',[]):
  p=root/'assets/review/commonware-reuse-20261004'/r['path'];assert sha(p.read_bytes())==r['sha256'];record['prior_report_ledger'].append({'wave':wave['wave'],'path':r['path'],'sha256':r['sha256']})
record['retained_sources']=[]
manifest=json.loads((root/'assets/review/commonware-reuse-20261004/wave10/body-coherence/source-manifest.json').read_text())
for e in manifest['sources']:
 p=root/'assets/review/commonware-reuse-20261004/wave10/body-coherence/sources'/e['kind']/e['path'];b=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();treepath=root/'assets/review/commonware-reuse-20261004/wave10/body-coherence/trees'/(e['kind']+'.json');tree=json.loads(treepath.read_text());assert not tree['truncated'];index={t['path']:t['sha'] for t in tree['tree']};assert blob==index[e['path']]==e['git_blob_sha1'] and sha(b)==e['sha256'];record['retained_sources'].append({'path':str(p.relative_to(root)),'revision':e['revision'],'sha256':sha(b),'git_blob':blob,'tree':str(treepath.relative_to(root))})
lineage=json.loads((root/'assets/review/commonware-reuse-20261004/wave13/body-seams/SOURCE_LINEAGE_RECEIPT.json').read_text());tree=json.loads((root/lineage['tree']).read_text());assert not tree['truncated'];index={t['path']:t['sha'] for t in tree['tree']}
for e in lineage['sources']:
 b=(root/e['local']).read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert sha(b)==e['sha256'] and blob==index[e['path']]==e['git_blob'];record['retained_sources'].append(e)
(out/'REQUIREMENTS_RECEIPT.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'docs':len(record['docs']),'diagrams':len(record['diagrams']),'publication':record['saved_publication_counts'],'prior_reports':len(record['prior_report_ledger']),'retained_sources':len(record['retained_sources']),'receipt_sha256':sha((out/'REQUIREMENTS_RECEIPT.json').read_bytes())},indent=2))
