from pathlib import Path
import hashlib,json,subprocess,re,datetime
root=Path.cwd();out=root/'assets/review/commonware-reuse-20261004/wave13/body-seams';base='78d5f2eca347b0fc04b7f7d31ff858cc2a69bee4';sha=lambda b:hashlib.sha256(b).hexdigest();changed={'docs/tx/README.md','docs/overview/interfaces.md'};old='**Nunchi supplies the queue/selection actor; TxPool connects its payload and canonical lifecycle to Baton.**';new='**Nunchi supplies the queue/selection actor; TxPool adds payload hooks and connects durable Executor outcomes to that actor.**';sentence='`CommitResult` is passed by value: use concrete cloneable receipt handles or recover copies of the same immutable receipt for multiple consumers; type equality and `Send` do not duplicate an owned value.'
records=[]
for p in subprocess.check_output(['git','ls-files','docs']).decode().splitlines():
 b=(root/p).read_bytes();original=subprocess.check_output(['git','show',base+':'+p]);expected=original
 if p=='docs/tx/README.md':assert original.decode().count(old)==1;expected=original.decode().replace(old,new).encode()
 if p=='docs/overview/interfaces.md':anchor='`Executor::Block` is assembled';assert original.decode().count(anchor)==1;expected=original.decode().replace(anchor,sentence+'\n\n'+anchor).encode()
 assert b==expected,p
 if p in changed:
  assert re.findall(rb'^#+ .+$',b,re.M)==re.findall(rb'^#+ .+$',original,re.M)
  assert re.findall(rb'\]\(([^)]+)\)',b)==re.findall(rb'\]\(([^)]+)\)',original)
 records.append({'path':p,'sha256':sha(b),'baseline_sha256':sha(original),'changed':b!=original})
assert len(records)==88 and {e['path'] for e in records if e['changed']}==changed
previous=json.loads((out/'CURRENT_READER_RECEIPT.json').read_text());
for e in previous['diagrams']:assert sha((root/e['source']).read_bytes())==e['source_sha256'];assert sha((root/Path(e['source']).with_suffix('.svg')).read_bytes())==e['svg_sha256']
md=(root/'docs/overview/rust-interfaces.md').read_text();parts=re.findall(r'```rust\n([\s\S]*?)\n```',md);expected='// @generated from docs/overview/rust-interfaces.md; edit that Markdown source.\n// Application interface proposals only; no protocol implementation.\n\nuse std::future::Future;\n\n'+'\n\n'.join(re.sub(r'^use std::future::Future;\n\n','',p) for p in parts)+'\n';assert expected.encode()==(root/'docs/assets/interfaces/baton.rs').read_bytes()
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':base,'docs':records,'diagrams_unchanged':18,'traits_unchanged':previous['traits'],'blank_choices_unchanged':previous['blank_decisions'],'export_matches':True,'scope':'Exact final local reader comparison; no remote publication/build/runtime proof'};(out/'FINAL_READER_RECEIPT.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'changed':[e for e in records if e['changed']],'receipt_sha256':sha((out/'FINAL_READER_RECEIPT.json').read_bytes())},indent=2))
