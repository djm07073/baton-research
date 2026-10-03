# Baton — current research handoff

Updated 2026-10-04. This supersedes the current-state claims in [SESSION_HANDOFF.md](archive/2026-10-03-root-history/repository/SESSION_HANDOFF.md), while preserving that earlier handoff as history. Research/specification work only; no native adapter, completed integration proof or E2E results.

## 2026-10-04 Active six-hour Commonware reuse review

The user requested six hours of repeated multi-agent investigation and review to maximize Commonware reuse in the current Baton GitBook, with actual Commonware-based chains as assembly references. The active window is 2026-10-03 19:29:14 UTC through 2026-10-04 01:29:14 UTC (2026-10-04 04:29:14–10:29:14 Asia/Seoul). Current requirements and wave evidence are tracked in [the reuse review](assets/review/commonware-reuse-20261004/README.md). This is ongoing, not a completion report.

Latest conversation decisions supersede the previous five-trait/storage ownership wording below: Executor produces execution changes/batches; Storage owns Merkle/root calculation, canonical database apply and persistence. Root computation should be requested when useful rather than required by dependency on glue::stateful::Application. Existing QMDB sealed-parent batch forks need to be distinguished from any additional root-deferred execution view. Executor continues to control exact execution paths, certification and normal-path state sync; Baton remains outside that result/apply path. Body propagation should follow real Commonware broadcast/resolver/archive composition with native Multimmit adapters. Tx pool reuse must be investigated across actual ecosystem implementations, not inferred from a generic provider/queue.

Four source/review waves now cover body/consensus composition, pool-to-producer mapping, concrete execution/storage APIs, Orderer proof storage, native startup/lifecycle and package identities. Current docs use existing Automaton/Relay/Reporter over buffer, generic resolver and archive for logical BlockService. Five application traits remain TxPool, Orderer, Baton, Executor and Storage. The native git workspace declares 2026.7.0 while inspected Tempo/Alto/Nunchi locks resolve registry 2026.9.0: copy wiring and adapt chosen actor source into one native graph, without silently assuming type interoperability or a release upgrade. Generic certificate Subject/Attestation/Scheme/Signers are reusable conditionally; unchanged N5f1 certificate quorum is n-f, not the execution f+1 requirement. Existing supervision supports task lifetimes but does not establish application flush or verified strict signing-material quiescence.

Fourth-wave local build/migration/browser checks pass for 31 pages, 249 local links, five unchanged Rust traits, 18 reused diagrams and 39 blank choices. GitBook change request #7 (`udvqzN3QJlTBXxJ0QtPN`) is published as `VZgSSM1vxObvtUhGUVFR`: strict readback verifies 38 pages, 478 links and 94 previous anchors; live IDs/documents/file metadata match the draft. Ten documents changed, 28 stayed unchanged; no attachment upload was needed. Prior publications remain in the review history. Raw remote attachment bytes remain unconfirmed. The third batch is pushed/verified at `cd9a0864cfa2171769bbe7f6d64fa3396ca878c6`; later batch GitHub receipts are recorded separately. Native pin, no-wait behavior, exact-order/direct-imported provenance and open policies remain intact. Source sketches are uncompiled; no protocol implementation, dependency upgrade or six-hour completion is claimed.

Fifth-wave source/review now makes archive identifiers/ownership and Producer admission, localized Nunchi actor adaptation, concrete pending-batch replay alternatives and runtime task placement explicit. CR8 `8Ld7JaQmvqlD1ahhTU6c` is published as `jCIYtF1KMH1WI7GnVz2Y`: 38 pages, 498 links, 98 preserved anchors; eight updated and 30 unchanged documents, all file metadata unchanged. Local build/migration/browser checks pass for 31 pages/251 links/five unchanged traits/18 diagrams/39 blank choices. [Final resolution](assets/review/commonware-reuse-20261004/wave5/DOCS_RESOLUTION.md) binds independent reviews and page hashes. The fourth batch was pushed/verified at `b5747f6a28527a4507901f2e46b426b5ff2a4b7c`; later batch Git receipts are separate. Native proof and open-policy boundaries remain; this is ongoing work within the requested six-hour window.

