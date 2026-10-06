from pathlib import Path
import json,re,urllib.parse,runpy,hashlib
R=Path('/Users/leojin/Documents/Codex/2026-09-30/task/overpass-research'); D=R/'docs'; W=Path('/tmp/baton-publication-20261006')
utils=runpy.run_path('/tmp/baton-reuse-gitbook.py'); headings=utils['heading_records']; outside=utils['outside_code']; maps=json.loads((W/'page-map.json').read_text()); baseline=json.loads((R/'assets/review/commonware-reuse-20261004/wave15/publication/expected-markdown.json').read_text()); live=json.loads((W/'live-content.json').read_text()); assets=json.loads((W/'asset-manifest.json').read_text()); uploaded=json.loads((W/'uploaded-files.json').read_text())
for x in uploaded: maps['files'][assets[x['index']]['source']]=x['file']['id']
(W/'page-map.json').write_text(json.dumps(maps,indent=2))
groups=[]; pages=[]; current=None
for l in (D/'SUMMARY.md').read_text().splitlines():
 if l.startswith('## '):
  slug={'Overview':'overview','Tx layer':'tx','Consensus layer':'consensus','Baton layer':'baton','Execution layer':'execution','E2E cases':'e2e','Benchmark baselines':'baselines','Development and references':'reference'}[l[3:]]; current={'title':l[3:],'slug':slug,'pages':[]}; groups.append(current)
 m=re.match(r'\* \[(.*?)\]\((.*?)\)',l)
 if m:
  p={'title':m[1],'source':m[2]}; pages.append(p)
  if current:current['pages'].append(p)
ids={**maps['pages'],**{'@'+k:v for k,v in maps['groups'].items()}}; expected={}
for p in pages:
 src=p['source']; md=(D/src).read_text()
 def link(m):
  href=m[1]
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',href) or href.startswith('#'):return m[0]
  path,sep,frag=href.partition('#'); target=(D/Path(src).parent/urllib.parse.unquote(path)).resolve(); rel=str(target.relative_to(D))
  if rel=='SUMMARY.md': return '](/pages/'+maps['pages']['README.md']+'#complete-table-of-contents)'
  if rel in maps['pages']:return '](/pages/'+maps['pages'][rel]+(sep+frag if sep else '')+')'
  assert rel in maps['files'],(src,href)
  return '](/files/'+maps['files'][rel]+')'
 md=outside(md,lambda x:re.sub(r'\]\(([^)]+)\)',link,x))
 if src=='README.md':
  md+='\n## Complete table of contents\n\n'
  for g in groups:md+='### ['+g['title']+'](/pages/'+maps['groups'][g['slug']]+')\n\n'+'\n'.join('- ['+p['title']+'](/pages/'+maps['pages'][p['source']]+')' for p in g['pages'])+'\n\n'
 expected[src]=md
for g in groups:expected['@'+g['slug']]='# '+g['title']+'\n\n'+'\n'.join('- ['+p['title']+'](/pages/'+maps['pages'][p['source']]+')' for p in g['pages'])+'\n'
assert len(expected)==40
prepared={}; anchor_maps={}; reports=[]
for src,md in expected.items():
 old=headings(baseline.get(src,'')); current=headings(md); prev={h['slug']:h['id'] for h in old if h['id']}; used=set(prev.values()); next_num=max([int(x.rsplit('-',1)[1]) for x in used] or [0])+1; lines=md.splitlines(keepends=True); amap={}; active=set(); aliases={}
 for match in re.finditer(r'<a id="([^"]+)"></a>',md):
  after=md[match.end():]; nxt=re.search(r'^#{1,6} .+$',after,re.M)
  if nxt:
   h=headings(nxt[0]+'\n')[0]; aliases[match[1]]=h['slug']
 for h in current:
  dest=prev.get(h['slug'])
  if not dest:
   options=[prev[a] for a,s in aliases.items() if s==h['slug'] and a in prev and prev[a] not in active]
   if options:dest=options[0]
  if h['level']==1:dest=None
  elif not dest:
   while f'section-{next_num:03}' in used:next_num+=1
   dest=f'section-{next_num:03}'; used.add(dest); next_num+=1
  amap[h['slug']]=dest
  if dest:active.add(dest);lines[h['line']]=lines[h['line']].rstrip('\n')+' {#'+dest+'}\n'
 missing=[(slug,aid) for slug,aid in prev.items() if aid not in active]
 for slug,aid in missing:
  assert src=='overview/rust-interfaces.md' and slug=='orderer',(src,slug,aid)
  lines.append('\n## Former Orderer role {#'+aid+'}\n\nThis compatibility anchor retains earlier links. The role is now inside [Baton](#baton); there is no separate public Orderer trait.\n'); amap[slug]=aid; active.add(aid)
 for a,target in aliases.items():
  if a not in amap and target in amap:amap[a]=amap[target]
 assert set(prev.values()).issubset(active),(src,prev,active)
 assert len(active)==len(re.findall(r'\{#section-\d+\}',''.join(lines))),src
 prepared[src]=''.join(lines); anchor_maps[ids[src]]=amap; reports.append({'source':src,'preserved_anchors':len(prev),'new_anchors':len(active-set(prev.values())),'compatibility_aliases':missing})
resolved={}
for src,md in prepared.items():
 def anchor(m):
  href=m[1]; target=re.match(r'^/pages/([^#]+)#(.+)$',href)
  pid,frag=(target[1],target[2]) if target else (ids[src],href[1:]) if href.startswith('#') else (None,None)
  if pid is None:return m[0]
  frag=urllib.parse.unquote(frag); assert frag in anchor_maps[pid],(src,href)
  dest=anchor_maps[pid][frag]; return ']('+('/pages/'+pid if target else '')+('#'+dest if dest else '')+')'
 resolved[src]=outside(md,lambda x:re.sub(r'\]\(([^)]+)\)',anchor,x))
labels={p['source']:p['title'] for p in pages}; labels.update({'@'+g['slug']:g['title'] for g in groups});cr=json.loads((W/'new-pages.json').read_text())['cr']
for name,contents in [('anchors',prepared),('content',resolved)]:
 changes=[{'operation':'update_page','page':ids[src],'title':re.match(r'^# (.+)',md)[1],'linkTitle':labels[src],'document':{'markdown':md}} for src,md in contents.items()]
 for n in range(0,len(changes),8):
  payload={'operationId':'updateChangeRequestContent','params':{'path':{'spaceId':'pvyFEde12m2tVRjI8TRw','changeRequestId':cr},'query':{'compat':False},'body':{'changes':changes[n:n+8]}}}; (W/f'{name}-{n//8:02}.json').write_text(json.dumps(payload))
(W/'expected-markdown.json').write_text(json.dumps(resolved,ensure_ascii=False,indent=2));(W/'anchor-checks.json').write_text(json.dumps(reports,indent=2))
print({'pages':len(resolved),'preserved_anchors':sum(x['preserved_anchors'] for x in reports),'source_bytes':sum(len(x.encode()) for x in resolved.values()),'fences':sum(x.count('```mermaid') for x in resolved.values()),'missing_represented':[(x['source'],x['compatibility_aliases']) for x in reports if x['compatibility_aliases']]})
