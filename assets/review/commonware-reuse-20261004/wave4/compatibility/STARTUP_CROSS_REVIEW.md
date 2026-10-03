# Independent startup/lifecycle cross-review

Reviewer: `/root/reuse_storage_types_v3`, wave4 compatibility role. Reviewed startup REPORT snapshot SHA-256 `9f82dd9f7efb7ffa87ea57af4cb85c72bc0f99d811fa1058d5ba3f02f9e3f295`. Native pin `534af0ede48affd35b2111522527547b4cc9bf72`, Tempo `61c979a524f9af5de9c540a0088c429a44741e4c`, Alto `1d87569348b5560699465a72d691d90f18affb9c`. Independent receipt paths/hashes are recorded in this role's [source-manifest.json](source-manifest.json).

## Outcome

**Scoped source/API fit passes.** The report's startup recommendations are consistent with directly inspected source; its strict join/signing-material quiescence limitation is appropriately qualified. No executed race, confirmed native bug, compiled assembly or finished canonical recovery proof is established. No blocking source correction is required before using these recommendations in reader pages.

## Exact checks

| Claim | Independent check | Assessment |
|---|---|---|
| Channel registration versus network binding | Native discovery Network::start L192–204 binds the router mailbox synchronously before spawn. Router ingress content L204–210 returns Feedback::Ok when unbound and never queues the content. | First actual outbound fetch/publication must follow binding. Initialization or an idle actor start need not wait for an invented readiness handshake. |
| Immutable local recovery | Native archive immutable storage L110–180 obtains committed Freezer checkpoint and ordinal sections from Metadata. Existing init handles replay; application identity/authentication is not part of this primitive. | Reuse archive recovery; retain exact custody/context partition semantics separately. |
| Archive custody completion | Immutable sync L293–315 waits for Freezer and Ordinal, then put_syncs committed Metadata checkpoint. Archive start_sync L141–153 covers accepted earlier writes, default completes sync before returning ready Handle and fatal Handle error invalidates archive. | A running task, successful init or abort/join does not supply the covering custody sync. No QMDB/state cursor atomicity is implied. |
| Pre-running native body verification | Engine start L700–746 awaits open_stores and recovered-payload Automaton verification before constructing child actors. Running is returned later. | Separate body resolver/custody callbacks must work during start; depending on returned Running or native resolver creates a cycle. Report keeps the genuine native recovery fence. |
| Startup readiness | Voter actor L913–930 seeds native resolver, submits initial producer wake, sends ready. Engine Readiness L514–525 retains Ready/Failed. | Ready is a remembered startup milestone, not a recurring health probe, body propagation/root/result-certificate completion or application durability. |
| Owned task lifetimes | Spawner mandatory supervision L287 onward; Handle::select L189–244 aborts owned group after first completion or future drop. | Existing runtime machinery suffices; cancellation must not be relabeled graceful storage flushing or automatic restart. |
| Global cooperative stop | Spawner::stop docs L323–354 and signal Guard/Signaler L125–160 show completion tied to held Signal references. | Does not prove arbitrary application storage flush; retain cleanup ownership and error/timeout behavior. |
| Strict Running::join postcondition | Engine L589–591 awaits root handle; root select L816–830 exits without explicitly joining remaining children; Handle L129 sends result before supervision abort L139. | Source alone does not prove every descendant future/signing capability has gone when join returns. Report says unproved source postcondition and no race claim; see independent limited check below. |
| Actual Tempo assembly | lib.rs L148 starts network before consensus-engine task; engine L524–588 starts peer manager/buffer/resolver bridge before Marshal/epoch and uses Handle::select. | Useful pattern, still release2026.9/Simplex/Reth-specific, not public native Multimmit helper types. |
| Actual Alto assembly | chain engine L465–495 starts buffer/Marshal/queued consumer before consensus; waits with try_join_all. Validator L349 starts network first. | Report correctly distinguishes all-success wait/early-error behavior from first-clean-exit selection despite source comment. |
| Safety-store recovery identity | Native Engine L306 onward restricts fresh path to never-active epoch key/new partition; Tempo alias L216–228 has deletion advice in error string. | Do not import Simplex deletion advice into native signing storage. Report preserves key/partition provenance and independent recovery obligations. |

