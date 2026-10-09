# Round 15 — Concrete QMDB branch and reader API

Read actual current QMDB and glue wrapper source against `docs/execution/qmdb.md`. This pass focuses on what handles/guards/batches actually preserve, not the durability audit already completed. No native code, diagrams or runtime tests changed. All event traces below are analytical.

## Confirmed reader overstatement and owned correction

The old table called `DatabaseSet::readers()` a “guarded retained-version read.” That overstates the API:

- `Reader<DB>` wraps `Shared<DB>`; `Reader::read()` acquires the shared cell's current read guard (`glue/src/stateful/db/mod.rs:210-223`). There is no target/version argument.
- Single-DB `readers()` clones the live Shared handle (`794-795`); tuple `readers()` does the same for each member (`1037-1038`). Creating the handles takes no version snapshot.
- A held guard stabilizes that database against mutation through the same Shared cell. Dropping it and later reacquiring can observe a newer applied DB. The handle alone does not retain the old state or make it durable.
- Independent tuple component guards do not establish atomic App state across databases. Tuple apply completes each member's own write lifecycle (`1041-1051`); a read or new-batch construction concurrent with partial tuple application can otherwise mix stages of that one apply.

Changed the table to current guarded access and added a short reader paragraph: handles are live, historical versions are not pinned, and App authority binds value/proof/root/applied identity coherently. At root's request, folded one sentence into the existing access-authority paragraph to exclude draft/query observation of a partially applied database set. These obligations can use App's existing canonical writer/access ownership; no snapshot/read-view service was introduced. Historical query retention remains open App work.

## API and scenario checks

| Concern | Concrete source behavior | Current design result |
|---|---|---|
| `new_batches()` versus `fork_batches()` | Single DB acquires a scoped read for `ManagedDb::new_batch`; tuple acquires component reads, builds batches, then releases guards (`db/mod.rs:781-787,1024-1030`). `fork_batches(parent)` uses sealed-parent `new_batch()` and needs no DB lock at construction. | Pass. A new draft starts at actual applied state; a pending-parent fork requires a sealed parent. Neither API lets App name an arbitrary old root and obtain that historical state. |
| Live DB fall-through | Wrapper docs explicitly say reads use applied state at read time (`db/any.rs:4-5`); both draft and sealed wrapper get/get_many reacquire Shared (`106-117,364-375`). Low-level get_many resolves mutations/ancestor diffs, then reads the supplied DB (`storage/qmdb/any/batch.rs:1892-1943,2940-3004`). | Pass. App must preserve valid access ancestry across reads, child creation and hashing. Generation-based result rejection alone cannot prevent reading a sibling's applied state. |
| Guard scope | Raw `Reader::read()` holds one shared guard; wrapper batch get/merkleize independently reacquire that same DB (`any.rs:106-117,395-423`). Shared is writer-preferring (`db/mod.rs:148-152`). | Pass after reader correction. Do not hold a Shared guard and call a wrapper that reacquires the same cell across an await; an intervening queued writer can deadlock it. A raw DB read/proof through one guard is different from nested wrapper locking. |
| Strong/weak ancestor retention | Draft `Base::Child` holds immediate parent Arc (`any/batch.rs:204-214,2869-2877`); sealed batch parent is Weak (`341-358`), ancestor iteration ends when upgrade fails (`2838-2841`). Source explicitly requires unapplied ancestors alive through child/descendant merkleization (`2854-2858`) and proof material retention (`2880-2894`). | Pass, with wording narrowed to further branch reads/proofs/child merkleization. Keeping one leaf is not a universal substitute for needed ancestors. Already sealed apply also retains ancestor diffs, so the docs should not imply every old ancestor object must live forever merely to apply a leaf. |
| Branch from rootless AB | Concrete draft writes exist; generic `Unmerkleized` only exposes consuming merkleization, while `Merkleized` provides the child constructor (`db/mod.rs:296-324`). No unsealed-parent fork is provided by these handles. | Pass. The design's conditional recipe replays exact keyed effects into independent drafts from one valid applied/sealed anchor, or uses a concrete App overlay. An unavailable historical anchor cannot be reconstructed just by cloning a Shared handle. |
| Selected exact-prefix apply | Source says apply_batch applies its batch and unapplied ancestors (`any/batch.rs:323-329`). Applying sealed ABC commits ABC, not an App-selected visible subset. | Added one sentence making the complete-prefix effect explicit. Existing AB-only example correctly requires an exact AB batch/effects reconstruction; it cannot apply ABC and hide C. |
| Root determinism under batching | Writes in one draft are last-write-wins (`1748-1753`); each merkleization emits its CommitFloor metadata/operation (`1273-1289`) and carries a particular journal ancestry. | Pass. Same transaction order/final values need not imply the same QMDB operation history/root if arbitrary speculative batch boundaries differ. Canonical normalization/boundary/root rules remain open, and local speculative roots cannot be signed as automatically equal. |
| Native wrapper versus App semantics | Wrapper merkleization takes the current DB read guard and consumes its draft; `prepare` validates/retains the chain (`any.rs:395-423`; raw batch `1756-1816`). These operations know DB ancestry, not execution runtime, ordered-input identity or output journal. | Pass. App still binds execution state, outputs and selected canonical/signing boundary. Reusing glue DB utilities does not require the full Stateful application actor. |

