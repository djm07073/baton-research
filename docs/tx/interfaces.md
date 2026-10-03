# Tx 인터페이스

접수·후보 선택·proposal 결과·canonical 결과 반영의 경계를 정의한다. 정적 분석에 live balance나 nonce 판단을 섞지 않는다.

## 인터페이스 개요

```rust
use std::future::Future;

pub trait TxPool: Send {
    type Tx: Send;
    type Source: Send;
    type Admission: Send;
    type Selection: Send;
    type Batch: Send;
    type ProposalOutcome: Send;
    type CommitResult: Send;
    type Error: Send;

    fn admit(
        &mut self,
        tx: Self::Tx,
        source: Self::Source,
    ) -> impl Future<Output = Result<Self::Admission, Self::Error>> + Send;
    fn select(
        &mut self,
        request: Self::Selection,
    ) -> impl Future<Output = Result<Self::Batch, Self::Error>> + Send;
    fn on_proposal(
        &mut self,
        outcome: Self::ProposalOutcome,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
    fn on_commit(
        &mut self,
        result: Self::CommitResult,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
}

pub trait TxPolicy: Send {
    type Tx;
    type Features;
    type Decision;
    type Error;

    fn analyze(&self, tx: &Self::Tx) -> Result<Self::Features, Self::Error>;
    fn classify(&self, features: &Self::Features) -> Result<Self::Decision, Self::Error>;
}
```

`Selection`은 native producer context와 bounded selection limits를 식별한다. `Batch`는 후보이며 block 포함이나 tx 성공의 증거가 아니다. `on_proposal`은 local build 취소·재선택을, `on_commit`은 durable canonical 결과에 따른 lifecycle 갱신을 다룬다. 서로 같은 삭제 조건으로 취급하지 않는다.

`TxPolicy`의 입력은 tx payload에서 얻은 정적 특징이다. `Decision`을 producer routing이나 packing filtering에 연결하는 위치·규칙은 미결정이다. Live balance·nonce·부하 조회를 정적 분석에 섞지 않는다. 순수 계산을 수행하는 두 메서드의 CPU budget / worker 배치는 별도로 정한다.

| 제안 인터페이스 | 호출자 → 수신자 | 입력 | 출력 / 다음 처리 |
|---|---|---|---|
| `TxPool::admit` | Tx API / peer → tx layer | Canonical tx bytes, tx ID, source | Admission result와 후보 보관 |
| `TxPolicy::analyze` | TxPool admission / packing 위치 | Tx payload, 선택한 analysis version | Static features |
| `TxPolicy::classify` | TxPool / inclusion 연결부 | Static features | Routing / filtering decision; 위치·정책은 미결정 |
| `TxPool::select` | Producer adapter → pool | Native producer context, bounded limits | Candidate tx batch |
| `TxPool::on_proposal` | Producer adapter → pool | Attachment의 local request correlation, cancellation / local outcome | 후보 lifecycle 갱신; permanent deletion 여부는 canonical 근거와 구분 |
| `TxPool::on_commit` | Executor → pool | Durable ordered range의 tx 결과 | Canonical lifecycle 반영 |

Tx ID는 tx, external body commitment는 외부 body, native header ID는 epoch/chain/height/parent/commitment를 포함한 전체 producer header를 식별한다. 선택한 tx bytes와 body, authenticated header, canonical tx outcome의 대응은 adapter가 유지한다. Local request correlation도 native private build ID가 Context로 전달된다는 뜻은 아니다. API codec·ID 규칙·중복 의미는 아래 빈칸에서 정한다. [Producer header identity](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L113).
