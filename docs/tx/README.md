# Tx 레이어: 역할과 동작

TxPool이 tx를 접수·보관·선택한다. 정적 분석을 router에 둘지 블록 packing 시점에 둘지는 아직 결정하지 않았다.

## 역할과 책임

Client·peer의 tx를 받아 producer가 body를 만들 때 사용할 후보를 보관한다. 정적 분석은 tx payload에서 얻을 수 있는 특징을 추출한다. Routing이나 packing 정책은 이 특징을 입력으로 삼을 수 있으며, live balance·nonce·현재 부하를 정적 분석 결과라고 부르지 않는다.

재사용 후보로 별도 Constantinople의 `TransactionSource`와 pool 구현이 있다. TransactionSource는 parent `Header`·consensus `Round`·이미 선택한 signed tx byte count를 받아 `Vec<VerifiedTransaction>`을 반환하며 marshal의 finalized-block Update를 요구한다. Native producer Context와 digest callback는 이 타입을 제공하지 않으므로 selection과 canonical outcome adapter가 필요하다.

Commonware dependency rev도 native pin과 달라 direct Rust type compatibility는 미확인이다. 기존 crate 의존 또는 부분 구현 재사용, queue·cleanup 정책은 아래 빈칸에서 정한다. [TransactionSource](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/crates/mempool/src/lib.rs#L9), [Dependency pin](https://github.com/commonwarexyz/constantinople/blob/3b6c92e76bf582855615844a4175b8304808f6a9/Cargo.toml#L50).

Body builder가 `TxPool::select`를 요청하면 context와 limits에 맞는 후보를 반환한다. Proposal 생성과 취소는 mempool admission을 canonical outcome으로 바꾸지 않는다. Canonical 실행 결과가 도착한 뒤 해당 tx lifecycle을 정리한다.

## Tx P2P connection

기존 Commonware authenticated P2P 연결을 사용하고 tx 메시지는 native consensus 메시지와 구분된 logical channel로 연결한다. 물리 connection을 tx 전용으로 새로 만든다고 가정하지 않는다. Tx flood에 따른 report·body·native 처리의 자원 경쟁은 설계에서 다루며, quota·queue·runtime 배치의 구체 방식은 [§1.6](../overview/networking.md#p2p-연결과-message-planes)처럼 미결정이다.

Tx 전달 wire protocol, inventory/body 방식, producer 대상 선정, 재전송·중복 억제 방법은 비워 둔다. 실제 tx peer 수신이 `TxPool::admit`로 들어오는 연결만 인터페이스에 표시한다.

## 미결정 사항

| 항목 | 결정 |
|---|---|
| Tx format / ID / signature domain | |
| Mempool 재사용 구현체 | |
| 정적 분석 위치와 결과 schema | |
| Router / packing 정책과 교체 인터페이스 | |
| Tx P2P wire protocol / logical channel ID | |
| 후보 선택 순서 / byte·count limits | |
| 중복 tx의 application 의미 | |
| Admission 응답의 durability | |
| Proposal 취소 / 재선택 / 재전송 | |
| Canonical cleanup / retention / GC | |
