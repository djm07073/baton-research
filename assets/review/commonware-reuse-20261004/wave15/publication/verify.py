import json,re,collections,hashlib,sys
prefix=sys.argv[1] if len(sys.argv)>1 else "/tmp/baton-wave10-gitbook"
from pathlib import Path
from html.parser import HTMLParser
class Text(HTMLParser):
 def __init__(self):super().__init__();self.text=[]
 def handle_data(self,s):self.text.append(s)
def plain(html):
 p=Text();p.feed(html);return re.sub(r'\s+',' ',''.join(p.text)).strip()
def links(md,pid):
 md=re.sub(r'^```[^\n]*\n.*?^```[^\n]*$', '',md,flags=re.M|re.S)
 return collections.Counter('/pages/'+pid+x if x.startswith('#') else x for x in re.findall(r'\]\(([^)]+)\)',md))
def fences(md):return re.findall(r'^```([^\n]*)\n(.*?)^```',md,re.M|re.S)
d=json.loads(Path(prefix+'-semantic.json').read_text());checks=[];failures=[];total_links=0;mermaid=0
for k,v in d.items():
 a,b=plain(v['sourceHTML']),plain(v['readHTML']);texts=a==b;code=fences(v['source'])==fences(v['read']);expected=links(v['source'],v['pageId']);actual=links(v['read'],v['pageId']);linkcheck=expected==actual
 if not texts:failures.append(k+': text differs')
 if not code:failures.append(k+': code differs')
 if not linkcheck:failures.append(k+': links differ '+str(expected-actual)+'; extra '+str(actual-expected))
 anchors_expected=re.findall(r'\{#(section-\d+)\}',v['source']);anchors_read=re.findall(r'id="(section-\d+)"',v['read'])
 if anchors_expected!=anchors_read:failures.append(k+': heading anchor differs')
 total_links+=sum(actual.values());mermaid+=v['read'].count('```mermaid')
 checks.append({'source':k,'pageId':v['pageId'],'documentId':v['documentId'],'url':v['url'],'text_preserved':texts,'fences_preserved':code,'links_preserved':linkcheck,'markdown_sha256':hashlib.sha256(v['read'].encode()).hexdigest()})
traits=re.findall(r'pub trait (\w+)',d['overview/rust-interfaces.md']['read']);assert traits==['TxPool','Orderer','Baton','Executor','Storage'],traits
assert len(d)==38 and mermaid==18
baseline=json.loads(Path('/tmp/baton-wave13-gitbook-expected.json').read_text())
preserved=0
for source,old in baseline.items():
 for anchor in re.findall(r'\{#(section-\d+)\}',old):
  assert anchor in re.findall(r'id="(section-\d+)"',d[source]['read']),(source,anchor)
  preserved+=1
assert 'id="section-012"' in d['overview/rust-interfaces.md']['read']
assert not failures, '\n'.join(failures)
report={'verified_pages':len(d),'content_pages':31,'section_indexes':7,'links':total_links,'mermaid_diagrams':mermaid,'traits':traits,'old_heading_anchors_preserved':preserved,'checks':checks,'failures':failures}
Path(prefix+'-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
