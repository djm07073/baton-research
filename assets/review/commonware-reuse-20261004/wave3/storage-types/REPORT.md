# Wave 3: concrete Executor / Storage batch wiring

This independent source investigation reviews canonical HEAD `3c5ec96c91883dae892ee99832dee315c789eaee` after GitBook revision `NY491pkJQdX6ny2Lyndj`. The [document manifest](doc-manifest.json) identifies the nine reviewed current pages; [source manifest](source-manifest.json) records fresh upstream retrievals. Native source remains `534af0ede48affd35b2111522527547b4cc9bf72`; the comparison is `v2026.9.0`. The six-hour goal remains active.

**Verdict: the responsibility split works with public QMDB types without `stateful::Application` or a Stateful actor. The remaining interface detail is how Executor receives valid branch access, and how completed unsealed effects are retained when preparing them consumes the draft.** Existing types already implement the straight-line read/write/seal/apply path. They do not provide a production generic keyed-access trait or rootless multi-child draft tree.

No canonical docs, generated assets, external checkout, protocol implementation, dependencies or published material were changed by this reviewer. The accompanying type sketch is source-derived, not compiled against Commonware and not an adopted schema.

## Actionable refinements for the current docs

| Detail to add | Existing primitive to reuse | Application seam that remains |
|---|---|---|
| Show the input state handle consumed by `Executor::execute` internally | `DatabaseSet::new_batches` at applied base; `fork_batches` at a sealed parent; concrete `AnyUnmerkleized` / `CurrentUnmerkleized` reads/writes | Authorized base/parent access and clone-wide validity permit; do not use canonical `Storage::read` as a pending-parent reader |
| Distinguish a single DB from a tuple DB set in a type recipe | `<DB as ManagedDb<E>>::Unmerkleized` / `Merkleized`; `Shared<DB>` implements `DatabaseSet<E>` | Dispatch per-DB merkleize for tuples and construct the selected commitment; no tuple-wide upstream seal/root |
| State the reverse associated-type equality in generic preparation code | Actual Any/Current implementations return their matching sealed type | A generic helper additionally needs `DB::Unmerkleized: Unmerkleized<Merkleized = DB::Merkleized>` |
| Mark unsealed/staged handles as one-shot outputs | Upstream consumes `self` for write/stage/merkleize; sealed wrappers cheaply clone `Arc` plus matching Shared handle | Retain exact prefix effects separately if the same rootless completed prefix must support multiple children or preparations |
| Reject incompatible prepared material before taking canonical DB ownership | Concrete Any/Current `Db::validate_batch(&batch)` | Keep preflight and mutation under the same canonical authority; uphold exact order/base/runtime/rule/provenance checks too |

These refinements need not add a sixth application trait or a public Storage method. A concrete Storage attachment can supply internal authorized batch/access handles while the existing five public application traits remain stable. If the project later wants backend-generic execution, a narrow application read/write view is an adapter choice, not an existing upstream trait to claim as reused.

## Public imports and concrete type compatibility

Native public imports exist through `commonware_glue::stateful::db`:

```rust,ignore
use commonware_glue::stateful::db::{
    Barrier, DatabaseSet, ManagedDb, Merkleized, Reader, Shared, Unmerkleized,
};
use commonware_glue::stateful::db::any::{AnyMerkleized, AnyStaged, AnyUnmerkleized};
use commonware_glue::stateful::db::current::{
    CurrentMerkleized, CurrentStaged, CurrentUnmerkleized,
};
```

