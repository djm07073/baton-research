from pathlib import Path
import hashlib,json,re,datetime
b=Path(__file__).parent;m=json.loads((b/'source-manifest.json').read_text());pins=m['pins']
def link(tag,path,line,label):
 r,p=pins[tag];return f'[{label}](https://github.com/{r}/blob/{p}/{path}#L{line})'
r=lambda p,l,s:link('reth',p,l,s)
n=lambda p,l,s:link('nunchi',p,l,s)
c=lambda p,l,s:link('constantinople',p,l,s)
t=lambda p,l,s:link('tempo',p,l,s)
a=lambda p,l,s:link('native',p,l,s)
report=f'''# Wave 7 — retain the pool, filter during body selection

## Outcome and scope

The user's packing-overlay alternative is feasible without a second admission/dedup/gossip/nonce/status actor. The strongest newly verified public hook is Reth's `BestTransactions::filter_transactions`: it composes a predicate with the existing dependency-aware iterator. Nunchi supports an external overlay over non-destructively cloned candidates, but does not expose filtering before its count truncation. Constantinople destructively pops whole batches, so filtering its returned vector alone does not preserve rejected/canceled candidates. These are conditional reuse routes; neither backend nor admission-router versus packing-overlay placement is chosen.

Source audit only against baseline `f2973dd98598eddac73d212c2b78e04cefb311c8`. Thirty-four freshly retrieved source files were checked against five authenticated, complete, non-truncated pinned Git trees. Manifest records raw URL, byte hash and matching Git blob SHA-1. No protocol implementation, dependency change, compilation, native test or integration proof. Native remains `{pins['native'][1]}`. Historical review manifests were not used as fresh retrieval evidence.

## Existing selection hooks and precise limits

| Source | Keep unchanged where compatible | Small connection still needed |
|---|---|---|
| Nunchi SDK | Existing actor/handle, admission checks, digest/status maps, lane readiness, maintenance and optional P2P; `pending(limit)` clones ordered ready candidates | Analyze/classify immutable payload copies, pack exact body bytes and preserve dependencies. Filtering before count truncation or continuation requires localized adaptation of existing Pending message/kernel, if that contract is selected |
| Reth | Full Ethereum-compatible pool and maintenance; public best iterator and predicate wrapper | Payload-only feature projection/policy; chosen producer context, complete body packing and any analysis-work bound. Keep iterator exclusions distinct from canonical removal |
| Constantinople | Existing admission/dedup/status owner and byte-limited lane machinery, if fixed workload/source graph fits | Proposal pop is destructive: retain/reconcile returned material or adapt existing selection path to inspect before pop. Rejected policy candidates cannot be recovered from digest-only tracking |

### Reth: a public predicate, with dependency-aware local exclusion

{r('crates/transaction-pool/src/traits.rs',399,'TransactionPool::best_transactions')} returns a boxed best-transactions iterator; {r('crates/transaction-pool/src/traits.rs',1189,'the Box implementation')} delegates selection controls. {r('crates/transaction-pool/src/traits.rs',1175,'filter_transactions')} accepts `FnMut(&Item) -> bool` and returns public `BestTransactionFilter`; its constructor is {r('crates/transaction-pool/src/pool/best.rs',318,'also public')} and {r('crates/transaction-pool/src/pool/mod.rs',113,'reexported')}. No new generic filter/selector trait or actor is needed merely to apply a static producer predicate.

The wrapper's {r('crates/transaction-pool/src/pool/best.rs',337,'next loop')} calls the predicate, yields passing entries and invokes the underlying `mark_invalid` for false entries, using `TxTypeNotSupported` as its error kind. In the concrete base Reth iterator, {r('crates/transaction-pool/src/pool/best.rs',124,'mark_invalid')} only adds the sender to that iterator's invalid set. The iterator owns a copied candidate map; it does not remove transactions from the shared pool. Its {r('crates/transaction-pool/src/pool/best.rs',208,'next-candidate loop')} skips that sender and descendants. An ordinary Rust `.filter` after yielding is weaker: yielding already unlocks the successor; silently dropping the predecessor does not call this dependency control. A selected whole extension must be checked for its own `mark_invalid` semantics and error-kind interpretation; do not generalize base Reth internals to every implementation.

The predicate can call the proposed TxPool's payload-only `analyze`/`classify` hooks after projecting the transaction out of its validated-pool wrapper. Keep live account nonce, balance, fee validation and readiness in the existing backend. Those state fields are not static routing features. Configuration may choose policy; no policy, decision schema, tx format or default is supplied here.

`filter_transactions(...).take(N)` bounds passing/yielded entries, not visited/rejected entries or feature-analysis work: a single wrapper `next()` loops until a match/end. The iterator also performs dependency skips internally. With updates enabled it may receive new candidates while selecting. A chosen hard work limit cannot be inferred from a returned count; local bounded driving of the existing iterator is a possible integration route, without a new pool actor or promised algorithm. {r('crates/transaction-pool/src/pool/best.rs',283,'no_updates')} drops the new-admission receiver and last-priority marker. It does not freeze canonical provider state or certify candidates for a native parent.

Reth also has public {r('crates/transaction-pool/src/traits.rs',606,'get_pending_transactions_with_predicate')}, but this is a different query: {r('crates/transaction-pool/src/pool/txpool.rs',524,'its implementation')} filters/collects the pending by-ID walk under the pool read access, cloning Arc entries. It has no count/work limit and no dependency-invalidation operation. Filtering this vector can leave nonce gaps. It is useful inventory/query evidence, not a replacement for dependency-preserving proposal selection.

### Nunchi: count truncation occurs before the external overlay

{n('mempool/src/actor.rs',177,'MempoolHandle::pending(limit)')} sends an existing Pending message and returns cloned txs (empty on shutdown). The {n('mempool/src/actor.rs',403,'handler')} runs the private kernel selection synchronously before responding. There is no public predicate, scan cursor, native producer-parent context or byte-budget argument. {n('mempool/src/pool.rs',160,'Kernel pending')} clones contiguous ready nonce runs round-robin and mutates `ready_cursor` afterward. It is non-destructive, but not side-effect-free; repeated calls rotate lane start, not within-lane pagination.

An external packing overlay can analyze/classify returned txs, retain allowed candidates and build a smaller body. It cannot claim to have considered all eligible txs: in one lane, `pending(2)` repeatedly starts at the same committed nonce until state changes. If its first two candidates are excluded, a later payload does not become visible by repeating that limited call. This is source-derived truncation reasoning, not a fairness benchmark or mandate to scan everything. A later nonce may depend on excluded predecessors anyway, so revealing it does not establish eligibility. Underfilled bodies may be an intentional bounded-selection result; liveness/fairness and scan/packing policies remain choices.

If selection must filter before count truncation, adapt only the existing Pending Message/handle/handler and existing ready-lane walk to carry the selected bounded filter/continuation contract. Do not build another queue, pool or reconciliation actor. Whether this adaptation is necessary depends on the selected contract; unchanged `pending` suffices for a bounded post-selection overlay with the stated limitations. {n('mempool/src/tx.rs',32,'PoolTransaction')} offers immutable-payload-facing digest/nonce-key/nonce/encoded-size/verify accessors, but Clone/Send/Sync does not prohibit interior mutation. Stable selected encoding/identity and analysis version must agree; per-tx admission size is not whole-body size.

Pending response reflects the actor's processed selection instant, not an exposed canonical watermark. {n('mempool/src/actor.rs',195,'finalized')} uses lossy `try_send`, no processed ACK; {n('mempool/src/pool.rs',211,'finalize')} mutates nonce snapshots, height and TTL. Filtering does not fix lost notifications or restart hydration. Keep the already documented context-bound completion/replay connection in that actor's existing owner. A packed candidate is not canonical inclusion/execution; body filtering must not remove it or report a durable result. Imported certified outcomes follow the same durable Executor-to-pool lifecycle as direct ones; no pool ACK gates native cut or direction.

### Constantinople: filtering after pop needs material ownership

{c('crates/mempool/src/lib.rs',10,'TransactionSource')} is public but fixed to VerifiedTransaction and Simplex Marshal reporting. Its `propose(parent, round, filled)` feeds the {c('crates/mempool/src/webserver/actor.rs',829,'existing Propose handler')}. {c('crates/mempool/src/webserver/actor.rs',406,'pop_lane_proposal')} inspects the front whole batch, stops the lane if it does not fit the remaining encoded-tx-byte budget, pops accepted batches, and records only height/digests. {c('crates/mempool/src/webserver/actor.rs',437,'pop_proposal')} tries foreground then background. No partial-batch selection or search around a too-large lane head is implemented there. Encoded tx-byte sum excludes complete selected body framing.

Policy exclusions after this call have already left the pool; digest records do not retain rejected bytes. The smallest route is selected build-material retention/cancellation ownership or adapting that same selection path before pop, not a second pool. No unchanged public non-destructive peek/predicate/continuation API was found. Existing status completion must still map to durable Executor outcomes; proposal serving and static policy rejection are not canonical execution.

## Actual chain example and assembly boundary

Tempo assembles Reth/Tempo pool and network/maintenance in its existing node; it obtains best transactions through {t('crates/payload/builder/src/lib.rs',249,'pool selection')}. The {t('crates/payload/builder/src/lib.rs',590,'body builder')} classifies immutable payment transaction content for a local resource rule, and {t('crates/payload/builder/src/lib.rs',616,'checks encoded block size')} before continuing selection through `mark_invalid`. This demonstrates pool-preserving body-side classification and packing using an existing iterator. It does not adopt Tempo's payment quotas, gas rules, state-aware wrappers, timing policies or execution/merkleizing builder. Tempo's {t('crates/transaction-pool/src/best.rs',116,'merged iterator')} delegates exclusions to its protocol/AA backend; its {t('crates/transaction-pool/src/best.rs',139,'StateAwareBestTransactions')} is explicitly execution-dependent and is not static routing.

The chosen pool remains beneath TxPool::select. Native {a('consensus/src/lib.rs',146,'Automaton::propose')} is the body-build callback; the {a('consensus/src/multimmit/actors/voter/executor.rs',708,'native voter')} invokes it and awaits its receiver. Pack the selected candidate body, retain its bytes/identity and return the chosen digest through that callback; existing {a('consensus/src/lib.rs',243,'Relay::broadcast')} handles dissemination attachment. Proposal cancellation/bytes/canonical correlation remain the existing body connection, not a new public application trait. This source sequence does not fill the undecided body schema or custody policy.

Native workspace package versions are {a('Cargo.toml',63,'2026.7.0 at the git pin')}; Nunchi imports {n('Cargo.toml',61,'registry 2026.9.0')} and Constantinople {c('Cargo.toml',51,'a different Commonware git revision')}. Preserve the prior package-identity source-adaptation boundary. A public ecosystem selection hook does not prove unchanged native interoperability; no chain builder or Stateful Application is needed for the conditional pool overlay.

## Small reader delta

Only three clarifications add to the existing documentation: name Reth's public predicate and distinguish selection-only invalidation; explain Nunchi's pre-filter count truncation/rotating lane starts; show Tempo's body-side classification/size checks as composition evidence. Returned-count versus visited-analysis limits and Constantinople's destructive whole-batch head-of-line rule need a short caveat, not new infrastructure. See READER_DELTA.md. Preserve five traits, empty policy cells, no-wait cuts, backend choices and direct-router versus packing-overlay choice.
'''
(b/'REPORT.md').write_text(report)
delta=f'''# Proposed reader delta — not adopted edits

Baseline `f2973dd98598eddac73d212c2b78e04cefb311c8`. Keep existing headings, diagrams, interfaces and policy tables. No Rust declaration change is needed.

## docs/tx/interfaces.md

In the existing backend mapping select row, Reth's dependency-aware iterator can name `BestTransactions::filter_transactions`. One paragraph after that table is enough:

> For a packing overlay, Reth already exposes a predicate wrapper around its best iterator. Rejected entries invoke the iterator's dependency control; the base implementation excludes entries locally without deleting them from the pool. An ordinary filter after yielding a predecessor does not preserve this behavior. A returned-count limit after filtering does not bound visited candidates or static-analysis work. Keep analysis on immutable payload facts and connect the chosen body-byte/work limits without introducing another pool actor. {r('crates/transaction-pool/src/traits.rs',1175,'Public predicate')}, {r('crates/transaction-pool/src/pool/best.rs',337,'filter loop')}, {r('crates/transaction-pool/src/pool/best.rs',124,'base iterator exclusion')}.

## docs/tx/README.md

In the existing Nunchi paragraph describing pending/packing, add:

> `pending(limit)` truncates before a wrapper filters candidates. Repeated calls rotate ready-lane starts, rather than paging further into the same lane. A filtered limited prefix can therefore hide later entries until canonical or pool state changes; excluded nonce predecessors can also make their successors ineligible. Filtering before truncation, if required, belongs in the existing Pending message/kernel, with its contract and limits still undecided. {n('mempool/src/pool.rs',160,'Pending walk')}.

In the existing Constantinople destructive-selection paragraph, append its lane-head caveat: selection pops whole batches and stops a lane when its head exceeds remaining tx-byte budget; it does not search smaller later entries. Its existing retention/cancellation warning remains necessary. {c('crates/mempool/src/webserver/actor.rs',406,'Whole-batch pop')}.

One sentence near the existing Reth/Tempo comparison gives the real chain example: Tempo filters immutable payment content and checks encoded block size inside its existing body builder while retaining the pool/iterator composition; its state-aware wrappers and execution builder are not adopted. {t('crates/payload/builder/src/lib.rs',590,'Content classification')}, {t('crates/payload/builder/src/lib.rs',616,'Size filter')}.

## docs/reference/integration.md

Only if its existing pool assembly row needs the hook spelled out, name the selected Reth best iterator/predicate beside the existing complete-pool candidate. Do not add a new primitive/actor/trait row. Keep source-port compatibility, whole backend lifecycle and canonical refresh caveats. No new generic scan engine, cache, reconciliation actor, policy defaults, budgets or backend choice.
'''
(b/'READER_DELTA.md').write_text(delta)
entries={(x['repo'],x['pin'],x['path']):x for x in m['sources']};anchors=[]
for name in ['REPORT.md','READER_DELTA.md']:
 for repo,pin,p,line in re.findall(r'https://github.com/([^/]+/[^/]+)/blob/([0-9a-f]{40})/([^\s)#]+)#L(\d+)',(b/name).read_text()):
  x=entries[(repo,pin,p)];ls=Path(x['local']).read_text().splitlines();assert 1<=int(line)<=len(ls);anchors.append({'document':name,'repo':repo,'pin':pin,'path':p,'line':int(line),'line_text':ls[int(line)-1]})
root=b.parents[4];pages=['docs/tx/README.md','docs/tx/interfaces.md','docs/reference/integration.md','docs/overview/rust-interfaces.md'];receipt={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':'f2973dd98598eddac73d212c2b78e04cefb311c8','fresh_sources':len(m['sources']),'complete_trees':5,'anchors':anchors,'files':{n:hashlib.sha256((b/n).read_bytes()).hexdigest() for n in ['REPORT.md','READER_DELTA.md','source-manifest.json']},'reader_baseline_hashes':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in pages}}
(b/'review-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt['files'],indent=2));print(len(anchors),'checked anchors')
