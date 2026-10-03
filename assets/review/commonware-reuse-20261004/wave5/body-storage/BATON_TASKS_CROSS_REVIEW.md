# Independent cross-review: Baton runtime/task reuse

Reviewer `/root/reuse_network_v3`. Reviewed baton-tasks `REPORT.md` SHA-256 `b8112fc405dc958d421ee6bb041a07452329c5115246617958e3752a2cd3dfa6`. No canonical/foreign-report edits, implementation, build, strategy/placement choice or new gates.

**Pass for the proposed source-grounded reader delta. Existing primitives cover task/deadline/completion mechanisms; native Strategy::spawn alone does not prove nonblocking owner/cut execution, and future cancellation does not prove CPU/signing/storage quiescence.**

## Independent receipts and checks

The decisive native source files were freshly retrieved and independently matched to the fresh native `534af0ede48affd35b2111522527547b4cc9bf72` tree. [cross-review/source-manifest.json](cross-review/source-manifest.json) records those blobs, SHA-256 and line counts separately from the reviewed report's receipts.

| Report claim | Fresh source and inspection | Result |
|---|---|---|
| Clock current/sleep_until support one fixed deadline | runtime/src/lib.rs Clock lines428–447 | Pass. API provides SystemTime deadline sleep; the application must choose/freeze the deadline and process threshold/deadline closure once. No fairness, wall-clock total order or cutoff implementation is inferred. |
| Runtime Spawner places owned work; CPU should run in task body | runtime/src/lib.rs Spawner lines261–325; tokio/runtime.rs lines574–624 | Pass. Tokio invokes `f(self)` to construct the future on the caller before scheduling it. The report correctly warns against performing candidate work while constructing that future. Explicit task-body placement handles inline strategy cases; Shared(false) does not prove CPU isolation. |
| Sequential strategy does work before returning a future | parallel/src/lib.rs lines795–810 | Pass: `f(self.clone())` runs synchronously; merely pushing the returned future into a completion pool does not move work. |
| Rayon may also execute inline; receiver drop does not cancel submitted closure | parallel/src/lib.rs lines1007–1059 | Pass. At most one worker executes immediately. Multi-worker submission is independent, and pool-member polling can execute queued work inline. The closure discards failed response send; receiver cancellation cannot revoke the already-running closure. |
| Pool and AbortablePool are unordered/unbounded and require admission/correlation | utils/src/futures.rs lines16–160 | Pass. push has no capacity parameter. Pool clear drops pooled futures; Aborter drop triggers abort for its wrapped future. Neither is a preemptive CPU scheduler or automatic authority fence. |
| Handle abort cannot stop a synchronous closure mid-instruction | runtime/src/utils/handle.rs abort path and Abortable task runner | Pass as a limit, not an asserted observed race. Abort requests future cancellation; a non-yielding running poll must return before future machinery can observe it. No durability/quiescence guarantee is added. |
| select/loop priority is local processed-event order | macros/src/lib.rs lines45–80, generated loop shape lines163–181 | Pass. Biased branch order, shutdown first in select_loop. This does not make network observations, verification completion and snapshot admission the same event. |
| Feedback is endpoint handling/overflow feedback | actor/src/lib.rs lines13–30 | Pass. Backoff is handled by an overflow policy and accepted() includes it. It is not authentication, admission, remote delivery, planning completion or direction approval. |
| Native task permit/generation pattern is internal, not Baton authority | multimmit/actors/voter/executor.rs finish_task/shutdown_tasks, lines37–70; reserve/schedule lines479–545 | Pass. Reservation precedes retained crypto/verification work; stale-generation completions are discarded. Methods are internal and do not supply a public Baton policy hook. |

The reader delta must retain exact-context admission, one distinct identity, once-only snapshot closure and cut independence. Do not await capacity/window/evaluation, invent another direction reply collector, or infer bounded CPU/memory from these source shapes. The report already preserves those limits and leaves placement, priority and queue policies open.

## MCP response content independently validated

The saved wrappers were not treated as valid because they returned JSON. Their text was extracted and checked against independently fresh Git blob-verified release `d476a2361ce6840d2b9d0aa6fb30a924429046d4` files. Receipts are [cross-review/mcp-content-cross-check.json](cross-review/mcp-content-cross-check.json).

Both current snippets contain the expected Rust trait and match the release source exactly after accounting for **zero-based MCP line labels versus one-based GitHub anchors**: Clock61/61 lines and Strategy51/51 lines match at +1 offset. The numbered MCP lines must not be copied directly into GitHub anchors. The earlier `mcp-content-checks.json` I initially read described an older Clock response; use the actual reviewed response hashes in this independent receipt.

The release Strategy signature has `spawn(&self, len: usize, f)`, including adaptive inline/offload documentation; native Strategy has `spawn(&self, f)` with the checked Sequential/Rayon behavior. Release snippets corroborate the conceptual caveat but cannot replace native signatures or line anchors. The report correctly uses native sources for those claims. No material native-source correction is required.
