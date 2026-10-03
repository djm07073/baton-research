from pathlib import Path
import urllib.request,json,re,hashlib,datetime
b=Path(__file__).parent;endpoint='https://mcp.commonware.xyz';headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
def call(msg,name):
 q=urllib.request.Request(endpoint,data=json.dumps(msg).encode(),headers=headers);resp=urllib.request.urlopen(q,timeout=60);raw=resp.read().decode();(b/(name+'.sse')).write_text(raw)
 if resp.headers.get('Mcp-Session-Id'):headers['Mcp-Session-Id']=resp.headers['Mcp-Session-Id']
 try:r=json.loads(raw)
 except json.JSONDecodeError:r=json.loads(next(x[6:] for x in raw.splitlines() if x.startswith('data: ')))
 (b/(name+'.json')).write_text(json.dumps(r,indent=2)+'\n');return r
call({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'Baton-source-audit','version':'1'}}},'mcp-initialize')
tools=call({'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}},'mcp-tools');assert any(x['name']=='get_file' for x in tools['result']['tools'])
r=call({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'get_file','arguments':{'path':'p2p/src/simulated/ingress.rs','version':'v2026.9.0','start_line':400,'end_line':449}}},'mcp-release-simulated')
s='\n'.join(x.get('text','') for x in r['result']['content'] if x['type']=='text');ls=(b/'sources/release/p2p/src/simulated/ingress.rs').read_text().splitlines();num=re.findall(r'^(\d+): ?(.*)$',s,re.M);assert num
for n,line in num:assert ls[int(n)]==line,(n,line,ls[int(n)])
(b/'mcp-content-check.json').write_text(json.dumps({'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'server':'https://mcp.commonware.xyz','explicit_version':'v2026.9.0','numbering':'zero_based','numbered_lines_matched':len(num),'source_sha256':hashlib.sha256((b/'sources/release/p2p/src/simulated/ingress.rs').read_bytes()).hexdigest(),'mcp_response_sha256':hashlib.sha256((b/'mcp-release-simulated.json').read_bytes()).hexdigest()},indent=2)+'\n');print(len(num),'release lines matched')
