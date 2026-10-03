# Baton 구현 스펙 — 페이지별 문서

현재 문서 원본은 **[Baton Docs](docs/README.md)**다. [전체 목차](docs/SUMMARY.md)에서 레이어별·E2E 케이스별로 검토한다. 이 파일은 이전 링크를 위한 진입점이며 본문을 중복해서 관리하지 않는다.

분리 직전 원본은 [보관 스냅샷](archive/2026-10-03-before-gitbook/IMPLEMENTATION_SPEC.md)에 있다.

## 이전 섹션 찾아보기

<a id="11-네-레이어"></a>

[전체 아키텍처](docs/overview/architecture.md#네-레이어)

<a id="12-레이어-사이의-입력과-출력"></a>

[전체 아키텍처](docs/overview/architecture.md#레이어-사이의-입력과-출력)

<a id="14-data-path-control-path-canonical-path"></a>

[전체 아키텍처](docs/overview/architecture.md#data-path-control-path-canonical-path)

<a id="15-작업자와-authority"></a>

[전체 아키텍처](docs/overview/architecture.md#작업자와-authority)

<a id="13-역할과-용어"></a>

[역할과 공통 용어](docs/overview/glossary.md#역할과-용어)

<a id="16-p2p-연결과-message-planes"></a>

[P2P와 메시지 경로](docs/overview/networking.md#p2p-연결과-message-planes)

<a id="17-rust-trait를-읽는-방법"></a>

[인터페이스 읽는 방법](docs/overview/interfaces.md#rust-trait를-읽는-방법)

<a id="31-역할과-책임"></a>

[Tx 레이어: 역할과 동작](docs/tx/README.md#역할과-책임)

<a id="33-tx-p2p-connection"></a>

[Tx 레이어: 역할과 동작](docs/tx/README.md#tx-p2p-connection)

<a id="34-미결정-사항"></a>

[Tx 레이어: 역할과 동작](docs/tx/README.md#미결정-사항)

<a id="32-인터페이스-개요"></a>

[Tx 인터페이스](docs/tx/interfaces.md#인터페이스-개요)

<a id="41-역할과-책임"></a>

[Consensus: 역할과 native 구조](docs/consensus/README.md#역할과-책임)

<a id="46-실제-native-actor와-파일-구조"></a>

[Consensus: 역할과 native 구조](docs/consensus/README.md#실제-native-actor와-파일-구조)

<a id="42-인터페이스-개요"></a>

[블록 생성과 Block body 송수신](docs/consensus/block-body.md#인터페이스-개요)

<a id="43-mempool에서-가져와-블록-생성"></a>

[블록 생성과 Block body 송수신](docs/consensus/block-body.md#mempool에서-가져와-블록-생성)

<a id="44-블록-전파조회custody"></a>

[블록 생성과 Block body 송수신](docs/consensus/block-body.md#블록-전파조회custody)

<a id="45-합의와-baton-연결"></a>

[확정 실행 순서 전달](docs/consensus/ordered-input.md#합의와-baton-연결)

<a id="47-미결정-사항"></a>

[Consensus 미결정 사항](docs/consensus/decisions.md#미결정-사항)

<a id="51-역할과-책임"></a>

[Baton: 역할과 report 경로](docs/baton/README.md#역할과-책임)

<a id="53-report-connection"></a>

[Baton: 역할과 report 경로](docs/baton/README.md#report-connection)

<a id="54-leader-report로-baton-생성"></a>

[Direction 선택과 재실행](docs/baton/direction.md#leader-report로-baton-생성)

<a id="55-leader-producer들에게-baton-전파"></a>

[Direction 선택과 재실행](docs/baton/direction.md#leader-producer들에게-baton-전파)

<a id="56-non-leader-실행재실행-요청"></a>

[Direction 선택과 재실행](docs/baton/direction.md#non-leader-실행재실행-요청)

<a id="58-미결정-사항"></a>

[Direction 선택과 재실행](docs/baton/direction.md#미결정-사항)

<a id="52-인터페이스-개요"></a>

[Baton 인터페이스와 로컬 진행 알림](docs/baton/interfaces.md#인터페이스-개요)

<a id="57-cut-commit-요청-전달"></a>

[Baton 인터페이스와 로컬 진행 알림](docs/baton/interfaces.md#확정-상태-진행-알림)

<a id="61-역할과-책임"></a>

[Execution: 역할과 책임](docs/execution/README.md#역할과-책임)

<a id="66-미결정-사항"></a>

[Execution: 역할과 책임](docs/execution/README.md#미결정-사항)

<a id="62-인터페이스-개요"></a>

[Executor·Runtime·결과 인증 인터페이스](docs/execution/interfaces.md#인터페이스-개요)

<a id="68-결과-인증-trait"></a>

[Executor·Runtime·결과 인증 인터페이스](docs/execution/interfaces.md#결과-인증-trait)

<a id="63-qmdb-state-관리와-재사용-경계"></a>

[QMDB 분기·재사용·상태 적용](docs/execution/qmdb.md#qmdb-state-관리와-재사용-경계)

<a id="64-실행-요청을-받으면-분기-tree-정리"></a>

[QMDB 분기·재사용·상태 적용](docs/execution/qmdb.md#실행-요청을-받으면-분기-tree-정리)

<a id="65-commit-요청을-받으면-branch를-canonical로-만들기"></a>

[QMDB 분기·재사용·상태 적용](docs/execution/qmdb.md#commit-요청을-받으면-branch를-canonical로-만들기)

<a id="67-state-sync-인증된-실행-결과로-상태-동기"></a>

[State sync: 인증된 실행 결과로 상태 동기](docs/execution/state-sync.md#state-sync-인증된-실행-결과로-상태-동기)

<a id="21-전체-e2e-tx-입력부터-canonical-state까지"></a>

[정상 흐름: tx 접수부터 상태 적용까지](docs/e2e/normal.md#전체-e2e-tx-입력부터-canonical-state까지)

<a id="22-tx-lifecycle-신규중복잘못된-tx"></a>

[정상 흐름: tx 접수부터 상태 적용까지](docs/e2e/normal.md#tx-lifecycle-신규중복잘못된-tx)

<a id="23-block-lifecycle-mempool--propose--body-전파"></a>

[Block body 송수신](docs/e2e/block-body.md#block-lifecycle-mempool--propose--body-전파)

<a id="24-block-lifecycle-verify본문-누락검증-실패"></a>

[Block body 송수신](docs/e2e/block-body.md#block-body-송수신-조회검증누락-처리)

<a id="214-native-합의-정상-경로-producer-da--leader-proposal--finality"></a>

[블록 제안·DA·cut 확정](docs/e2e/native-consensus.md#native-합의-정상-경로-producer-da--leader-proposal--finality)

<a id="25-baton-lifecycle-leader-report-수집과-direction-전파"></a>

[Leader report·direction과 proposal 경합](docs/e2e/leader.md#baton-lifecycle-leader-report-수집과-direction-전파)

<a id="211-planner-completion과-proposal-freeze의-경합"></a>

[Leader report·direction과 proposal 경합](docs/e2e/leader.md#planner-completion과-proposal-freeze의-경합)

<a id="26-baton-lifecycle-non-leader의-direction재실행-요청"></a>

[Direction 수신과 재실행](docs/e2e/reschedule.md#baton-lifecycle-non-leader의-direction재실행-요청)

<a id="27-cut-commit--ordered-range--실행-commit"></a>

[확정 순서와 canonical 상태 적용](docs/e2e/canonical.md#cut-commit--ordered-range--실행-commit)

<a id="28-execution-lifecycle-qmdb-분기-생성과-canonical-승격"></a>

[확정 순서와 canonical 상태 적용](docs/e2e/canonical.md#execution-lifecycle-qmdb-분기-생성과-canonical-승격)

<a id="212-startup-custody를-준비한-뒤-native-recovery"></a>

[시작·재시작과 이력 복구](docs/e2e/recovery.md#startup-custody를-준비한-뒤-native-recovery)

<a id="29-재시작과-backfill"></a>

[시작·재시작과 이력 복구](docs/e2e/recovery.md#재시작과-backfill)

<a id="210-결과-endpoint-direct-execution과-f1-인증"></a>

[Executor 간 결과 인증과 조회](docs/e2e/results.md#결과-endpoint-direct-execution과-f1-인증)

<a id="213-state-sync-인증된-실행-결과로-상태-동기"></a>

[State sync: 인증된 실행 결과로 상태 동기](docs/e2e/state-sync.md#state-sync-인증된-실행-결과로-상태-동기)

<a id="71-commonware-integration-anchors"></a>

[Commonware 연결 지점과 개발 순서](docs/reference/integration.md#commonware-integration-anchors)

<a id="72-개발-단계와-확인할-흐름"></a>

[Commonware 연결 지점과 개발 순서](docs/reference/integration.md#개발-단계와-확인할-흐름)

<a id="73-컴포넌트별-검증-케이스"></a>

[검증할 케이스](docs/reference/verification.md#컴포넌트별-검증-케이스)

<a id="8-참고자료와-문서-상태"></a>

[참고자료와 문서 상태](docs/reference/sources.md)

<a id="1-전체-구조"></a>

[전체 아키텍처](docs/overview/architecture.md)

<a id="2-e2e-lifecycle과-sequence-diagram"></a>

[정상 흐름: tx 접수부터 상태 적용까지](docs/e2e/normal.md)

<a id="3-tx-router--tx-mempool-레이어"></a>

[Tx 레이어: 역할과 동작](docs/tx/README.md)

<a id="4-consensus-레이어-commonware-multimmit"></a>

[Consensus: 역할과 native 구조](docs/consensus/README.md)

<a id="5-baton-레이어"></a>

[Baton: 역할과 report 경로](docs/baton/README.md)

<a id="6-실행-레이어와-qmdb"></a>

[Execution: 역할과 책임](docs/execution/README.md)

<a id="7-실제-example에-연결할-지점과-개발-순서"></a>

[Commonware 연결 지점과 개발 순서](docs/reference/integration.md)
