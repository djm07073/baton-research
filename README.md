# Baton

Read and edit the implementation design in **[Baton Docs](docs/README.md)**. The [table of contents](docs/SUMMARY.md) organizes 32 pages by layer, E2E case and separate benchmark implementation. Each module starts with its responsibility, then explains its Rust inputs/outputs, flow, and detailed contracts.

| Start here | Covers |
|---|---|
| [Implementation docs](docs/README.md) · [Contents](docs/SUMMARY.md) | Four layers, module responsibilities, Commonware source mapping, E2E sequences, open decisions |
| [Rust interfaces](docs/overview/rust-interfaces.md) · [Single Rust file](docs/assets/interfaces/baton.rs) | Four application traits plus existing body callbacks; arguments, outputs and completion conditions |
| [Pre-cut baseline implementation](docs/baselines/precut.md) · [GitBook](https://app.gitbook.com/s/pvyFEde12m2tVRjI8TRw/baselines/precut) | Separate chain without Baton: speculation, native ordering and incremental repair |
| [Research paper draft](baton-paper.md) | Algorithm, conditional safety/reuse arguments, native integration obligations, evaluation plan |

The [GitBook Baton space](https://app.gitbook.com/o/Z5g7kwPjokG0jEOyXNu6/s/pvyFEde12m2tVRjI8TRw/) is private within Beaker. [Rust interfaces](https://app.gitbook.com/s/pvyFEde12m2tVRjI8TRw/overview/rust-interfaces) is a direct entry point. Markdown in docs/ remains canonical. Git Sync and automatic Google Docs synchronization are not configured.

This is design work. Protocol implementation, native integration proofs, E2E execution, and benchmarks are not complete. Existing Commonware APIs and proposed application contracts stay distinct. Open policy cells remain blank. The Bank application model is outside the current scope.

Older documents and research material are preserved through the [archive index](archive/2026-10-03-root-history/README.md). Earlier implementation contracts are [archived](archive/2026-10-03-root-history/repository/research/archive/2026-10-03-implementation-outline/README.md). Historical Overpass documents are provenance, not replacements for the current design. [BATON_HANDOFF.md](BATON_HANDOFF.md) records sources and prior Google Doc revisions; [AGENTS.md](AGENTS.md) gives continuation instructions.

Source pin: [Commonware 534af0ede48affd35b2111522527547b4cc9bf72](https://github.com/commonwarexyz/monorepo/tree/534af0ede48affd35b2111522527547b4cc9bf72). [Tempo Technical Overview](https://app.notion.com/p/2dfc1352439b801db5b6cf6fe21fc315?pvs=204) and [Tempo DeepWiki](https://deepwiki.com/tempoxyz/tempo) are references for presentation structure. Their Simplex / Reth / REVM implementation is not adopted.

The canonical repository is [djm07073/baton-research](https://github.com/djm07073/baton-research). Existing checkout names and origin remain unchanged.

## Local preview

Use Node.js 20+ and Python 3 from the repository root:

```sh
npm ci
npm run docs:check
npm run docs:build
npm run docs:serve
```

The [local preview](http://127.0.0.1:8765) provides navigation, search, an in-page outline, and previous/next links. site/ is generated and excluded from Git. Edit docs/. Mermaid source and rendered assets live in docs/assets/diagrams/; diagram changes require refreshed renders and manifest.

[IMPLEMENTATION_SPEC.md](IMPLEMENTATION_SPEC.md) preserves older section links. The [pre-partition snapshot](archive/2026-10-03-before-gitbook/README.md) retains original prose and diagrams. Archived snapshots are historical and stay unchanged. [GitBook publication verification](assets/review/gitbook-upload-20261003/README.md) records the initial upload; the [English revision checks](assets/review/english-docs-20261003/README.md) record the translated update.
