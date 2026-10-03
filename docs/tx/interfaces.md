# Tx interfaces

**TxPool owns candidate lifecycle; TxPolicy owns payload-based classification.** Admission makes a transaction available for selection. A canonical result determines its eventual lifecycle update. The detailed contract keeps these events separate.

## Interface overview

Rust declarations: [TxPool](../overview/rust-interfaces.md#txpool) and [TxPolicy](../overview/rust-interfaces.md#txpolicy). The Rust interfaces page is the single source for these declarations. Arguments use the associated types shown below. Async methods return a Future whose output is `Result<SuccessType, Self::Error>`; synchronous policy methods return Result directly. The output column names SuccessType.

`Selection` identifies the native producer context and bounded selection limits. `Batch` is a set of candidates, not evidence of block inclusion or successful execution. `on_proposal` handles local build cancellation and reselection; `on_commit` handles lifecycle updates from durable canonical results. They do not share a deletion condition.

TxPolicy consumes static features extracted from payloads. Where and how `Decision` controls producer routing or packing filters remains undecided. Balance, nonce, and load lookups do not belong in static analysis. CPU budgets and worker placement for the two pure computations are separate decisions.

| Proposed interface | Caller → receiver | Input | Output / next action |
|---|---|---|---|
| `TxPool::admit` | Tx API / peer → tx layer | `Self::Tx`, `Self::Source` | `Self::Admission`; retained candidate |
| `TxPolicy::analyze` | TxPool admission / packing integration | `&Self::Tx`; configured analysis version | `Self::Features` |
| `TxPolicy::classify` | TxPool / inclusion integration | `&Self::Features` | `Self::Decision`; placement and policy undecided |
| `TxPool::select` | Producer adapter → pool | `Self::Selection`: producer context and limits | `Self::Batch`; candidate transactions |
| `TxPool::on_proposal` | Producer adapter → pool | `Self::ProposalOutcome`: local correlation and outcome | `()`; local lifecycle update, separate from canonical deletion |
| `TxPool::on_commit` | Executor → pool | `Self::CommitResult`: durable range and tx outcomes | `()`; canonical lifecycle update |

A tx ID identifies a transaction; an external body commitment identifies body content; the native header ID identifies the complete producer header, including epoch, chain, height, parent, and commitment. Adapters maintain the correspondence between selected bytes, body, authenticated header, and canonical outcomes. Attachment-local request correlation does not imply that a native private build ID is exposed in Context. Codec, identity, and duplicate semantics remain undecided. [Producer header identity](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L113).