[Glue exports](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/lib.rs#L8) expose `stateful`, and [stateful](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/mod.rs#L106) exposes `db`; [db modules](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L106) expose `any` and `current`. This uses glue's database utilities, without implementing its `Application<E>` or constructing its actor. It still introduces the ordinary `commonware-glue` crate dependencies; independence from the Application trait does not mean importing a separate storage-only crate. The upstream glue module is labelled ALPHA.

The raw alternative exists in `commonware_storage::qmdb::{any,current}::batch`: native Any `UnmerkleizedBatch<F,H,U,S>`, `Staged<F,H,U,S>`, and `MerkleizedBatch<F,D,U,S>`; Current adds its const bitmap chunk parameter `N` and requires a graftable family. Raw keyed get/merkleize accepts a matching concrete `&Db`. Glue's wrappers already retain `Shared<Db>` and reacquire it for those calls. **Prefer the wrapper where its DB variant is supported, rather than writing another generic shared-DB batch wrapper.** Source: [Any raw types](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L263), [Current raw types](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/current/batch.rs#L260), [Any wrapper](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/any.rs#L53).

Use the actual `ManagedDb<E>` projection to avoid duplicating its long family/journal/index/update type list. For a supported concrete `DB` and runtime `E`, the single-DB draft is `DB::Unmerkleized` and the sealed output is `DB::Merkleized`. The production [Any unordered fixed alias](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/unordered/fixed.rs#L24) is `Db<F,E,K,V,H,T,S>`; [glue's matching implementation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/any.rs#L485) supplies `AnyUnmerkleized` / `AnyMerkleized`. This is an illustrative compatible choice, not adoption of Any, unordered keys or fixed values. Variable-value and ordered choices have different journal/index/value bounds.

### Generic lifecycle traits are not generic execution access

Exact native declarations:

```rust,ignore
pub trait Unmerkleized: Sized + Send {
    type Merkleized: Merkleized;
    type Error: Send;
    fn merkleize(self)
        -> impl Future<Output = Result<Self::Merkleized, Self::Error>> + Send;
}
pub trait Merkleized: Sized + Send + Sync {
    type Digest: Digest;
    type Unmerkleized: Unmerkleized;
    fn root(&self) -> Self::Digest;
    fn new_batch(&self) -> Self::Unmerkleized;
}
// Excerpt from ManagedDb<E>:
type Unmerkleized: Unmerkleized;
type Merkleized: Clone + Merkleized<Unmerkleized = Self::Unmerkleized>;
// Excerpt from DatabaseSet<E>:
type Unmerkleized: Send;
type Merkleized: Clone + Send + Sync;
```

[Native traits](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L291) and [release traits](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/mod.rs#L295) have these bounds. `Unmerkleized` supplies no `get`, `write`, key or value associated types. `DatabaseSet::Unmerkleized` may be a tuple and need not implement `Unmerkleized` at all. Also, ManagedDb constrains sealed-to-unsealed equality, but not the reverse unsealed-to-sealed equality. Actual supported Any/Current implementations satisfy it; a fully generic adapter must state it explicitly if its return type is `DB::Merkleized`. [The sketch](assembly-sketch.rs.txt) shows that additional bound. It does not cast an arbitrary set output to a single batch.

Do not select `commonware_storage::qmdb::any::traits` as a ready production keyed abstraction: [the module is gated](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/mod.rs#L96) behind tests / `test-traits`, and [the variant implementation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/unordered/mod.rs#L65) has the same gate. This is a test trait facility, not the normal execution seam. Native variant `sync` implementation modules are `pub(crate)` too; public `StateSyncDb::sync_db` or the generic public sync engine remain the external entries.

## Minimal actual assembly

1. Storage opens the chosen concrete DB or DB tuple and retains upstream `Shared` handles beneath one application authority. [`Shared<DB>: DatabaseSet<E>`](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L726) already supplies the single-DB lifecycle. Keep raw Shared mutation handles within the canonical writer boundary; executor workers should receive branch access, not unrestricted writers.
2. For an applied canonical base, Storage obtains `set.new_batches().await` while its authority validates the exact base and readiness. For a sealed pending parent, use `DatabaseSet::fork_batches(&parent)` or `Merkleized::new_batch`; no additional read-through tree is needed for that case. The construction releases its upstream read guard before returning. [`BatchContext` fields](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs#L256) are private and `Shared::read_locked` is private: external code should not try to manually construct this capability from a read guard. The public set entry already creates it correctly.
3. Executor receives that authorized branch handle internally and computes transactions through concrete `get`, `get_many`, `write`, or staged access. This is where the current opaque contracts need an explanation: `Storage::read` addresses canonical queries; it does not read an unsealed parent branch. Keep exact input/base/runtime, access validity, outputs and direct execution evidence with the attempt. No root computation is necessary between straight-line transaction updates.
4. Executor returns completed changes and outputs. At the selected deterministic boundary, Storage consumes the draft into a sealed batch, computes the chosen commitment and preserves the application binding. A single wrapper uses `Unmerkleized::merkleize`; a tuple requires calls to each concrete component. Executor signs only this prepared commitment and only with its own direct evidence. Upstream sealing alone does not confer execution provenance or certify the order.
5. Before canonical by-value mutation, Storage uses existing concrete `validate_batch` while the same canonical authority prevents a sibling advance between preflight and use. Native Any/Current validate actual authenticated ancestry and floors. It does not check application exact range/runtime/output provenance. Perform both classes of check.
6. Native pin: `set.finalize(sealed).await` applies and returns `Barrier`; observe `durable().await`. Release: `set.apply(sealed).await` then `set.finalize().await`, then observe its barrier. Only after successful durability plus recoverable state/output/cursor/provenance linkage does Executor emit its delivery ACK and TxPool outcome. Direct local application need not wait for peer certificate collection; imported application needs a verified full-subject certificate and applicable material first.

The recipe neither calls `Application::{propose,verify,apply}` nor creates a full Stateful actor. Transaction semantics remain Executor code; indexing/Merkle/apply/sync algorithms remain upstream.

### Exact keyed wrapper signatures

These are existing inherent Any wrapper methods, not proposed Baton traits:

```rust,ignore
pub async fn get(&self, key: &U::Key) -> Result<Option<U::Value>, Error<F>>;
pub async fn get_many(&self, keys: &[&U::Key])
    -> Result<Vec<Option<U::Value>>, Error<F>>;
pub fn write(self, key: U::Key, value: Option<U::Value>) -> Self;
pub async fn stage(self, keys: &[&U::Key])
    -> Result<(Vec<Option<U::Value>>, AnyStaged<F,E,C,I,H,U,S>), Error<F>>;
```

Source: [native](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/any.rs#L110), [release](https://github.com/commonwarexyz/monorepo/blob/v2026.9.0/glue/src/stateful/db/any.rs#L110). The actual `write` implementation spells `mut self`, reflecting its owned builder semantics. Current supplies the analogous inherent methods in its wrapper. Reads combine pending mutations, sealed ancestors and applied DB; they do not freeze a historical DB independently. `Reader<DB>::read()` dereferences to the applied DB and has no pending branch overlay.

## Draft ownership and the truly new rootless adapter

`AnyUnmerkleized`, `AnyStaged`, raw `UnmerkleizedBatch` and `Staged` have no Clone implementation at either inspected revision. Their batch fields and pending mutation maps are private. Raw `into_parts` is private, not an application delta extraction API. Merkleize consumes them; stage consumes the unsealed handle and its returned staged handle remains tied to that same batch. Thus an opaque `ExecutionResult` may own a one-shot upstream batch, but cannot promise arbitrary AB prefix extraction or copying that rootless AB into both ABC and ABD merely by retaining a reference.

Existing sealed wrappers do implement cheap Clone: [`AnyMerkleized::clone`](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/any.rs#L174) clones the inner Arc and matching Shared handle. This directly satisfies the proposed `PreparedResult: Clone` material component. Keep a small application binding/provenance/output wrapper around it; do not copy a second database or rewrite a sealed batch representation.

For rootless retained multi-block work, the remaining adapter is precise: retain an execution effects chain / working key overlay rooted at an authorized valid storage base; answer child reads from its own changes then the base; retain exact selected-prefix output/provenance; later materialize that selected prefix into a new upstream batch under the deterministic storage rule. Neither upstream stage expansion nor a canonical Reader substitutes for that overlay. `AnyStaged::expand` preserves staged indices, does not deduplicate prior keys, and cannot see values only computed in the caller. Staged preparation may still reduce resolution work in a straight-line attempt; its optimization is reusable without adopting a rootless tree implementation.

If AB is prepared by consuming the only one-shot draft, retaining that same draft afterward is impossible. Either retain the required application effects beforehand, retain and fork the resulting sealed AB, or reexecute missing exact effects. This clarifies existing open choices; it selects no checkpoint/signing/storage-root policy. Preparing new AB does not automatically reconnect an old sealed ABC whose actual storage ancestry differs.

## Existing preflight protects by-value DB ownership

Native Any:

```rust,ignore
pub fn validate_batch(&self, batch: &MerkleizedBatch<F,H::Digest,U,S>)
    -> Result<(), crate::qmdb::Error<F>>;
pub async fn apply_batch(self, batch: Arc<MerkleizedBatch<F,H::Digest,U,S>>)
    -> Result<(Self, Range<Location<F>>), crate::qmdb::Error<F>>;
```

[Any validation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L2733) is side-effect-free; [apply](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/any/batch.rs#L2763) repeats it after consuming the DB. [Current](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/current/db.rs#L776) exposes the equivalent preflight delegating to Any. Both exist in the release too. Glue sealed wrappers Deref to their raw sealed batch, allowing concrete preflight without fabricating a new changeset type. Glue finalization consumes the DB and applies `batch.inner` directly.

Do not retain an outer upstream read guard and invoke wrapper get/merkleize: they reacquire the writer-preferring Shared lock. The application authority may span validation/use without recursively holding the same upstream read guard. Preflight cannot make a stale branch safe if an uncontrolled clone mutates after the check; it is part of the common fencing/writer contract, not a substitute.

One upstream ManagedDb rustdoc sentence describes producing a `Changeset` through `merkleized.finalize()`, but the inspected native Any implementation actually passes `batch.inner` to `apply_batch` then `start_sync`. No public Any `Changeset` type or batch-finalize extraction method appears in these batch files. Treat “change set” as the conceptual application output unless a chosen concrete API supplies one; cite implementation rather than copying that stale rustdoc sentence into an exact recipe.

## Receipts and limits

Fresh retrieval produced 38 successful raw files plus two HTTP 404 guesses (`any/operation/update.rs` at each revision), recorded as failures rather than evidence. Three explicit v2026.9.0 Commonware library MCP get_file responses were checked for actual Rust content and retained. Every successful raw receipt has SHA-256 and HTTP metadata; exact line citations above use its pinned/release source.

This is source and type-shape review. It did not compile Commonware, implement a selected backend, test a protocol or verify a concrete Executor/Storage implementation. Standalone generated Baton interface syntax checks do not establish these upstream associated-type, visibility or keyed-access constraints. A future authorized integration compilation must use one coherent dependency revision, concrete variant types and the exact equality/bounds above. All 39 policy cells stay unselected; result provenance, root-before-sign, native no-wait, canonical fencing and durability linkage stay in force.
