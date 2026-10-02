# Overpass: English LaTeX working draft

> **ARCHIVED RESEARCH DIRECTION — 29 September 2026:** This placement-based manuscript is retained for reference and existing builds. The [fresh research outline](../../overpass-plan-ordering-outline.md) is now authoritative for the research direction. LaTeX/PDF and Google Docs have not been rewritten. Historical “authoritative/latest” statements below refer to this old manuscript only.

> **Design update, 28 September 2026 — not yet applied to this manuscript:**
> [The fixed-cut implementation plan](../../overpass-fixed-cut-implementation-plan.md)
> supersedes the decision to retain native Multimmit tip extraction and extension
> voting. The new direction combines a 5f+1 fixed-certified-cut consensus profile,
> pipelined execution, and producer placement. Parent/view-change safety must be
> re-established; this is not a threshold-only patch. The LaTeX sources, released
> PDFs, and Google Docs remain v13.20, and the fork has not been changed.

Manuscript title: **Overpass: Pipelined Execution and Producer Placement for
Low-Latency State Finalization in Autobahn-Family Consensus**.

`main.tex` is the manuscript's editable source. `review-notes.tex` is a separate
internal evidence and validation companion, not an appendix for submission.
LaTeX remains the authoritative manuscript. A Google Docs review copy supports
anchored user comments; apply requested revisions back to LaTeX, then rebuild
the publication-format PDF. This is an explicit review workflow, not automatic
two-way synchronization. Preserve review comments when refreshing the copy.

