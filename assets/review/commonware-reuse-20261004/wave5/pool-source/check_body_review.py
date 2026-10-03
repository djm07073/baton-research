from pathlib import Path
import json,hashlib,re,datetime
base=Path(__file__).parent;other=base.parent/'body-storage';report=other/'REPORT.md';receipt=json.loads((base/'body-review-receipts.json').read_text());fresh={(r['repo'],r['pin'],r['path']):r for r in receipt['sources']};anchors=[]
for repo,pin,path,line in re.findall(r'https://github.com/([^/]+/[^/]+)/blob/([a-f0-9]{40})/([^)#]+)#L(\d+)',report.read_text()):
 row=fresh[(repo,pin,path)];p=Path(row['local']);lines=p.read_text().splitlines();n=int(line);assert 0<n<=len(lines);anchors.append({'repo':repo,'pin':pin,'path':path,'line':n,'line_text':lines[n-1],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'fresh_tree_blob_verified':True})
original=json.loads((other/'source-manifest.json').read_text());rehashed=[]
for row in original['files']:
 tag=row['source'];p=other/'sources'/tag/row['path'];b=p.read_bytes();sha256=hashlib.sha256(b).hexdigest();blob=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest();assert sha256==row['sha256'] and blob==row['blob_sha1'];rehashed.append({'source':tag,'path':row['path'],'sha256_match':True,'blob_match':True})
out={'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),'supplied_manifest_sha256':hashlib.sha256((other/'source-manifest.json').read_bytes()).hexdigest(),'independent_fresh_receipt_sha256':hashlib.sha256((base/'body-review-receipts.json').read_bytes()).hexdigest(),'fresh_decisive_sources':len(fresh),'supplied33_rehash':rehashed,'anchors':anchors}
(base/'body-cross-review-checks.json').write_text(json.dumps(out,indent=2)+'\n');print('independent fresh sources',len(fresh),'fresh-source report anchors',len(anchors),'supplied receipts rehashed',len(rehashed))
