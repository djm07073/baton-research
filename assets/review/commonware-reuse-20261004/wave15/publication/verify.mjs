import fs from 'node:fs';import {marked} from '/Users/leojin/Documents/Codex/2026-09-30/task/overpass-research/node_modules/marked/lib/marked.esm.js';
const prefix=process.argv[2] || '/tmp/baton-wave10-gitbook';
const expected=JSON.parse(fs.readFileSync(prefix+'-expected.json','utf8'));const samples={};
for(const [source,md] of Object.entries(expected)){
 const file=prefix+'-readback-'+source.replaceAll('/','__').replace('@','group-')+'.json';
 if(!fs.existsSync(file))throw new Error('Readback pending: '+source);
 const r=JSON.parse(fs.readFileSync(file,'utf8'));if(r.result.isError)throw new Error(source+': '+r.result.content[0].text);
 const page=JSON.parse(r.result.content[0].text);
 samples[source]={sourceHTML:marked.parse(md.replace(/ \{#section-\d+\}$/gm,'')),readHTML:marked.parse(page.markdown),source:md,read:page.markdown,pageId:page.id,url:page.urls.app,documentId:page.documentId};
}
fs.writeFileSync(prefix+'-semantic.json',JSON.stringify(samples));
