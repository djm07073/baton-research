# Minimal role clarification — adopted by root

Only three existing page leads needed changes. No other API prose, declaration, diagram or policy adjustment proposed.

1. Architecture: explicitly name Executor computing transaction changes and Storage preparing roots/durably applying canonical state.
2. Normal E2E: explicitly name Executor computing changes and Storage applying/persisting; keep BlockService on existing body primitives.
3. Canonical E2E: replace ambiguous “It acknowledges delivery” with “Executor acknowledges delivery only after Storage has made canonical state, outputs, cursor and provenance recoverably durable.”

Current exact final page hashes and baseline comparison are in REPORT.md and final-prose-diffs.json. Root owns these canonical changes. Their meaning follows existing interfaces; no new vocabulary or another storage engine is needed.