Sixth-wave review adds the exact Tempo body propagation path, six-role reuse table, typed result exchange, public repeated sync with explicit progress/completion and storage ownership, recoverable native exact-source handoff, and existing Metadata/journal commit mechanisms. CR9 `lXj54cWzKiMbpHh5ZXR1` is published as `NFuXtAIdglYgcndKT0Ly`: 38 pages, 532 links, 98 preserved anchors; eight updated and 30 unchanged documents, all file metadata unchanged. Local build/migration/browser checks pass for 31 pages/257 links/five unchanged traits/18 diagrams/39 blank choices. [Final resolution](assets/review/commonware-reuse-20261004/wave6/DOCS_RESOLUTION.md) binds four reports, independent cross-reviews and eight final page hashes. The fifth batch was pushed/verified at `8b61492bbebdbf34dbc10e5d43c3117e19618377`; subsequent Git receipts are separate. This is ongoing work within the six-hour window, with native/application integration and policy choices still open.

Seventh-wave review adds existing body codec/digest/archive interfaces, Reporter/mailbox composition, QMDB live ancestor handle ownership and storage bounds/root distinction, and dependency-aware static pool selection. CR10 `rcT3ZAPCvF24CgW3Tviy` is published as `FC0fuQHY8XibiksLncT6`: 38 pages, 551 links, 98 preserved anchors; four updated and 34 unchanged documents, all file metadata unchanged. Local build/migration/browser checks pass for 31 pages/257 links/five unchanged traits/18 diagrams/39 blank choices. [Final resolution](assets/review/commonware-reuse-20261004/wave7/DOCS_RESOLUTION.md) binds independent reviews and four final hashes. Wave6 was pushed/verified at `f2973dd98598eddac73d212c2b78e04cefb311c8`; later Git receipts are separate. The six-hour review remains active, with native/application integration and policy choices still open.

Eighth-wave review adds buffer receive/subscribe, public Current value/absence proofs, optional Exact completion handles and public worker/future/strategy APIs. CR11 `3AhBcT7WpRoeqE3mFNgy` is published as `2KMSlL0AfmImuyvywE5i`: 38 pages, 566 links, 98 preserved anchors; four updated and 34 unchanged documents, all file metadata unchanged. Local build/migration/browser checks pass for 31 pages/257 links/five unchanged traits/18 diagrams/39 blank choices. [Final resolution](assets/review/commonware-reuse-20261004/wave8/DOCS_RESOLUTION.md) binds all independent reviews/final hashes. Wave7 was pushed/verified at `99dc2c456c4b318fefb368cb39a145298f7d86b7`; later Git receipts are separate. The six-hour goal remains active; integration proofs, root/query/worker choices remain open.

## 2026-10-04 GitBook comments and planning ownership correction

Five inline comments were read at their exact Rust-interface anchors: BlockService Commonware reuse, merging TxPolicy into TxPool, Runtime ownership, ResultService decomposition/primitive reuse, and removing the redundant Planning inside Executor section. The follow-up user question corrected direction selection ownership: Baton::plan selects direction from reports; Executor handles execution-tree parents, execute/commit, canonical promotion and pruning. The previous merge mistakenly combined these two responsibilities.

The public interface now has five module traits. TxPool absorbs static analyze/classify. Executor owns transaction effects and exposes sign_result, collect_result, verify_result, and result_certificate directly; Runtime and ResultService are no longer application traits. Commonware task runtime, crypto, storage, and transport primitives remain reusable beneath these contracts. Application statement verification and exact-order/input-state checks remain Executor responsibilities. All methods retain English Rust doc comments. Existing historical notes below describe earlier revisions.

Commonware primitive selection is now recorded in each layer and in docs/reference/integration.md. Discovery queried commonware-library MCP v0.0.5 at explicit source v2026.9.0; native Multimmit remains pinned to 534af0ede48affd35b2111522527547b4cc9bf72. Collector/result transport, Stateful lifecycle and QMDB sync are reuse candidates with explicit compatibility and application-verification boundaries. Buffered broadcast is not durable custody; generic collector response counts are not f+1 execution certificates; one-time Stateful bootstrap sync is not repeated normal-path validator sync. No dependency or protocol implementation was changed. Published GitBook revision `TBVjJb5b1ideu6YEBXIq` matches the verified 38-page draft. See [comment and primitive checks](assets/review/comments-and-primitives-20261004/README.md).

## Historical: 2026-10-04 Executor planning and execution tree

