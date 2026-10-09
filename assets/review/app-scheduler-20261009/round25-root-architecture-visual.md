# Round 25: current architecture artifact

Root directly viewed the current `docs/assets/diagrams/diagram-01.png` and reread its `.mmd` plus `docs/overview/architecture.md`.

- The App boundary visibly contains pool, callback handles, selected scheduler, execution/checkpoints and canonical writer. Existing Engine, Marshal and QMDB remain distinct supplied components.
- Canonical input reaches App execution without a Baton approval path. ACK is explicitly after durable apply. Scheduler-to-worker dispatch is exact-parent work.
- The adjacent caption says boxes are responsibilities, not mandatory actors; shared-owner state handles internal canonical/scheduler reconciliation. This overview is not a complete internal message graph.
- No clipped labels or overlapping text were visible. All arrows and the App boundary are readable at the displayed resolution.

This is artifact/prose QA, not a native execution test or protocol proof. Current reader images are under `docs/assets/diagrams`; older top-level artwork remains historical.

Observed UTC: 2026-10-09T09:22:16.581119+00:00

```json
{
  "docs/assets/diagrams/diagram-01.mmd": "a07d1e03a3344594185b4c5d9147532023c110a71e97b2d4b007c26e1ee7320d",
  "docs/assets/diagrams/diagram-01.png": "c48294a2db52efdc167829fa129c4fbf70c8961e5f62539036583aca91e4c3d1",
  "docs/assets/diagrams/diagram-01.svg": "86a9dc87bb5f0eb690889b0343ef72e548e9ce07b8872d9998335b8932bc4739"
}
```
