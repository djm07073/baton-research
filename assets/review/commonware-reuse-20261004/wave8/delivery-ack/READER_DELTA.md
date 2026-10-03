# Proposed reader delta

In `docs/consensus/ordered-input.md`, after the existing Journal/Metadata atomicity paragraph, explain local completion-handle reuse without changing public traits:

**Reuse existing local completion handles when delivery needs a waiter.** `commonware_utils::acknowledgement::Exact` supplies a handle/future pair, as used between Tempo's Marshal and Executor. Associate it with the immutable range and signal only after verifying that range's durable CommitResult. All cloned handles must acknowledge; dropping an unacknowledged clone cancels the waiter. The token alone carries no range/result or durable replay. Keep optional Baton observation outside this completion condition; cancellation leaves delivery pending/recoverable rather than advancing a cursor. The Simplex Marshal's pending-ack tracker is private, so copy the ownership pattern around public handles, not that tracker. Existing context-bound oneshot plumbing is also sufficient; no extra waiter or ACK engine is mandatory.

Cite native utils acknowledgement trait/drop, actual Tempo executor completion and private Marshal tracker. No new heading, public trait/signature, schema, quorum, policy choice or native progress wait.