[Open the Google Docs review copy](https://docs.google.com/document/d/1O-ub6EfMx_LBXTbx3bRzDH9zz3A_adku-Lslg9UjUrE).
It contains the main manuscript in a single-column commenting layout, including
figures, tables, references, and red review notes. The internal review companion
and placement supplement remain separate. Leave comments on selected text, then
request that those comments be applied to the LaTeX manuscript and PDF. Do not
resolve or reply to comment threads without explicit authorization.
Three multiline display equations use editable, subscript/superscript-formatted
text in the review copy to avoid Google Docs equation-conversion overflow; the
LaTeX formulas and publication PDF retain their original mathematical typesetting.

## Current scope (v13.20, 27 September 2026)

Overpass is specified against an **Autobahn-family consensus contract**; the
selected implementation and all three primary benchmark configurations use
**Multimmit**. This family name is a design category defined by this paper, not
a claim that the protocols have identical quorums or cut extraction.

Preserve native Multimmit voting, extensions, extraction, and horizontal-sweep
emission. Speculation may overlap dissemination and consensus; canonical result
adoption requires the authenticated emitted ordered prefix, not merely an L-QC
notification or chain-local membership finality. Equal cut votes do not establish
equal local bodies, dependency DAGs, or completed execution.

The draft marks three integration obligations in red: M1 (native emitted-prefix
adapter and version pinning), M2 (common execution checkpoints and eligible
signers), and M3 (placement metadata, admission, readiness threshold, activation
counter). The old Autobahn-only Q(F) subset and rotating-lane proposal are not
the selected Multimmit baseline. Legacy proof/PAC SDK and fork code are unchanged.

See [Korean feedback checklist](../../overpass-family-multimmit-review.md).
This update changes local LaTeX and PDFs only; Google Docs has not been synchronized.

The v13.20 scheduling decision replaces c+2 with selection at cut c and activation
after cut c+1 finalizes. Production continues without draining old blocks.
Old/new-map blocks may coexist and repeat a transaction; stable-ID filtering keeps
only its first canonical occurrence, excluding IDs consumed in prior history.
Application failure also consumes that ID. Later copies generate no second
attempt, fee, or event. Changed surviving occurrences require speculative reuse
validation. Map applicability/retirement and failed-producer reassignment remain
unresolved; the delay alone proves neither authorization nor simultaneous delivery.

The verified v13.20 build has **13 technical pages plus one references page**,
a ten-page internal review companion, and a two-page supplement. All three PDFs
were rebuilt and visually inspected; the build has no unresolved citations,
missing glyphs, or overfull-box warnings (underfull text-box warnings remain).
The scheduling and duplicate semantics add one page relative to v13.19; the
twelve-technical-page target therefore needs a later condensation pass, without
removing unresolved obligations. Experiments remain planned, not completed.

## Compact layout and previous v13.18 measurements

The main draft now uses the official USENIX two-column template for a realistic
OSDI page-budget check: US letter, 10-point type on 12-point leading, a 7-by-9-inch
text area, and a 0.33-inch gutter. This is a working layout, not a decision to
submit to OSDI or a claim of submission readiness. References start on a separate
page to make the technical-page count explicit. Red evidence notes remain in the
main draft and the internal review companion.

The official style was retrieved from
[USENIX author resources](https://www.usenix.org/conferences/author-resources/paper-templates).
`usenix2019_v3.sty` retains its typography and dimensions; the only local driver
change skips the dvips-only `breakurl` package under XeTeX. `preamble.tex` loads
hyperref first and disables unsupported microtype kerning/spacing features for
XeTeX/Tectonic. No font-size, line-spacing, or margin reduction is used to fit text.

The second slimming pass compresses sidecar preparation/selection/activation,
removes algorithm/prose duplication, groups Byzantine behavior into four attack
classes, and restructures Evaluation as questions, setup, and planned result
panels. The Multilevel rationale, routing-threshold example, eligible-signer
argument, and unresolved D4/P3 handoff remain in the main text. That v13.18 pass preserved 30 red-note blocks verbatim. The v13.19 scope update
revises obsolete profile assumptions and adds M1--M3 rather than hiding unresolved work.

`placement-supplement.tex` is a separate optional PDF: Appendix A contains
reproducibility/encoding details and Appendix B contains transfer/storage details.
It is not part of the main technical-page count; the main argument must stand
alone. The internal review companion is not a submission supplement.

Reserve roughly four of the eventual twelve technical pages for actual Evaluation
results. Replace planned-panel prose with measurements and their interpretation;
do not append a full results section to the current plan. The remaining allocation
is approximately two pages for Introduction/Background, two for the core pipeline,
1.5 for placement, one for correctness, and 1.5 for related work and closing
sections. This is a target, not a statement that all sections already fit it.

The verified v13.18 build has **12 technical pages plus one references page**,
with a two-page supplement and a ten-page internal review companion. Main-section
source words fell from 8,980 to 7,234 (about 19.4%); this excludes the supplement
and is not a typeset word count. The previous 22-page PDF used a single-column
11-point layout, so its page count is not a like-for-like compression metric.
Four pages of empirical results are **not yet free**: replacing the Evaluation
plan and resolving review notes will require another page-budget pass.

The abstract opens with Autobahn's parallel producer-lane dissemination and
cut agreement, then distinguishes ordered inputs from completed execution and
result certification before introducing Overpass. The revised abstract makes
no claim that Autobahn ignores execution or that the proposed gains are measured.

The correctness section retains case-by-case Byzantine boundaries. The detailed
Evaluation fault-injection procedures and multilevel unit-test checklist have
been deleted, not relocated to an appendix or the review companion. Red review
notes remain. No completed fault tests or bounded latency under arbitrary attacks
are claimed. Input DA and execution certification must not be conflated.

The entity-based audit covers a Byzantine planner/leader, producer, client/relay,
DA voter, executor/collector, and data/read server. The f bound counts distinct
validator identities across roles, not f per role. The cut proposal and its locks
must bind the map/KEEP decision; merely attaching a map to a tips certificate is
insufficient. Fixed-map rejection is separated from unresolved producer handoff,
independent certificate collection, and online activation. Valid KEEP, declared
access padding, and poisoned history are not automatically invalid. At each
configured update opportunity, multilevel search rebuilds a nested affinity
hierarchy from singleton scopes while preserving incumbent positions and
residence. Coarse bundles expose joint moves and fine refinement permits splits;
every move is scored using actual whole-transaction routing. Neither hierarchy
construction nor candidate certification activates a map, erases cold scopes,
guarantees improvement, or repairs faulty-producer handoff.
The review companion retains the actor/check/residual-risk table and unresolved
evidence obligations; these are not experimental results.

## Scope

The objective is lower transaction-ingress-to-certified-state-finalization
latency. The cut-to-state interval is the principal diagnostic interval targeted
by the same-cut DA/ordering/execution pipeline, not a replacement for E2E
measurement. Group computation, routing, queueing, admission verification, and
retries are included; durable read readiness is a distinct endpoint.

Section 3 presents the core pipeline, declared accesses and safe reuse, and
certified state installation. Section 4, **Reducing Re-execution through Producer
Placement**, combines the subsequent cost with its proposed solution: bounded
deterministic multilevel grouping, whole-transaction assignment, and a placement
predicate checked before DA acknowledgement. It does not introduce a trusted
coordinator, a new execution engine, a ZK/PAC design, or state-owner lanes.

The algorithm choice is grounded in KaHyPar (JEA 2022), deterministic parallel
hypergraph partitioning (ACDA 2025), and workload-driven affinities in Schism.
The core draft retains the routing-threshold example with cost 15 to 12,
explaining why coordinated moves can improve where one/two-scope greedy changes
cannot. Supplementary Appendix A holds the reproducible hierarchy-construction details and a
connectivity/routing-cost counterexample. This supports the search
architecture, not a measured latency gain or transfer of native connectivity
optimization guarantees. Greedy search remains an evaluation baseline.

The grouping cost is a historical proxy, not a proven retry or latency optimum.
Input windows, tie-breaking, integer arithmetic, group/load/change limits, and
explicit KEEP decisions are specified. Online map
activation, authenticated old-map applicability, durable canonical deduplication,
and reassignment from a faulty producer remain red obligations D4/P3. Cross-block
duplicate exclusion is no longer a goal. A fixed authorized map is
the first enforcement profile; dynamic update safety is not claimed complete.

Section 4.3 adds a logical placement sidecar: background validators reproduce and
store a candidate, with a readiness threshold q_map > f; the concrete native-profile
threshold remains M3. The leader proposes a prepared candidate or KEEP. Native
finality must bind the decision and activation context. Selection at cut c and
activation after cut c+1 require authenticated native consensus identifiers (M3),
not local L-QC arrival counts or wall clocks. Later KEEP cannot cancel a scheduled
update. The sidecar is neither an ingress coordinator nor independent finality.
Old blocks remain intact and may be ordered later; a version tag alone cannot
authenticate newly produced stale-map blocks. Safe version lifecycle and
faulty-producer reassignment remain D4/P3.

The main evaluation is **Original / Pipeline / Pipeline + Placement**, with the
same application and execution backend and same-order controls. Block-STM with
Aggregators V2 is the planned benchmark backend only, not a protocol requirement
or design contribution. Zaptos is brief related work, not a required direct
benchmark. No experimental speedups or complete implementation are claimed.
Grouping is compared against ungrouped state affinity under the same admission
policy; hard versus soft admission is a separate comparison. Groups are fitted
on a past history window and evaluated on the next unseen window.

The family contract does not fix one ordering quorum. The selected Multimmit
profile uses n >= 5f+1 and retains native finality. Result certification requires
f+1 matching direct-execution signatures from a configured eligible set A_e(F)
within the epoch committee; its concrete definition is unresolved M2. This is
an honest-witness threshold for a unique, already-finalized deterministic input,
not a replacement for any ordering quorum.

Execution signatures bind the exact ordered range, parent history, runtime, and
outputs, not the serialization of one L-QC. Common checkpoint endpoints are
necessary to collect matching signatures despite differing compatible emitted
prefix lengths. Liveness requires enough honest eligible executors to complete
the same checkpoint. No Autobahn Prepare/Confirm subset is transplanted into
Multimmit, and no new execution vote is a prerequisite for native ordering.

## Files

- `main.tex`, `sections/`: English manuscript.
- `sections/04-placement.tex`: the follow-on problem and solution, including
  multilevel rationale, routing-aware cost/refinement, and sidecar updates.
- `sections/09-placement-details.tex`: Appendix A, containing hierarchy
  construction and the connectivity/routing-cost counterexample.
- `sections/10-transfer-details.tex`: Supplementary Appendix B, containing
  certified-update transfer and crash-safe installation details.
- `placement-supplement.tex`: independently buildable optional supplement.
- `usenix2019_v3.sty`: official USENIX style with the XeTeX driver guard above.
- `preamble.tex`: shared typography and red review-note command.
- `figures/pipeline.tex`: editable vector pipeline diagram (TikZ).
- `figures/uneven-lane-order.tex`: editable four-lane ordering example (TikZ),
  with unequal growth and an explicit D-to-C-to-B-to-A visit order.
- `figures/placement-sidecar.tex`: editable candidate-certification flow and
  cut-selection / delayed-activation timeline (TikZ).
- `references.bib`: verified primary-source bibliography.
- `review-notes.tex`: English claim/evidence review.
- `Makefile`: build with Tectonic or latexmk, then publish local PDFs.

## Build

With Tectonic installed:

```sh
make
```

Or provide its location:

```sh
make TECTONIC=/absolute/path/to/tectonic
```

With a conventional TeX Live installation:

```sh
make latexmk
```

The build directory is ignored. `make publish` copies all three PDFs to `output/pdf/`
at the repository root. Import this directory as a ZIP into a LaTeX editor such
as Overleaf; select `main.tex`, `review-notes.tex`, or `placement-supplement.tex`
as the main document. The main PDF has no dependency on the supplement.
The source requires only ordinary TeX packages and no shell escape.

## Structure rationale

Separate the core mechanism from a substantial optimization, but keep the
optimization's motivating cost next to its solution. Autobahn first presents its
base protocol and then explains the residual wait motivating parallel multi-slot
agreement in Section 5.4; Section 5.5 holds additional optimizations.
Anthemius uses Architecture followed by Block Construction inside its design
section, while TxAllo separates Design Challenges from its algorithm section.
These are structural precedents, not claims that their mechanisms match ours:
[Autobahn](https://www.cs.cornell.edu/~fsp/reports/Autobahn__SOSP24_CR.pdf),
[Anthemius](https://fc25.ifca.ai/preproceedings/115.pdf),
[TxAllo](https://arxiv.org/pdf/2212.11584).

## Before public release

Keep red review notes until their underlying evidence or design obligation is
resolved. Do not merely hide the notes to make an unfinished draft appear complete.
Authors and affiliations are deliberately not invented; add the confirmed author
list before circulation as a submission. Before arXiv, review the final source
bundle for internal notes and metadata, obtain coauthor approval, check the target
venue's preprint policy, and choose the license. This task does not submit to arXiv.
The current [OSDI 2027 CFP](https://www.usenix.org/conference/osdi27/call-for-papers)
allows twelve technical pages plus references and separate optional supplements;
reviewers need not read the latter. It also distinguishes permitted AI editing
from prohibited wholly or largely AI-generated submissions. Authors must own and
verify the substantive research, evidence, and final manuscript; formatting this
working draft does not establish compliance with that policy. Recheck the target
venue's actual CFP before submission.