Additional directly inspected resolver/voter cleanup and buffer start do not establish whole-application apply/flush. Shutdown integration still needs clone-wide writer fencing and durable state/order/provenance linkage. Neither native startup readiness nor public Inspector/Serve replaces those checks.

## Independent lifecycle receipt

[LIFECYCLE_CROSS_CHECK.md](LIFECYCLE_CROSS_CHECK.md) was written independently before this full startup report review; SHA-256 `ff45b8d5ebde1004cddd2a9839f6fd89570396e79954eb14e43ad16722cd2ecb`. It uses independently fetched native engine and Handle bytes and does not assert a confirmed race.

## Extra fresh sources for this review

These nine files were independently retrieved rather than inferred from the startup inventory; all match fresh complete repository-tree Git blobs. Other checks above use this role's earlier independent wave4 source receipts for the same exact pins.

| Local source suffix | SHA-256 | Git blob |
|---|---|---|
| `native/p2p/src/authenticated/router/ingress.rs` | `3fa0dc6a91d27c90fde14ccff5a647d80e3a5499ae22a7fad84af1e30d6a5544` | `4f101375e7f61d21595ee16b529c29829536191d` |
| `native/storage/src/archive/mod.rs` | `cbd060766dafdcee549826b92529bb0a865f56e04c6e9db7d1b50ba9ebe58877` | `51cec09eace51b01c1b313090007579a38f5dc2b` |
| `native/storage/src/archive/immutable/storage.rs` | `a92d48f6e9ae4c6bb150aff6a3e9b80f9fae27ca3240f572727180e4b5d63b1e` | `ce3f72708b986503f939e2c385f30956c01a29c9` |
| `native/consensus/src/multimmit/actors/voter/actor.rs` | `7dc0b0fd04eb3706d6dc4a3873ae5615c2356d859a5102f998e7949c670036bc` | `f2850e31a9cfaad56779665d62816a4c8e902344` |
| `native/consensus/src/multimmit/actors/voter/executor.rs` | `780e2723d917711ef7800a20de1aadd79048d32904ce38bcf2463994115aacea` | `4e38fbb0b91c9368906ff40a01b39734630720ec` |
| `native/runtime/src/utils/signal.rs` | `30349b19075c0e7fe5367fda27bdef75980caf81beb2e30c915841af917b24fb` | `91f0c4979399f902b5e9281fb9bd047af6c0c651` |
| `native/runtime/src/utils/supervision.rs` | `8b534c8f374c33bab1861dcda9d7f8d8b60c3785182b5b35406f66ffa5b9eac0` | `e2f8c10222be0765f3974a2e7218632b76844241` |
| `tempo/crates/consensus/src/lib.rs` | `d09cb17ecedce40656a4d752748204fcba8077f61fabebfc6a0e981697b7fabc` | `d9af8a0cfd422094357b6878d487043e6900fbdb` |
| `tempo/crates/consensus/src/alias.rs` | `3cab895e0f42a507f6a9e93c9edfbada3c95c8d05a9053916777e93ebe587aa0` | `0d7d2179201396b80b9be76554404f3afd57fd8a` |

No native protocol compilation/tests, external checkout edits or dependency changes were performed. Recommended reader edits can preserve five public application traits and existing signature/policy choices. This is source fit only.

## Current reader-page review

The final current root prose in recovery.md, networking.md and integration.md was also checked against the fresh sources above. [DOCS_REVIEW.md](DOCS_REVIEW.md) records exact hashes of this review snapshot. Prep/idle intake versus first-send binding, separate body resolver before Running, archive init/covering sync, fresh key/partition identity, remembered readiness and careful join limitation are accurately qualified. No new ACK round, flush-from-cancellation claim or authority-transfer proof was introduced.
