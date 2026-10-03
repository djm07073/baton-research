# Baton implementation documentation

The current source is **[Start here](docs/README.md)**. Review layers and E2E cases through the [table of contents](docs/SUMMARY.md). This page preserves older links without duplicating the editable specification.

The source before page partitioning is preserved in the [archived snapshot](archive/2026-10-03-before-gitbook/IMPLEMENTATION_SPEC.md).

## Find older sections

<a id="11-네-레이어"></a>

[Architecture](docs/overview/architecture.md#four-layers)

<a id="12-레이어-사이의-입력과-출력"></a>

[Architecture](docs/overview/architecture.md#inputs-and-outputs-between-layers)

<a id="14-data-path-control-path-canonical-path"></a>

[Architecture](docs/overview/architecture.md#data-control-and-canonical-paths)

<a id="15-작업자와-authority"></a>

[Architecture](docs/overview/architecture.md#workers-and-decision-authority)

<a id="13-역할과-용어"></a>

[Roles and terminology](docs/overview/glossary.md#roles-and-terms)

<a id="16-p2p-연결과-message-planes"></a>

[P2P and message paths](docs/overview/networking.md#p2p-connections-and-message-planes)

<a id="17-rust-trait를-읽는-방법"></a>

[Reading the interfaces](docs/overview/interfaces.md#how-to-read-the-rust-traits)

<a id="31-역할과-책임"></a>

[Tx: roles and flow](docs/tx/README.md#roles-and-responsibilities)

<a id="33-tx-p2p-connection"></a>

[Tx: roles and flow](docs/tx/README.md#tx-p2p-connection)

<a id="34-미결정-사항"></a>

[Tx: roles and flow](docs/tx/README.md#open-decisions)

<a id="32-인터페이스-개요"></a>

[Tx interfaces](docs/tx/interfaces.md#interface-overview)

<a id="41-역할과-책임"></a>

[Consensus: native structure](docs/consensus/README.md#roles-and-responsibilities)

<a id="46-실제-native-actor와-파일-구조"></a>

[Consensus: native structure](docs/consensus/README.md#native-actors-and-source-layout)

<a id="42-인터페이스-개요"></a>

[Block construction and body exchange](docs/consensus/block-body.md#interface-overview)

<a id="43-mempool에서-가져와-블록-생성"></a>

[Block construction and body exchange](docs/consensus/block-body.md#select-transactions-and-build-a-block)

<a id="44-블록-전파조회custody"></a>

[Block construction and body exchange](docs/consensus/block-body.md#body-dissemination-lookup-and-custody)

<a id="45-합의와-baton-연결"></a>

[Finalized ordered input](docs/consensus/ordered-input.md#consensus-and-baton-integration)

<a id="47-미결정-사항"></a>

[Consensus open decisions](docs/consensus/decisions.md#open-decisions)

<a id="51-역할과-책임"></a>

[Baton: roles and reports](docs/baton/README.md#roles-and-responsibilities)

<a id="53-report-connection"></a>

[Baton: roles and reports](docs/baton/README.md#report-connection)

<a id="54-leader-report로-baton-생성"></a>

[Direction and rescheduling](docs/baton/direction.md#leader-choose-direction-from-reports)

<a id="55-leader-producer들에게-baton-전파"></a>

[Direction and rescheduling](docs/baton/direction.md#leader-disseminate-direction)

<a id="56-non-leader-실행재실행-요청"></a>

[Direction and rescheduling](docs/baton/direction.md#non-leader-request-execution-and-rescheduling)

<a id="58-미결정-사항"></a>

[Direction and rescheduling](docs/baton/direction.md#open-decisions)

<a id="52-인터페이스-개요"></a>

[Baton interfaces](docs/baton/interfaces.md#interface-overview)

<a id="57-cut-commit-요청-전달"></a>

[Baton interfaces](docs/baton/interfaces.md#finalized-state-progress-notifications)

<a id="61-역할과-책임"></a>

[Execution: responsibilities](docs/execution/README.md#roles-and-responsibilities)

<a id="66-미결정-사항"></a>

[Execution: responsibilities](docs/execution/README.md#open-decisions)

<a id="62-인터페이스-개요"></a>

[Executor, Runtime, and certification interfaces](docs/execution/interfaces.md#interface-overview)

<a id="68-결과-인증-trait"></a>

[Executor, Runtime, and certification interfaces](docs/execution/interfaces.md#result-certification-trait)

<a id="63-qmdb-state-관리와-재사용-경계"></a>

[QMDB branches and canonical application](docs/execution/qmdb.md#qmdb-state-and-reuse-boundaries)

<a id="64-실행-요청을-받으면-분기-tree-정리"></a>

[QMDB branches and canonical application](docs/execution/qmdb.md#manage-the-branch-tree-for-execution-requests)

<a id="65-commit-요청을-받으면-branch를-canonical로-만들기"></a>

[QMDB branches and canonical application](docs/execution/qmdb.md#commit-a-branch-to-canonical-state)

<a id="67-state-sync-인증된-실행-결과로-상태-동기"></a>

[State sync from certified results](docs/execution/state-sync.md#state-sync-from-certified-execution-results)

<a id="21-전체-e2e-tx-입력부터-canonical-state까지"></a>

[Normal flow: transaction to state](docs/e2e/normal.md#full-e2e-transaction-input-to-canonical-state)

<a id="22-tx-lifecycle-신규중복잘못된-tx"></a>

[Normal flow: transaction to state](docs/e2e/normal.md#tx-lifecycle-new-duplicate-and-invalid-transactions)

<a id="23-block-lifecycle-mempool--propose--body-전파"></a>

[Block body exchange](docs/e2e/block-body.md#block-lifecycle-mempool--propose--body-dissemination)

<a id="24-block-lifecycle-verify본문-누락검증-실패"></a>

[Block body exchange](docs/e2e/block-body.md#body-lookup-verification-and-missing-content-handling)

<a id="214-native-합의-정상-경로-producer-da--leader-proposal--finality"></a>

[Native proposal, DA, and finality](docs/e2e/native-consensus.md#normal-native-consensus-producer-da--leader-proposal--finality)

<a id="25-baton-lifecycle-leader-report-수집과-direction-전파"></a>

[Leader reports and proposal races](docs/e2e/leader.md#leader-lifecycle-collect-reports-and-disseminate-direction)

<a id="211-planner-completion과-proposal-freeze의-경합"></a>

[Leader reports and proposal races](docs/e2e/leader.md#planner-completion-versus-proposal-freeze)

<a id="26-baton-lifecycle-non-leader의-direction재실행-요청"></a>

[Direction receipt and reexecution](docs/e2e/reschedule.md#non-leader-lifecycle-direction-and-rescheduling)

<a id="27-cut-commit--ordered-range--실행-commit"></a>

[Finalized order and canonical application](docs/e2e/canonical.md#cut-commit--ordered-range--execution-commit)

<a id="28-execution-lifecycle-qmdb-분기-생성과-canonical-승격"></a>

[Finalized order and canonical application](docs/e2e/canonical.md#execution-lifecycle-qmdb-branches-and-canonical-promotion)

<a id="212-startup-custody를-준비한-뒤-native-recovery"></a>

[Startup, restart, and recovery](docs/e2e/recovery.md#startup-prepare-custody-before-native-recovery)

<a id="29-재시작과-backfill"></a>

[Startup, restart, and recovery](docs/e2e/recovery.md#restart-and-backfill)

<a id="210-결과-endpoint-direct-execution과-f1-인증"></a>

[Executor certification and queries](docs/e2e/results.md#result-endpoint-direct-execution-and-f1-certification)

<a id="213-state-sync-인증된-실행-결과로-상태-동기"></a>

[State sync from certified results](docs/e2e/state-sync.md#state-sync-from-certified-execution-results)

<a id="71-commonware-integration-anchors"></a>

[Commonware integration and development order](docs/reference/integration.md#commonware-integration-anchors)

<a id="72-개발-단계와-확인할-흐름"></a>

[Commonware integration and development order](docs/reference/integration.md#development-stages-and-validation-flows)

<a id="73-컴포넌트별-검증-케이스"></a>

[Cases to verify](docs/reference/verification.md#verification-cases-by-component)

<a id="8-참고자료와-문서-상태"></a>

[Sources and document status](docs/reference/sources.md)

<a id="1-전체-구조"></a>

[Architecture](docs/overview/architecture.md)

<a id="2-e2e-lifecycle과-sequence-diagram"></a>

[Normal flow: transaction to state](docs/e2e/normal.md)

<a id="3-tx-router--tx-mempool-레이어"></a>

[Tx: roles and flow](docs/tx/README.md)

<a id="4-consensus-레이어-commonware-multimmit"></a>

[Consensus: native structure](docs/consensus/README.md)

<a id="5-baton-레이어"></a>

[Baton: roles and reports](docs/baton/README.md)

<a id="6-실행-레이어와-qmdb"></a>

[Execution: responsibilities](docs/execution/README.md)

<a id="7-실제-example에-연결할-지점과-개발-순서"></a>

[Commonware integration and development order](docs/reference/integration.md)
