# Baton Docs

Commonware Multimmit 위에 Tx·Baton·Execution을 연결하는 구현 설계 문서다. **페이지별로 읽고 검토하며, 수정할 원본은 이 docs 폴더의 Markdown이다.**

## 먼저 읽을 페이지

| 순서 | 페이지 | 확인할 내용 |
|---|---|---|
| 1 | [전체 아키텍처](overview/architecture.md) | 네 레이어와 데이터·제어·확정 경로 |
| 2 | [역할과 공통 용어](overview/glossary.md) | 각 모듈의 책임과 완료 조건 |
| 3 | [정상 E2E](e2e/normal.md) | Tx가 block·실행 결과·로컬 상태가 되는 과정 |
| 4 | [Execution 역할과 책임](execution/README.md) | Executor의 state finalization·state sync |

## 문서 구성

- **전체 구조:** 아키텍처, 용어, P2P와 인터페이스 읽는 방법
- **Tx:** 접수·mempool·정적 분석·후보 선택
- **Consensus:** Multimmit·Block body 송수신·확정 순서 전달
- **Baton:** Reports·direction·사전 실행·재실행 조율
- **Execution:** Runtime·QMDB·결과 인증·state sync·복구
- **E2E:** 정상 흐름, 본문 송수신, native 합의, leader, 재실행, canonical 적용, 복구, 결과 인증, state sync
- **개발·참고자료:** Commonware 소스 연결 지점과 개발·검증 계획

전체 페이지 목록은 [목차](SUMMARY.md)에서 볼 수 있다. 각 레이어 페이지는 책임·인터페이스를, E2E 페이지는 sequence와 사건 순서를 설명한다.

## 현재 정한 책임

확정 입력은 **Orderer → Executor**로 직접 전달한다. **Executor ↔ Executor**가 실행 서명·인증서·change set을 교환하고 state finalization·state sync를 처리한다. Baton은 사전 실행·재실행과 report·direction을 조율하며 결과 인증이나 상태 적용의 승인·대기 조건이 아니다.

## 문서 상태

설계와 Commonware source 연결을 정리한 구현 전 문서다. 실제 프로토콜 구현·native 통합 증명·E2E·성능 결과는 아직 없다. 기존 Commonware API와 앞으로 만들 application 계약을 구분하고, 미결정 정책의 결정 칸은 비워 둔다. Bank 업무 모델은 현재 범위에서 제외한다.