The latest user decision merges Planner into Executor and removes the public reschedule method. Executor::plan evaluates bounded direction candidates; execute(block) resolves a valid execution-parent block hash, links the child, and executes through Runtime; commit(range) promotes the exact finalized path, persists it durably, and prunes conflicting branches. Compatible descendants remain pending. Physical reclamation follows worker-reference release and required recovery/query/result/state-sync retention. An execution-parent hash is distinct from a Multimmit producer-header parent; concrete hash/context binding remains open.

The canonical Rust page now has eight traits, and every method has English Rust doc comments explaining its role and success boundary. Baton retains report windows, direction authentication/dissemination, and a completed prepared-policy cache. Executor owns planning, tree links, branch reuse, worker priority/fencing, canonical promotion, and pruning. Planning from a snapshot must not block commit or native cut. This is an interface/documentation change, not runtime implementation or a new native protocol proof. Published GitBook revision `DC05zLPlfWkUydJDXdiw` is verified; see [Executor tree update checks](assets/review/executor-tree-20261004/README.md).

## English documentation revision

The 31 active docs pages now use English, including navigation and diagram labels. Each module begins with a plain-language responsibility, then describes Rust trait inputs/outputs, call flow, and detailed completion conditions. All nine Rust declarations, pinned external source occurrences, and 39 blank policy decisions are preserved. Two stale diagram endpoints now match the already-adopted Executor responsibility: canonical outcomes originate in Executor, and Orderer delivers directly to Executor. This is documentation work, not protocol implementation or validation. GitBook updates preserve existing page identities; Markdown remains canonical without Git Sync. The English revision `QZTpgxjih7GpPhLNrfyh` is published and verified; see [publication checks](assets/review/english-docs-20261003/README.md).

## 2026-10-03 GitBook 업로드 완료

