# Consensus open decisions

**The responsibilities are defined; the integration contracts still need decisions.** Wire formats, policy adoption, and recovery details below remain blank until reviewed.

## TODO: bind Baton prefix and policy to cut proposals

**Status: not implemented or proved.** The pinned native `LeaderBlock` contains `round`, `parent`, `history` and per-lane `proposals`. Each `ChainProposal` carries its lane anchor and payload commitments; neither type currently expresses Baton's selected cross-lane execution prefix or ordering policy. Public Automaton/Relay/Reporter callbacks alone cannot add this binding. This work requires changes at native proposal construction, validation and recovery boundaries. [Pinned LeaderBlock](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L563).

- [ ] Define a bounded representation for the selected prefix and frozen ordering policy, bound to the actual proposal parent, history, immutable frontier, rule and execution context. Inline bytes versus a commitment to retrievable material remains an open choice; an unauthenticated side message is insufficient.
- [ ] Connect completed Baton selection to native leader proposal construction. Bind the chosen representation into canonical encoding and the proposal digest authenticated by native signatures/votes. Recheck actual context and freeze it before signing; late reports/planning must not mutate that proposal.
- [ ] Add validation before native proposal voting. Verify the available selection/authentication basis, exact context, producer ancestry and inherited ordering constraints. Validate the permitted exception to baseline global ordering and exact leading-prefix preservation, rather than accepting arbitrary reordering. Concrete proof material and validation interfaces remain open; Reporter is a post-admission observer, not this validation hook.
- [ ] Connect policy interpretation to native tip extraction, continuation and extension. Show that every adopted prefix block is included and the irrevocable execution sequence starts with that exact prefix after the immutable frontier. Prefix membership or lane-tip inclusion alone is insufficient; adding a field does not prove this property. Preserve native tip extraction/extension and do not assume all proposed inputs become irrevocable immediately.
- [ ] Preserve the authenticated policy, selected source witnesses and history through V-QC rescue, view recovery, retained evidence export and restart. Baton must reconstruct the same continuous order and deliver it through `on_finality` to `Executor::commit` without reinterpretation or duplicate canonical effects.
- [ ] Keep cut no-wait behavior: before adoption, use an actual-parent valid base path when no valid policy is prepared; do not wait for report count, deadline, planning or a direction ACK quorum. After authenticated adoption, never silently drop the protected prefix as fallback. Adoption/availability and liveness conditions still require a concrete design and proof.
- [ ] Implement and run checks for valid policy exceptions, missing/reordered prefix, invalid ancestry, wrong parent/history/rule, policy substitution after signing, late planning, unavailable policy material, same-tip evidence revisions, extension, view change and restart. Verify exact emitted order and no added report/direction barrier. These checks are planned, not run.

The ordinary local scheduling rule still preserves completed/current execution and sorts only pending blocks. Proposal-policy validation does not by itself adopt a conflicting advisory direction's precedence over that local path. If native confirmed order differs from speculation, Executor's existing exact-parent reuse/repair responsibility applies. Codec, policy availability, adoption, tail ordering and the concrete integration API remain undecided below.

## Open decisions

| Item | Decision |
|---|---|
| Body format / size limit / archive layout | |
| Body transport adapter / fetch protocol | |
| Targeted retry / fallback / pending want, subscriber, and byte budgets | |
| Evidence export schema / retention handoff | |
| Ordering policy codec / availability | |
| Protected-prefix adoption conditions | |
| Exact continuation / extension / view recovery integration | |
| Backfill / checkpoint / GC | |
