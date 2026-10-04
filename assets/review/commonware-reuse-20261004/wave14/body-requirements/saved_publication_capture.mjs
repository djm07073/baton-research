import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {marked} from 'marked';
const pub='assets/review/commonware-reuse-20261004/wave13/publication';
const expected=JSON.parse(await readFile(path.join(pub,'expected-markdown.json'),'utf8'));
const verification=JSON.parse(await readFile(path.join(pub,'gitbook-verification.json'),'utf8'));
const pairs=[];
for(const e of verification.checks){
 const filename='baton-wave13-gitbook-readback-'+(e.source.startsWith('@')?'group-'+e.source.slice(1):e.source.replaceAll('/','__'))+'.json';
 const envelope=JSON.parse(await readFile(path.join(pub,filename),'utf8'));
 const actual=JSON.parse(envelope.result.content[0].text);
 const source=expected[e.source];
 pairs.push({source:e.source,pageId:actual.id,documentId:actual.documentId,sourceMarkdown:source,readMarkdown:actual.markdown,sourceHTML:marked.parse(source.replace(/\s\{#section-\d+\}/g,'')),readHTML:marked.parse(actual.markdown),savedCheck:e});
}
await writeFile('assets/review/commonware-reuse-20261004/wave14/body-requirements/SAVED_PUBLICATION_PAIRS.json',JSON.stringify(pairs,null,2)+'\n');
console.log(JSON.stringify({pages:pairs.length,scope:'New independent parsing of saved wave13 readbacks, no remote request or raw attachment fetch'}));
