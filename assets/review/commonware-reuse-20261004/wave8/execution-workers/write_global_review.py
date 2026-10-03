from pathlib import Path
import hashlib,json,datetime
b=Path(__file__).parent;root=b.parents[4];r=json.loads((b/'global-review/receipt.json').read_text());pages=r['page_hashes'];base=r['baseline']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert set(r['changed_docs'])==set(pages)
for p,h in pages.items():assert digest(root/p)==h,p+' changed during review'
for x in r['fresh_matched_source_files_for_new_citations']:
 v=Path(x['local']).read_bytes();assert digest(Path(x['local']))==x['sha256'];assert hashlib.sha1(f'blob {len(v)}\0'.encode()+v).hexdigest()==x['tree_blob']
text=f'''# Wave 8 final global reader and preservation review

Reviewer `/root/reuse_orderer_v3`; baseline `{base}`. **Pass: no actionable correction or publication blocker found in this four-page documentation diff.** The exact page hashes below bind this review. This verifies reader/source fit and preservation; it is not a compiled integration, protocol proof, publication confirmation or completion of the six-hour research goal.

## Exact reviewed pages

| Canonical page | SHA-256 |
|---|---|
'''+''.join(f'| `{p}` | `{h}` |\n' for p,h in pages.items())+'''
Exactly these four tracked docs pages differ from baseline, with ten inserted lines and one deleted/replaced table row. No canonical file was edited by this reviewer.

## Source fit of introduced prose

All 15 new source-citation occurrences were checked against 12 independently fresh primary files, blob-matched to authenticated complete pinned native/Tempo trees in this reviewer's current-wave work. Ten files were already freshly retrieved by this reviewer for worker research and independent body/query review; the acknowledgement implementation and private pending tracker were additionally retrieved for this global pass. Every new anchor is within the matched source and its line text is saved. `global-review/receipt.json` binds all evidence. Explicit release corroboration remains version-labeled in the source reports; it does not merge the native graph with registry package identities.

- Incoming bodies: Engine wraps raw channels with selected body codec, performs full-frame decode, computes digest, and notifies digest subscribers. Public subscribe is cache-hit-or-wait inside the existing owner, without polling or a new stream actor. Waiters can receive before residency. Cache/subscription success does not prove expected header/context/parent or archive custody. Resolver delivers to Consumer, without automatic broadcast-cache insertion; direct verified material can reach the same owner. This paragraph adds no fetch policy, body hash/schema choice, peer readiness or body ACK barrier.
- Local delivery completion: public Exact handle/future semantics match the text. Every held clone must acknowledge; any unacknowledged drop cancels the waiter. Token has no range/result, network receipt, certificate, timeout or durable replay. The native PendingAck/PendingAcks owner is pub(super), and Tempo uses an existing per-block handle after its own forkchoice/canonical check. The adopted paragraph explicitly retains immutable range/durable CommitResult verification, cancellation as pending/recoverable, and optional Baton observation outside the mandatory predicate. Numeric height or all-clones completion is not substituted for exact durable range identity or f+1. Existing context-bound oneshot remains sufficient and no additional ACK engine is required.
- Worker helpers: native OptionFuture(None) remains Pending; Some completion is retained and must be cleared/replaced by its owner. Strategizer creates its Rayon strategy from the runtime-owned worker context. Handle cancellation distinguishes spawned tasks from completion waits; aborting a waiter does not preempt detached/spawned work or establish quiescence. Placement/parallelism/cancellation choices remain open. The table introduces no public Runtime/Planner/reschedule interface or manual work scheduler. Existing single canonical writer and active database access/fencing rules remain authoritative.
- State queries: Current variant/root remains conditional. Public per-key verifiers authenticate active value/current root, ordered exclusion uses existing authenticated span/empty-commit material, and public generation/codecs already exist. Same valid DB authority captures value/proof/root without a same-DB interleaved writer; multi-store checkpoint/readiness linkage remains Storage's contract. Local None and retained historical operation inclusion do not prove current absence. Proof/root is not f+1 execution certification, order/runtime validation, durability or own execution provenance. Existing Reader guards are not arbitrary historical snapshots. No backend, additional speculative root, proof format, HTTP endpoint or query actor is adopted.

Independent peer report reviews also pass at the exact current hashes: body-receive `d94655809905c022262cf662aab72a5059de8c316447a138f7d2a80ec0b9a8d6` and state-query `fa3c6980e2c53c9ae2f7fee798d419653085c13588cfd29d14dd5224748e4885`. Those reviews independently retrieved 24 primary files/five complete trees and checked 59 report anchors; report/delta hashes are bound in CROSS_REVIEW_RECEIPT.json. The final global pass checks the adopted page prose as a whole and additionally fresh-checks the newly introduced ACK sources, rather than relying solely on peer approval.

## Preservation and ownership constraints

Read-only comparisons against baseline pass:

- All 32 tracked Markdown files preserve exact ordered headings and explicit compatibility anchors. All old external Markdown source URL occurrences remain, with at least their old multiplicity. All Rust and Mermaid fenced blocks are byte-identical.
- All 56 tracked non-Markdown docs assets remain byte-identical, including generated Rust export and rendered diagrams. The five public application traits remain TxPool, Orderer, Baton, Executor and Storage with exactly 30 methods. No new body/query/result/runtime/planner/ACK trait or helper actor is introduced.
- All 39 policy decision cells remain empty. Direct router versus packing overlay, immutable payload analysis semantics, backend/native source port/package identity, root/certificate/query shape, selection count/bytes/work, body codec/hash/custody, retention/recovery and worker choices remain unselected.
- The native pin, native n=5f+1 and unchanged tip/extension interpretation remain explicit. Exact dense input still stops at unresolved slots and distinguishes included versus irrevocably-empty; local ACK plumbing is not dense-order derivation, native voting, terminal witness reinterpretation or body release.
- Report-window snapshot/fixed deadline, bounded completed candidate search, original-report support, exact ENTIRE-prefix preservation and proposal policy binding are unchanged. No report/optimizer/timer/direction/observer/peer ACK wait is added to cut/native progress. The unimplemented prefix adoption/availability/sufficiency/view-recovery obligations remain open.
- Executor continues to own execution parent/path/tree selection, full result certification and normal-path peer state sync. Storage owns selected root/material/canonical apply/durability/physical retention/recovery. No full Stateful Application/actor or per-attempt mandatory Merkleization is adopted; existing sealed forks still do not establish root-deferred branching.
- Result certification still requires valid f+1 distinct eligible signatures over matching irrevocable exact input/base/runtime/result. DirectExecuted and ImportedVerified remain distinct; root preparation precedes own result signing. Stop unfinished execution only after certificate and applicable material verification. Canonical mutation/active access/fencing/quiescence must remain owned through safe completion, and durability requires recoverable state/output/cursor/provenance.
- Orderer sends exact ordered input directly to Executor and advances delivery only from a verified exact durable CommitResult. Outcomes go to TxPool; optional Baton observation does not gate certification, sync, canonical apply or delivery ACK. Cancellation cannot advance the delivery cursor by itself.

Read-only `python3 assets/tooling/check_docs.py --migration` passes: 31 content pages, 257 local links, 18 rendered diagrams, 39 blank policy cells and zero failures. This is documentation navigation/export/asset validation only. No compile, dependency change, runtime/native test, benchmark or implementation was performed.

## Remaining limits

The integration is source-audited and remains uncompiled. Rootless pending-parent access, native exact witness handoff/dense delivery, same-context prefix preservation, reliable canonical outcomes/restart, concrete body/custody and certified-query contracts, worker quiescence/cancellation/fencing and multi-store crash linkage still require selected integration contracts and validation. No proof closure or policy default is implied by public helper availability. Any change to one of the four bound page hashes requires a new review of that revision.
'''
(b/'DOCS_GLOBAL_REVIEW.md').write_text(text)
c={'reviewer':'/root/reuse_orderer_v3','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':base,'result':'pass_no_actionable_corrections','page_hashes':pages,'markdown_pages_preserved':32,'non_md_docs_assets_unchanged':56,'traits':r['public_traits'],'methods':r['method_count'],'blank_choices':39,'new_citation_occurrences':15,'fresh_blob_matched_sources_for_new_citations':12,'additional_raw_fetches':2,'docs_check':r['docs_check'],'detailed_receipt_sha256':digest(b/'global-review/receipt.json'),'report_sha256':digest(b/'DOCS_GLOBAL_REVIEW.md'),'canonical_edits':False,'implementation_compilation_native_tests':False,'publication_or_six_hour_completion_claim':False}
(b/'DOCS_GLOBAL_REVIEW_RECEIPT.json').write_text(json.dumps(c,indent=2)+'\n');print(json.dumps({'report':c['report_sha256'],'compact_receipt':digest(b/'DOCS_GLOBAL_REVIEW_RECEIPT.json'),'detailed_receipt':c['detailed_receipt_sha256'],'pages':pages},indent=2))
