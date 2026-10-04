# Final verification-row precision addendum

**A genuine narrow wording correction is warranted.** The Tx/pool verification case currently says “no cleanup before canonical outcome.” Read independently as a case specification, that can prohibit all candidate removal before that transaction's own canonical outcome, including a selected backend's destructive proposal pop, replacement/expiry or chosen eviction. Current detailed reader text explicitly leaves those policies open and permits destructive selection with retained material/cancellation reconciliation. “Cleanup” is broader than the intended canonical-retirement condition.

This addendum qualifies the no-further-edit conclusion in `COMPLETION_READINESS.md` (SHA-256 `900a05f6de1ecc4a05b19bf64d7b994996860b3814daaeb0ff72d34139bcc9a2`). Its full documentary/source assessment remains applicable; this additional adversarial check identifies one small validation-plan phrase that should match its already-correct detailed contracts. No backend/TTL/eviction/duplicate/cancellation policy is selected.

## Actual reader and source support

At baseline `1212e680e8e8f1316b9557a16b2e5b5acfe1ea8a`, `docs/reference/verification.md:23` reads:

```text
| Tx / pool | New, duplicate, structurally invalid; proposal cancellation; no cleanup before canonical outcome | Not run |
```

The central TxPool::select comment says “Selection alone does not establish canonical retirement.” Tx interfaces separate on_proposal and on_commit; the body E2E explicitly permits destructive selected-backend ownership/reselection integration. The tx reuse section describes Constantinople's immediate pop and Nunchi replacement/TTL without adopting them as defaults.

Pinned Constantinople `pop_lane_proposal` at actor.rs:402–435 actually pops entries and transfers transactions at proposal time. Pinned Nunchi Pool::finalize at pool.rs:211–281 advances nonce/height and can expire candidates beyond the included digests. These are retained complete-tree/blob-checked primary bytes bound in the readiness receipt, not fresh downloads. They demonstrate why pool storage removal is not synonymous with canonical retirement. The old row need not invalidate these whole-actor candidates by implication.

## Exact minimum recommendation

Replace only the broad clause with “selection/proposal is not canonical retirement”:

```text
| Tx / pool | New, duplicate, structurally invalid; proposal cancellation; selection/proposal is not canonical retirement | Not run |
```

This preserves the required distinction: selection/proposal alone cannot establish canonical execution or drive canonical outcome cleanup as though committed. It does not authorize arbitrary loss of selected/native custody material; existing retained bytes, cancellation/reselection, processed canonical outcome and recovery contracts still govern those owners.

No heading, citation, Rust signature/comment/export, diagram, public trait, test status or policy table changes are needed. No new test was executed or prescribed as a current result. Root owns the canonical edit and final reader/publication binding.

`addendum-receipt.json` binds the exact current reader/report bytes and the two decisive retained source files. Independent peer/final review and the full **01:29:14 UTC** window remain pending. This addendum does not complete the six-hour goal.
