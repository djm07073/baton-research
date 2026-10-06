import fs from 'node:fs';
import {marked} from '/Users/leojin/Documents/Codex/2026-09-30/task/overpass-research/node_modules/marked/lib/marked.esm.js';
const w='/tmp/baton-publication-20261006';
const e=JSON.parse(fs.readFileSync(w+'/expected-markdown.json'));
const r=JSON.parse(fs.readFileSync(w+'/'+(process.argv[2]||'draft-readback.json')));
const pairs={};
for(const [source,md] of Object.entries(e)){
 const p=r[source];if(!p)throw Error('Missing '+source);
 pairs[source]={sourceHTML:marked.parse(md.replace(/\s\{#section-\d+\}/g,'')),readHTML:marked.parse(p.markdown),source:md,read:p.markdown,pageId:p.id,documentId:p.documentId,url:p.urls.app};
}
fs.writeFileSync(w+'/semantic.json',JSON.stringify(pairs));
