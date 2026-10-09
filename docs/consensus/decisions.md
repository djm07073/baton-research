# Consensus open decisions

**The base Engine/Marshal connection already exists.** Remaining application choices concern body validity/bounds, scheduling and state application. Full Baton's change to authenticated ordering requires native protocol work beyond those callbacks.

## TODO: bind Baton prefix and policy to cut proposals

**Status: not implemented or proved.** Current `LeaderBlock` contains `round`, `parent`, `history` and per-lane `proposals`. It carries no selected Baton cross-lane prefix or frozen policy. `Automaton::propose` constructs a producer body, not this leader proposal; `Reporter<Activity>` observes admitted activity and cannot validate proposals before voting. [Current LeaderBlock](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/types/block.rs#L802).

- [ ] Define bounded policy/prefix representation bound to the actual proposal parent, history, immutable frontier, rule and execution context. Inline bytes versus a commitment to retrievable material remains undecided.
- [ ] Connect the App's completed Baton selection to native leader construction. Recheck the actual context, freeze policy in canonical authenticated proposal encoding and preserve it after signing. Late reports/planning cannot change that proposal.
- [ ] Validate the policy and ancestry before native voting, including exact leading-prefix preservation. Membership alone is insufficient. Authentication/proof material and the concrete hook remain open.
- [ ] Preserve native tip extraction and extension while proving adopted-prefix inclusion and exact leading execution sequence after the immutable frontier. Continuation can defer unresolved output; policy cannot assume all proposed inputs immediately become irrevocable.
- [ ] Preserve policy and interpretation through V-QC rescue, view changes, proof retention and restart. Extend existing Marshal history/order/recovery handling consistently so all nodes deliver the same output indices and block sequence. Do not add a second App-side final-order interpreter.
- [ ] Keep cut no-wait behavior: before adoption use an actual-parent valid base path if no valid prepared policy exists; never wait for report count, deadline, optimizer or direction ACK. After authenticated adoption do not silently drop a protected prefix as fallback. Adoption/availability/liveness still need design and proof.
- [ ] Test wrong parent/history/rule, omitted/reordered prefix, invalid ancestry, policy substitution, late planning, unavailable material, extension, same-tip evidence changes, view recovery and restart. These protocol tests are planned, not run.

The App's ordinary local scheduler preserves completed/current order and sorts pending work only. Advisory direction precedence over a conflicting started path remains open. When canonical Updates differ from speculation, App performs exact-parent reuse/repair; it cannot change the finalized stream to match its local queue.

## Open decisions

| Item | Decision |
|---|---|
| Application body format, hash/domain, transaction/byte bounds and validity | |
| App scheduling bounds, candidate retention and global-rule comparator/tie-break | |
| Baton actual-leader-context / prepared-policy native hook | |
| Ordering policy codec / availability | |
| Protected-prefix adoption conditions | |
| Exact continuation / extension / view recovery integration | |
| Policy-specific Marshal interpretation, persistence and recovery | |
| App state-sync/floor coordination and application retention | |

Marshal's base body transport, backfill, catalog and ACK cursor are existing mechanisms. Configure their supplied bounds and APIs rather than treating them as new Baton layers. See [assembly](../reference/integration.md) and [verification cases](../reference/verification.md).