[Beaker / Baton](https://app.gitbook.com/o/Z5g7kwPjokG0jEOyXNu6/s/pvyFEde12m2tVRjI8TRw/) 비공개 공간에 문서 31개·섹션 안내 7개를 업로드했다. [Rust 인터페이스](https://app.gitbook.com/s/pvyFEde12m2tVRjI8TRw/overview/rust-interfaces)와 단일 Rust 파일, 18개 SVG를 함께 연결했다. 저장된 38개 페이지의 텍스트·code fence·315개 링크를 확인하고 change request를 merge했으며 published revision `9wT9dqT7E4YdDK44oElB`의 document IDs·파일 목록도 확인했다. 한글 자동 절 주소 대신 cloud 전용 명시적 절 주소를 사용한다. 원본 Markdown은 `docs/`이며 Git Sync는 연결하지 않았다. [검증 기록](assets/review/gitbook-upload-20261003/README.md)을 읽는다. 아래 미발행 설명은 각 시점의 작업 이력이다.

## Rust 인터페이스 진입점

사용자가 Rust 인터페이스를 찾기 어렵다고 지적하여 [Rust 인터페이스](docs/overview/rust-interfaces.md)를 목차 상단과 시작 페이지에 배치했다. 기존 9개 trait 선언은 이 페이지를 원본으로 모으고 레이어별 상세 계약은 선언의 해당 anchor를 연결한다. 선언 본문은 그대로 유지했다. [단일 Rust 파일](docs/assets/interfaces/baton.rs)은 이 페이지에서 생성하며 문법을 확인했다. 실제 서비스 구현·프로토콜 검증을 수행한 것은 아니다.

문서는 현재 31개 본문 페이지다. GitHub 반영과 GitBook 업로드를 각각 확인했으며, GitBook에는 목차용 섹션 안내 7개도 둔다.

## 2026-10-03 GitBook 형태의 페이지별 문서

페이지 분리 당시 [Baton Docs](docs/README.md)와 [목차](docs/SUMMARY.md)를 30개 페이지로 구성했다. 전체 구조, Tx, Consensus, Baton, Execution, E2E, 개발·참고자료로 나눠 각각 검토한다. `.gitbook.yaml`은 GitBook Git Sync에 연결할 구조이며 계정 연결·서비스 발행은 수행하지 않았다. 로컬 사이트 빌드와 실행은 저장소 README에 설명한다.

기존 IMPLEMENTATION_SPEC.md는 이전 섹션 링크를 새 페이지로 안내하는 진입점이다. 원본 본문과 18개 그림은 [분리 직전 스냅샷](archive/2026-10-03-before-gitbook/README.md)에 보존했다. 이전 모든 본문 절과 외부 출처를 새 페이지에 대응시켰으며, 아직 Baton이 canonical 전달을 중계하는 것처럼 적힌 §5.7은 최신 Orderer → Executor 책임에 맞게 정정했다. 39개 미결정 정책 칸은 비워 둔다.

아래 단일 파일 재구성 설명은 페이지 분리 전 단계의 이력이다. 현재 문서의 책임·인터페이스 설명은 각 레이어 페이지에서, 사건별 흐름은 E2E 페이지에서 수정한다. Protocol 구현·통합 증명·E2E·benchmark 결과를 추가한 작업은 아니다.

## 2026-10-03 구현 문서 재구성

페이지 분리 전 구현 스펙은 한 파일이었다. [원본 스냅샷](archive/2026-10-03-before-gitbook/IMPLEMENTATION_SPEC.md)을 보존했다. 사용자 지정 네 레이어(Tx-router / mempool, Native Multimmit, Baton, generic execution / QMDB)와 lifecycle sequence를 중심으로 새 개요를 정리했으며 Bank는 현재 개발 범위에서 제외한다. 미결정 정책은 빈 결정 칸으로 보존한다. 아래 Google Docs revision 표와 상세 구현 계약은 이전 snapshot의 출처이며 새 개요와 자동 동기화하지 않는다. 구현 개요의 문서 검토를 마쳤으며 protocol 구현·E2E·benchmark 결과는 없다.

## Rust 인터페이스와 이름 정리

현재 구현 문서의 중심 모듈은 `TxPool`, `BlockService`, `Orderer`, `Baton`, `Executor`, `Runtime`이다. `TxPolicy`, `Planner`, `ResultService`는 이 안에 조립할 수 있는 보조 trait이며 별도 actor·crate를 필수로 추가하는 결정은 아니다. 기존 controller / owner / signer 등의 표기는 구현 스펙 §1.3의 대응표에서 찾는다. Commonware의 upstream API 이름은 유지한다.

§1.7은 호출 흐름과 associated type 연결을, 각 레이어의 인터페이스 절은 Rust trait 선언 초안을 보여준다. 구체 필드·codec·정책·runtime 배치는 미결정이며 native cut의 no-wait, 실행 결과 / durable 적용 / 결과 인증의 구분을 유지한다. 선언 문법 확인은 서비스 구현이나 프로토콜 실행 검증과 구분한다. 이전 문서 검토의 snapshot 기록은 이 후속 수정의 검토 기록으로 대체하지 않는다.

## Executor의 state finalization / state sync 책임

최신 사용자 결정에 따라 state finalization과 validator의 정상 경로 state sync는 Executor가 담당한다. 서명·인증서·change set은 Executor ↔ Executor로 직접 교환하고 ResultService는 Executor 내부 역할로 둔다. 확정 순서는 Orderer → Executor로 직접 전달하며 durable delivery ACK와 tx 결과도 Executor → Orderer / TxPool로 보낸다. Baton은 사전 실행·재실행과 report / direction을 조율하며 이 경로의 승인·중계·대기 조건이 아니다. 로컬 적용 알림은 선택적이다.

「State sync: 인증된 실행 결과로 상태 동기」는 기능 방향·책임을 정한 요구사항이다. 정상 실행 도중에도 인증서와 적용 가능한 자료를 검증한 뒤 남은 실행을 줄일 수 있다. 인증서만으로 중단하거나 imported 결과에 own direct-execution signature를 추가하지 않는다. Wire / material format, 안전한 작업 전환·canonical writer·durability·recovery와 성능 검증은 구현 전 과제로 남긴다. 문서·sequence 수정은 실제 프로토콜 구현이나 안전성 증명 완료를 뜻하지 않는다.

## Current document priority and historical document synchronization

1. Latest explicit user decisions.
2. [Current implementation architecture](docs/README.md) and [Baton research paper](baton-paper.md), each for its stated scope.
3. Google Docs revisions below and the [archived detailed implementation specification](archive/2026-10-03-root-history/repository/research/archive/2026-10-03-implementation-outline/baton-implementation-spec.md) as provenance of the previous manual synchronization. Reconcile later revisions deliberately with current user decisions and Markdown; these snapshots do not replace the current architecture.
4. Historical Overpass outline/design/reviews, earlier handoffs, draft PR1, toy and archive material as cited context.

| Document | Native Google Doc | Verified revision |
|---|---|---|
| Paper: problem, mechanism, indispensable assumptions and conditional arguments, evaluation and limitations; eight sections | [Baton: Execution-Aware Ordering for Autobahn](https://docs.google.com/document/d/1PtUpMGMNMkyo1UEY2bNciJD3oIiGLRf407PW_T3Er5I/edit) | `ANLCKQmRJs9iN4rM0jd-sH8a8PE8D5cH8yKKe09aXUrk1TDg_eTC_hlTvuhi55xsE1tMpqBAhdXm9Fx3q9fP50wosMdRhe8BeNyUOj22FLg` |
| Specification: identity/context, admission, frontier, bounds/completion, proposal/slot/recovery, signing, retention and alternatives | [Baton — 구현 스펙](https://docs.google.com/document/d/10x4RvqG8e07Tai0s20e-wpCfz8COgH0JGR5daKE1xO8/edit) | `ANLCKQldFScCUBScmgJIyaYLPQlgBG0-jI0rlb5_U3v2gX0Xu8MAXhBxHcyjHNY82H-xP142eGYXdLIhDp3KqCjj-Q226UsQGutIAR_eHK0` |

The current GitHub repository is `djm07073/baton-research`; the existing local checkout name and origin remain unchanged. Historical citation titles and source URLs remain intact. These are manual counterparts, not automatic two-way synchronization. A later native revision or user decision requires deliberate reconciliation rather than overwriting either side.

## What changed from the earlier repository snapshot

- Renamed the conceptual project to Baton and use direction instead of plan in current narrative.
- Replaced sum-only selection by 2f+1-supported entire-prefix first, with sum-LCP fallback and valid actual-parent base fallback. Longest selection is relative to the completed bounded admissible candidate set.
- Precisely closed the local snapshot at 4f+1 admissions or fixed deadline, excluding excess/later reports. Local prefix uniqueness uses m<=4f+1; it does not extend to larger native recovery pools or different snapshots.
- Made immutable ordering frontier, raw-report support, bounded candidate validation and selected/emitted/signed prefix distinctions explicit.
- Strengthened the goal to leader/validator cut construction that preserves selected prefix membership AND exact leading sequence for the same canonical context. Pure advisory ordering over arbitrary independent native membership is insufficient for this requirement.
- Separated implementation contracts from the eight-section paper, retaining essential native sufficiency/recovery/no-wait uncertainty and conditional reuse in the paper.
- Kept authenticated proposal freeze, progressive native finality and the exact-order + f+1 execution-signature endpoint. Retention and common signing boundaries are required for eventual completion, not implied by cryptographic result safety.

## Core preservation obligation and unresolved bridge

For a selected valid prefix p protected by the adopted proposal, final executable order O after the immutable frontier must satisfy p ⪯ O in the same canonical input state/runtime. A1 and B1 membership with A1→X→B1 fails preservation of p=A1→B1. Extra native blocks cannot simply be discarded. A candidate missing a mandatory predecessor is invalid from the start.

The precise boundary between advisory selection and protected authenticated adoption is not yet specified. Cut no-wait allows a prepared valid actual-parent fallback before adoption; it does not license dropping an already protected prefix. Requiring an unavailable/unadopted prefix in every ready cut conflicts with that fallback. The user adopted preservation as a high-level requirement, not a finished availability/vote-validity/continuation/recovery construction.

Already-ready certified anchors are a possible native inclusion bridge; adding positive-adoption conditions to proposal/vote validity is another unadopted route. Neither has a completed cross-lane leading-prefix, no-wait or recovery proof. Do not silently force invalid/unavailable blocks, remove native extensions or restore the historical direction approval lock.

## Pinned source findings and caveats

Commonware commit: [`534af0ede48affd35b2111522527547b4cc9bf72`](https://github.com/commonwarexyz/monorepo/tree/534af0ede48affd35b2111522527547b4cc9bf72).

- Final proposal position is the **3f+1-th greatest** position. Ordinary payload B at position j needs at least 3f+1 pool votes with position>=j for finalized position>=j. Extension carry additionally uses native n−f support when the finalized proposal position reaches proposed tip. [tips.rs](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/tips.rs#L143)
- Vote position reflects local consecutive DA-voted valid path. A node may know a proposal without a local positive DA path; position 0 is then legal. [chain.rs](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1978), [proposal validity](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/view.rs#L2601)
- In the stated f=1,n=6 ordinary-payload example, h1,h2,b report B; h2's view vote is delayed; b knows B but votes low. Pool h1,b,h3,h4,h5 has positions [1,0,0,0,0]; fourth greatest is 0. Only three honest nodes lack B. Final tip G is unsettled below B, so this does not prove permanent exclusion or arbitrary later emission. Requiring a complete DA certificate for candidate eligibility could make this example inadmissible. It is source-level analytical reasoning, not an executed protocol trace.
- At/below a valid DA-certified anchor, B is part of the position-0 base ancestry. Low positions cannot exclude it. This distinguishes the anchor case from ordinary payload support, without proving the cross-lane leading order. [anchor selection](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1880)
- Native certificates, tip history and consensus retention do not supply dense ordered delivery, policy content, emission evidence or durable marshal cursor. Recovery must preserve terminal decisions, previously emitted prefixes and protected direction prefixes. Source inspection does not close the modified native proof.

## Four proposed defaults remain unadopted

| Choice | Recommended proposal, not adoption | Tradeoff | Exactly what remains blocked |
|---|---|---|---|
| Signing boundaries | Per-block deterministic statement boundaries with canonical parent/result checkpoints | More signatures and retained intermediate state than chunks | Exact range/statement schema and common-boundary result liveness |
| Same-supported-prefix tail | Keep valid incumbent; canonical tie-break if none | Less churn, but may give up a higher tail sum-LCP score | Deterministic tail/update rule; first-tier longest-prefix rule is already fixed |
| Policy availability | Bounded canonical policy bytes inline in authenticated proposal | Larger proposal versus commitment-only retrieval obligations | Concrete encoding/availability/recovery interface |
| Continuation | Finite valid initial-prefix ancestry-preserving permutation followed by original base sweep | Restricted reorder scope; compatibility and eligibility still need proof | Exact completion rule and its common-prefix proof; cannot alone guarantee native inclusion |

These choices do not automatically solve or select the native prefix-adoption bridge. τ/W/budget tuning and benefit are empirical questions. No new choices were adopted during synchronization.

## Draft PR1 and next validation boundary

[Draft PR1](https://github.com/djm07073/overpass-research/pull/1), head `0a06faff9b859da16b31f285c28128e0768662e2`, remains unmerged and open. Its P/Q/P+ B2-extension fixture, legal-transcript checks, unresolved-slot-skip negative mutation, policy freeze/recovery/cursor checks, matching-f+1 endpoint and common-resource E2E gates remain useful. Its finite D=[B,B,A] encoding is a test candidate, not an adopted continuation or proof of selected-prefix preservation.

Before treating that plan as current implementation work, add the protected-prefix adoption/inclusion/leading-order gate and verify it through native extension and view recovery. Preserve its distinction among exact-five L-QC, larger sticky pools and safe V-QC facts. No fixtures or gates were executed by this documentation update.

## Checks performed for this synchronization

- Re-read native revision-protected content, preserved all paper heading roles/eight sections and References, and checked the removed technical paragraphs were retained in the specification.
- Confirmed both native cross-document Workspace chips target the right files and show Baton titles; owner-only access remained unchanged.
- Checked final native PDF exports page by page: paper 14 pages, specification 10 pages. This is exported-PDF layout QA, not a live browser-canvas check.
- Checked descending native rank, certified-anchor non-exclusion wording and the analytical-transcript caveats. Corrected the final-position comparison to j-or-greater and Korean naming grammar without changing decisions.
- Markdown paragraph/citation preservation, local links, references and Git diff/whitespace are checked separately before commit. Git publication/CI status belongs in the delivery report; it is not native protocol validation.

No protocol implementation, native/toy tests, protocol compilation, benchmarks, spending, credential reconfiguration or draft-PR management was performed. Future implementation requires explicit scope; do not ask again for decisions already adopted.

## Targeted paper clarification: direction replies

On 2026-10-02, the user chose to omit a separate direction vote/ACK/Ready quorum. Paper §§3.3, 3.4 and 4.3 now explain the no-reply flow, repeated leader-local control cycle and why approval replies introduce a barrier without certifying canonical order or execution. The native paper revision above and local baton-paper.md were checked after this targeted insertion; the specification was not edited. Native proposal votes, irrevocable order/input-state gates and f+1 execution-result signatures remain. Prefix adoption/continuation/recovery proof obligations remain open. Discussion and connector readback are preserved locally in /Users/leojin/dev/baton/archive/2026-10-03-local-material/repository/research/multimmit_fork/DIRECTION_NO_REPLY_DECISION.md and its companion update record. No commit/push, protocol implementation or runtime tests were performed by this clarification.
