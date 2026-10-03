# Summary

* [시작하기](README.md)

## 전체 구조

* [전체 아키텍처](overview/architecture.md)
* [역할과 공통 용어](overview/glossary.md)
* [Rust 인터페이스](overview/rust-interfaces.md)
* [P2P와 메시지 경로](overview/networking.md)
* [인터페이스 읽는 방법](overview/interfaces.md)

## Tx 레이어

* [Tx 레이어: 역할과 동작](tx/README.md)
* [Tx 인터페이스](tx/interfaces.md)

## Consensus 레이어

* [Consensus: 역할과 native 구조](consensus/README.md)
* [블록 생성과 Block body 송수신](consensus/block-body.md)
* [확정 실행 순서 전달](consensus/ordered-input.md)
* [Consensus 미결정 사항](consensus/decisions.md)

## Baton 레이어

* [Baton: 역할과 report 경로](baton/README.md)
* [Direction 선택과 재실행](baton/direction.md)
* [Baton 인터페이스와 로컬 진행 알림](baton/interfaces.md)

## Execution 레이어

* [Execution: 역할과 책임](execution/README.md)
* [Executor·Runtime·결과 인증 인터페이스](execution/interfaces.md)
* [QMDB 분기·재사용·상태 적용](execution/qmdb.md)
* [State sync: 인증된 실행 결과로 상태 동기](execution/state-sync.md)

## E2E 케이스

* [정상 흐름: tx 접수부터 상태 적용까지](e2e/normal.md)
* [Block body 송수신](e2e/block-body.md)
* [블록 제안·DA·cut 확정](e2e/native-consensus.md)
* [Leader report·direction과 proposal 경합](e2e/leader.md)
* [Direction 수신과 재실행](e2e/reschedule.md)
* [확정 순서와 canonical 상태 적용](e2e/canonical.md)
* [시작·재시작과 이력 복구](e2e/recovery.md)
* [Executor 간 결과 인증과 조회](e2e/results.md)
* [State sync: 인증된 실행 결과로 상태 동기](e2e/state-sync.md)

## 개발·참고자료

* [Commonware 연결 지점과 개발 순서](reference/integration.md)
* [검증할 케이스](reference/verification.md)
* [참고자료와 문서 상태](reference/sources.md)
