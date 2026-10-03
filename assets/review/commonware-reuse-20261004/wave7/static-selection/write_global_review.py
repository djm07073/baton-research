from pathlib import Path
import hashlib,json,datetime
b=Path(__file__).parent;root=b.parents[4];r=json.loads((b/'global-review/receipt.json').read_text());base=r['baseline'];pages=r['page_hashes'];assert set(r['changed_docs'])==set(pages)
for p,h in pages.items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p+' changed during review'
report=f'''# Wave 7 final global reader and preservation review

Reviewer `/root/reuse_orderer_v3`; baseline `{base}`. Review is bound to the four hashes below. **Pass: no actionable corrections or publication blocker found in this four-page documentation diff.** This conclusion verifies source fit and reader/preservation constraints, not a compiled integration, protocol proof, publication result or completion of the six-hour research goal.

## Exact reviewed pages

| Canonical page | SHA-256 |
|---|---|
'''+''.join(f'| `{p}` | `{h}` |\n' for p,h in pages.items())+f'''
Exactly these four tracked docs pages differ from baseline: 25 inserted lines and one replaced table row, no heading/trait/diagram changes. No canonical files were edited by this reviewer.

## Source fit of the new material

All 19 newly introduced source-citation occurrences resolve against 15 independently fresh wave7 raw source files matched to complete pinned Git trees. Twelve decisive files were already retrieved in this reviewer's current wave7 source/cross-review work; three more were freshly fetched for the final observer paragraph (native Reporter, native actor mailbox and actual Tempo Engine). This is current-wave raw/tree/blob evidence, not a reused historical inventory. Detailed receipts are in `global-review/receipt.json`; new raw files are under `global-review/sources/`.

- Body codec: native Write+EncodeSize → Encode, Read → Decode/Codec, Codec+Send+Sync → CodecShared blanket APIs are exact. Vec/Bytes read configurations and complete-frame `decode_cfg` remain distinct from aggregate body/work budgets. Buffer/Archive permit non-unit body configuration; generic resolver's unit outer config imposes no unit body schema. Native callbacks require commitments and native Context, not a Simplex Block/Application. Header codec/hash remain existing native identity; coherent body material/digest, authenticated header/body join and durable parent custody are preserved. The text chooses no hash, wire-byte hashing rule, encoding or bound.
- Observer composition: `Reporters::from((r1,r2))` and optional Reporter already exist, require the same Activity and call synchronously; nested Tempo composition is source-real. None returns Feedback::Ok; feedback is local submission, not processed/durable delivery. Existing actor mailbox overflow is message-Policy-owned and ready capacity alone does not bound retained overflow. The new paragraph keeps opportunistic body/header intake separate from exact Orderer evidence export and creates no event bus, actor, schema converter, retry service, durable outcome path or approval gate.
- QMDB handles: child drafts strongly retain immediate sealed parents; sealed object links are Weak. Lower retained ancestor data for apply does not guarantee every original object remains alive for subsequent get/fork/hash. “Still-needed unapplied ancestor” preserves selected ownership/retention rather than adopting a keep-all-forever rule. Public bounds remain storage commitment projections, not executed-order parents/provenance. Current canonical root differs from ops-only bounds root. Exact execution-context association, concrete DB applicability checking, shared access fence and Storage's physical retention stay distinct; no rootless public fork/tree API or automatic branch GC is claimed.
- Static selection: Reth public filter wrapper invokes dependency control while base iterator invalidation is local to that iterator, not shared pool removal. Dropping a predecessor through an ordinary filter does not preserve the same dependency control; count limits after filtering bound yields, not visits/analysis. Nunchi count truncation precedes the external filter; rotated lane starts are not same-lane pagination. Its underfilled bounded overlay is conditional, and any before-truncation connection belongs in the existing Pending kernel with contract/limits open. Constantinople whole-batch pop and lane-head byte rule require material retention/reconciliation after exclusion. Tempo's body-side immutable payment/size checks are an actual composition example; state-aware wrappers/execution builder are not adopted.

Prior independent reports/reviews remain consistent: own BODY_CODEC_CROSS_REVIEW and EXECUTION_TREE_CROSS_REVIEW bind report hashes `2e2dacda99f22abad89bb1e1741c1a449419961e9188feb4428dab914cfa2255` and `83dede50fa097a80c325b968419949c1e1618c8ff5c86741bb759c98798d2bfc`; storage agent independently reviewed static-selection report `201b6888c89eb24fc73f9325226c914b343e336f3b7f823edf8769821d79e8d8`. This final review additionally checks the adopted four-page prose as a whole, including the observer paragraph's fresh decisive source.

## Preservation and global reader constraints

A read-only comparison of every tracked docs Markdown file against baseline passes:

- All 32 Markdown files preserve exact ordered headings and explicit compatibility-anchor occurrences; all old external Markdown URL occurrences remain present with at least their prior multiplicity.
- Every Rust and Mermaid fenced block is unchanged. Canonical Rust page/export have five public traits (`TxPool`, `Orderer`, `Baton`, `Executor`, `Storage`) and 30 methods. No separate BlockService/new body/filter/tree trait, Runtime, Planner, ResultService, dispatcher or reconciliation actor is introduced.
- All 56 tracked non-Markdown docs assets match baseline byte-for-byte, including 18 rendered diagram families and the generated Rust export. No asset replacement or new retained policy/schema is implied.
- All 39 policy choices remain empty; transaction type/ID/analysis placement, backend, direct router versus packing overlay, producer selection order/work/count/bytes, outcomes/recovery and body/hash/storage/retention defaults remain open. Whole backend/source-port/native package-identity caveats remain intact.
- Four-page additions preserve the native git pin, no-wait cut/report/direction behavior and fixed report snapshot. They add no collector/observer/pool ACK requirement to native progress. Existing Orderer-to-Executor durable ACK and Executor-to-TxPool durable canonical outcome meanings remain intact.
- Executor execution-parent/context/tree/certification authority and Storage root/apply/durability ownership remain separate. Root deferral is preserved; QMDB sealed forks/public storage bounds do not replace unsealed-prefix read/replay or exact execution ancestry. No f+1 quorum/provenance/root-before-own-sign/verified-material-before-stop rule changes; optional observers do not relay or gate certification/state sync/canonical apply.

Read-only `python3 assets/tooling/check_docs.py --migration` passes: 31 content pages, 257 local links, 18 diagrams, 39 blank choices, zero failures. This validates documentation navigation/export/asset consistency only; no protocol/build/native test was run.

## Remaining limits

Native/application source adaptation and compatibility are uncompiled. Body schema/digest/domain/limits/custody contracts, pure policy semantics and bounded work, canonical pool readiness/restart, rootless branching, exact witness export and native prefix-preservation proofs remain open. These constraints are retained rather than filled by the editorial additions. If any of the four hashes changes, this exact review receipt no longer binds that page revision.
'''
(b/'DOCS_GLOBAL_REVIEW.md').write_text(report)
compact={'reviewer':'/root/reuse_orderer_v3','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':base,'result':'pass_no_actionable_corrections','page_hashes':pages,'markdown_pages_preserved':32,'non_md_docs_assets_unchanged':56,'traits':r['public_traits'],'methods':r['method_count'],'blank_choices':39,'new_citation_occurrences':19,'fresh_blob_matched_sources_for_new_citations':15,'additional_raw_fetches':3,'docs_check':r['docs_check'],'detailed_receipt_sha256':hashlib.sha256((b/'global-review/receipt.json').read_bytes()).hexdigest(),'report_sha256':hashlib.sha256((b/'DOCS_GLOBAL_REVIEW.md').read_bytes()).hexdigest(),'canonical_edits':False,'implementation_compilation_native_tests':False,'six_hour_completion_claim':False}
(b/'DOCS_GLOBAL_REVIEW_RECEIPT.json').write_text(json.dumps(compact,indent=2)+'\n');print(json.dumps({'report':compact['report_sha256'],'compact_receipt':hashlib.sha256((b/'DOCS_GLOBAL_REVIEW_RECEIPT.json').read_bytes()).hexdigest(),'detailed_receipt':compact['detailed_receipt_sha256'],'page_hashes':pages},indent=2))