## Concrete counterexamples checked

**Reader is not a retained version.** Obtain reader at state A; release any guard; canonical writer applies B; acquire the reader's guard again. It now observes B. A result labeled “query at A” needs a real retained A representation or must be rejected/rebound under the App query contract. The corrected reader text no longer promises A.

**Tuple readers are not an App snapshot.** During a tuple apply, member 0 reaches B while member 1 still exposes A. A query or `new_batches()` that acquires those states cannot call the pair one coherent B (or A) checkpoint merely because each member was individually guarded. App's existing writer/access authority must exclude or detect that mixed-state observation before using it.

**Weak grandparent disappears.** Draft C strongly retains sealed parent B, but B only weakly refers to unapplied A. Drop the last strong A reference. The remaining C/B objects do not restore A's full branch-read/proof chain. Raw reads can fall through to the older applied DB, while later merkleization rejects an invalid missing chain. Retain needed ancestors rather than treating C's presence as proof the whole prefix is usable.

**Rootless replay must be state replay, not hidden reexecution.** If AB's retained keyed effects include `k=2` and its output/runtime/base binding, replay them into a draft at their actual valid anchor to materialize AB before C/D reads. Do not claim `AnyStaged::expand` sees values computed for earlier slots but not submitted to merkleize: the wrapper explicitly excludes that visibility (`any.rs:242-247`). If effects/base are absent, the existing design falls back to reexecution. Read-your-writes behavior of an App overlay remains an integration choice.

**One batch versus two.** On the same initial state, writing `k=1` then `k=2` inside one draft leaves one keyed mutation. Sealing between those writes records separate operation/batch boundaries. Final key values can match while commitments differ. This is a source-derived reason to define deterministic selected boundaries, not an executed root-comparison test or a chosen per-block hashing policy.

**Only ABC is sealed, only AB is confirmed.** A sealed-leaf apply can include ancestors; it cannot omit the leaf's C effects. Exact AB needs retained material or reexecution. A newly normalized AB batch may also differ from the speculative AB parent used for old C, so logical input-prefix equality alone does not authorize reusing that C's concrete batch. Current prose preserves both execution and actual QMDB ancestry checks.

## Changes and limits

Minimal owned `docs/execution/qmdb.md` changes:

1. Correct current reader/guard semantics and multi-DB checkpoint limitation, with a direct source link to Reader.
2. Keep draft creation and queries within the existing access authority so they do not observe a partially applied database set.
3. Qualify leaf-only retention limits by operations that actually need ancestor objects.
4. State that applying a sealed leaf also applies unapplied ancestors.

No variant, overlay representation, root scheme, operation normalization, checkpoint cadence, historical query policy or public interface was selected. No diagram changed. Scoped `git diff --check` passed; root owns final link/build verification. Source compatibility/behavior was inspected, but no App implementation or runtime branch proof is claimed.
