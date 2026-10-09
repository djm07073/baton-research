# Round 18: clarify verify, role and speculative admission

Reviewer: `/root/docs_alignment`. Scope is one dense paragraph at `docs/baton/README.md:50`, under “When speculative execution begins.” The preceding trigger and three-origin list, and the immediately following admission-versus-dispatch paragraph, are already useful. No core edit has been made.

## Proposed replacement

Replace only the paragraph beginning “For a validator with a local producer lane” with:

```markdown
Interpret successful **live** verification according to the node's role:

| Role | Candidate interpretation |
|---|---|
| Validator with a local producer lane | `context.chain != local producer chain` can identify other-lane work |
| Nonproducing validator | Live validation still exists; there is no local lane to exclude |
| `Role::Observer` | No live per-chain validation; normally enter through Marshal Update unless an explicit authenticated early-candidate intake is added |

`verify` still does not mean a new network receipt. Before speculative admission, check App's current lifecycle and deduplicate exact block identity, excluding already-applied work. Track startup explicitly: the callback has no origin or recovery flag. These checks filter speculation, not the native custody verdict.

A local pre-sign body can be prepared locally. If report eligibility requires an authenticated native header, promote it only when that evidence is available. `TransactionProposed` and `ProtocolAccepted` are useful best-effort observations; missed hints may reduce speculation but cannot block canonical processing.
```

Keep the next paragraph unchanged:

> The scheduler separates **candidate admission** from **dispatch**. A body can be valid while its execution predecessor is unfinished. Admission updates pending work; dispatch later checks the exact parent checkpoint. Producer-header ancestry is lane ancestry, not the merged application's execution-state parent. [Callback behavior](../../../docs/baton/interfaces.md#automatonverify-validity-custody-and-scheduling) makes this sequence explicit.

That quoted link is relative to this review file. The real existing page already uses the correct `interfaces.md#automatonverify-validity-custody-and-scheduling` link and needs no edit.

## Why this is clearer

The original paragraph combines three mutually different node roles with common callback filters, local pre-sign authentication and optional observations. A three-row table makes the user's `verify + other conditions ≈ other-lane block known` question directly answerable without reading past two unrelated roles. The common conditions remain adjacent, so the table does not imply that successful verification is a fresh packet, a new unique candidate, or completed execution.

This is a structural clarification, not a promise to reduce word count. It changes one existing paragraph into parallel role rules plus shared conditions. It adds no actor, flag, trait, new callback or policy choice. No additional table of every callback origin is needed because the preceding three bullets already provide that distinction.

## Retained facts and authoritative detail

| Fact | Where it remains |
|---|---|
| Verify is not one-to-one packet receipt; remote eligibility, local pre-sign and recovery are separate origins | Existing README `:44–48`, plus the replacement's first common sentence |
| Successful verify, live phase and foreign chain qualify the producer-validator interpretation | Replacement introduction and first role row |
| A validator need not have a producer lane | Second row; actual role/mapping derivation remains in `overview/glossary.md:21` |
| Observer lacks live validation planes and normally executes Update | Third row, preserving the optional authenticated early-intake condition |
| No origin/recovery callback flag; explicit startup lifecycle | First common paragraph; detailed recovery activation and retained-candidate re-evaluation remain in `baton/interfaces.md:11–15` |
| Exact identity deduplication and already-applied exclusion | First common paragraph; exact current-owner checks after async custody and repeated-attempt rules remain at `baton/interfaces.md:50–55,65–87` |
| Skipping speculative admission does not negate native custody obligations | “These checks filter speculation, not the native custody verdict”; the detailed late/retired request contract remains at `baton/interfaces.md:67` |
| Local pre-sign preparation is not automatically authenticated report eligibility | Second common paragraph, conditional exactly as before |
| TransactionProposed/ProtocolAccepted are useful but lossy optional hints | Second common paragraph; core `interfaces.md:67,139–143` keeps native/canonical delivery independent |
| Pending admission can precede exact execution-parent readiness; callback does not wait for transaction execution | Existing trigger `:42` and immediately following paragraph `:52`, retained unchanged |

The replacement intentionally keeps role interpretation separate from native payload validity and does not introduce a condition under which a valid already-applied block must answer false. All source-derived behavior remains the same as the canonical handler page.

## Disposition

Recommendation only; root owns the core page. No other paragraph, compatibility anchor, diagram or companion page needs changing for this clarification. No render or runtime check is relevant to this prose-only proposal.

## Root disposition

Applied the proposed role table and shorter lifecycle/authentication paragraphs. Used the actual `context.chain()` getter spelling. The three verify-origin bullets and admission-versus-dispatch paragraph remain unchanged. No role, callback or policy was added.
