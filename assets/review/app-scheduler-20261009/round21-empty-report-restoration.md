# Round 21: restore the zero-report NativeBase condition

Reviewer/editor: `/root/docs_alignment`. Root's independent reviewer found a preservation omission: the baseline explicitly assigns an empty report snapshot to NativeBase, but the rewritten selection prose retained only “no prepared valid candidate.” I confirmed the baseline and applied the scoped E2E correction; root restored the canonical direction table.

## Preserved condition and counterexample

At research baseline `08cfe68b8b565fff4a0f8119cb36ec9b22062a31`, `docs/baton/direction.md` has:

```text
NativeBase | No reports / no prepared valid candidate |
Use an actual-parent-valid base policy | Native cut continues
```

Current `AGENTS.md:38` independently retains “without reports/prepared valid candidates use actual-parent valid base policy.” This is an adopted algorithm condition, not an open tie-break choice.

With zero admitted reports, the raw sum-LCP over that empty set equals zero for every admissible candidate. Merely saying “no supported prefix → sum-LCP” could therefore let an implementer choose an arbitrary all-zero candidate and publish it as prepared direction. “No prepared valid candidate” alone does not rule this out, because the mistaken implementation could label that arbitrary choice prepared. The explicit empty-snapshot rule is required.

This is a reasoning counterexample, not an executed native/Baton trace or a new test result. The Round 16 preservation pass did not detect this omission; its broad pass conclusion is qualified by this correction.

## Applied changes

| File | Scoped correction |
|---|---|
| `docs/baton/direction.md` — root-owned | Root restricts sum-LCP fallback to a nonempty report snapshot and restores “No reports or no prepared valid candidate” to the actual-parent-valid base row before protected adoption. |
| `docs/reference/verification.md:32` — native-owned | The coordinated verification row now explicitly covers nonempty-snapshot fallback and zero-report/no-prepared NativeBase behavior before adoption. It remains a Not run criterion. |
| `docs/e2e/leader.md` — first diagram and adjacent selection paragraph | Empty snapshot explicitly produces no prepared candidate; only a nonempty snapshot reaches candidate evaluation and optional direction. Prose restricts sum-LCP to a nonempty fully evaluated snapshot and restores no-reports base behavior. |
| `docs/assets/diagrams/diagram-06.mmd` | Mirrors the first embedded diagram's empty/nonempty branches. The native-cut branch remains parallel and never waits for report count, deadline or planning. |
| `docs/e2e/leader.md` — proposal-race diagram and final paragraph | Input label is “Frozen nonempty report snapshot and exact context.” No-report/no-prepared fallback is explicitly before adoption; already authenticated interpretation still cannot be dropped or reinterpreted. |
| `docs/assets/diagrams/diagram-12.mmd` | Mirrors the second embedded diagram's minimally qualified input label. The existing no-prepared branch still uses the native base without waiting. |

Both leader Mermaid blocks match their corresponding `.mmd` files. Only diagrams **06 and 12** require new rendering; root was notified and owns that render/manifest update. No other diagram was changed.

## What remains unchanged

- Snapshot closure is still once, on the first processed 4f+1-admission or fixed-deadline event. An empty-window deadline does not become a native cut wait.
- A nonempty snapshot with no qualifying 2f+1 entire prefix still uses the adopted raw sum-LCP fallback after complete bounded candidate evaluation.
- No new candidate-generation method, equal-score tie-break, tail policy, threshold or deadline setting is selected.
- Missing preparation before protected adoption may use the valid native base. Losing reports/material after authenticated adoption does not erase the protected prefix or permit fallback reinterpretation.
- App planning remains separate from actual native proposal-context recheck and the still-unimplemented authenticated Baton policy integration.

## Validation status

Baseline text and current AGENTS were read directly. Embedded Mermaid/source equality and `git diff --check` passed after the source edits. Root rendered 06/12, checked their source hashes, copied the assets into `docs/assets/diagrams`, updated the manifest, and reported passing docs check/build/diff. No native tests or protocol changes were made.

I opened both actual final PNGs after that copy:

- **06 passes:** the empty-snapshot branch visibly contains only “No prepared candidate,” while the nonempty branch contains evaluation and optional direction. Branch borders, labels and arrows remain readable without clipping or overlapping text. The native-cut branch remains separately marked under the outer parallel region, with its no-wait note intact.
- **12 passes:** “Frozen nonempty report snapshot and exact context” wraps cleanly above its request arrow. Prepared/recheck/fallback and later frozen-interpretation regions remain distinct and legible; the longer input label causes no overlap.

No further source or layout change is needed.

| Diagram | SHA-256 `.mmd` | SHA-256 actual `.png` |
|---|---|---|
| 06 | `3851356a09d3fbc31a11189b82e94ad523a591f009b41fd35cac147f89fd6b15` | `b869cad64219e42d4234fe8bd58d602b3283245cdb533fec1be70b38c876898b` |
| 12 | `b63f0d907f6cfebe31aa2f6a21b97d5d88c0e348c4ca05c5486f5f2c08cb221a` | `d607cf47fe4782d6678cd14615d53301895fc28d8564c4680ba830d8856c494b` |
