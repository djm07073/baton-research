# 블록 생성과 Block body 송수신

BlockService가 producer 본문을 생성·저장·전파·조회한다. 실제 tx 실행 판단은 Executor와 Runtime의 책임이다.

## 인터페이스 개요

Commonware의 `Automaton`, `Relay`, `Reporter`는 그대로 사용한다. 이를 위한 별도 `Consensus` trait를 다시 만들지 않는다. `BlockService`는 그 callback에 실제 body를 연결하는 application trait다.

```rust
use std::future::Future;

pub trait BlockService: Send {
    type ProducerContext: Send;
    type Digest: Send;
    type BlockRef: Send;
    type StoredBody: Send;
    type Retire: Send;
    type Error: Send;

    fn build(
        &mut self,
        context: Self::ProducerContext,
    ) -> impl Future<Output = Result<Option<Self::StoredBody>, Self::Error>> + Send;
    fn verify(
        &mut self,
        context: Self::ProducerContext,
        digest: Self::Digest,
    ) -> impl Future<Output = Result<bool, Self::Error>> + Send;
    fn fetch(
        &mut self,
        block: Self::BlockRef,
    ) -> impl Future<Output = Result<Self::StoredBody, Self::Error>> + Send;
    fn commitment(&self, body: &Self::StoredBody) -> Self::Digest;
    fn publish(&mut self, digest: Self::Digest) -> Result<(), Self::Error>;
    fn on_retire(&mut self, retired: Self::Retire) -> Result<(), Self::Error>;
}
```

`commitment`는 검증·보관한 body에 결속된 digest를 제공하는 accessor다. Native adapter는 이를 기존 propose receiver에 전달한다. `build`의 `Some(StoredBody)`는 body·필요 parent의 durable custody와 commitment 연결을 확인한 뒤에만 반환한다. `None`은 확정된 build decline이며, temporary missing dependency는 future / native receiver를 pending으로 둔다. `verify(false)`도 expected payload의 permanent invalidity에만 쓴다. Missing bytes·bad peer response는 fetch/retry, storage failure는 성공 custody를 발급하지 않는 경로다. `Error`를 native receiver closure나 `false`로 일괄 변환하지 않는다.

| 기존 Commonware 연결 | BlockService에 연결할 동작 |
|---|---|
| `Automaton::propose` | `build` 완료의 commitment를 기존 `oneshot::Receiver<Digest>`로 전달 |
| `Automaton::verify` | `verify`의 custody verdict를 기존 `oneshot::Receiver<bool>`로 전달 |
| `Relay::broadcast` | `publish`로 local publication 작업 예약. Remote receipt / custody ACK가 아님 |
| `Reporter::report` | Accepted artifact를 local 수신 경로로 전달해 StoredBody와 join. 느린 fetch를 callback에서 기다리지 않음 |

`Retire` 입력은 matching native lifecycle을 attachment에 전달할 제안 연결이다. 기존 `Relay`에 이미 retire callback가 있다고 가정하지 않는다. `publish`의 성공은 local 예약 경계일 뿐 전달 완료가 아니다. 실제 publication retry는 matching native `Retire`까지 유지하고, `on_retire`도 body archive 해제와 같은 사건으로 취급하지 않는다. Custody·history·serving references를 확인하는 release 계약은 §4.4 / §4.7에 남긴다. 위 두 receiver의 단계와 live closure 처리는 아래 existing callback 설명을 그대로 따른다.

| 경계 | 기존 API / 제안 연결 | 입력 → 처리 → 출력 |
|---|---|---|
| Producer payload 요청 | 기존 `Automaton::propose(Context)` | Native producer parent/context → pool batch와 body custody → payload digest |
| Payload 검증 | 기존 `Automaton::verify(Context, payload)` | Payload reference → body·parent lookup / 구조 검증 / durable custody → validity result |
| Body 전파 | 기존 `Relay::broadcast` + adapter | Digest → adapter owner의 body publication 요청 → Commonware broadcast / body P2P |
| Body 준비 | 제안 `StoredBody` | Exact context의 body·parent custody 완료 → local attachment readiness |
| Candidate header 관측 | 기존 `Reporter::report(Activity)` + adapter | Accepted native `TransactionBlock` artifact → exact header reference와 body join 입력 |
| 후보 실행 전달 | 제안 `CandidateBlock` | Authenticated native header와 exact body 대응 확인 → Baton block intake |
| Planning context | 신규 native owner hook | Leader view / V-QC parent / history / frontier → Baton planner read-only context |
| Policy adoption | 신규 native policy hook | Prepared matching candidate → proposal-bound frozen policy |
| Canonical 입력 전달 | 신규 evidence export + ordered delivery adapter | Exact authenticated native evidence / policy history → Executor ordered range |

`CandidateBlock`에는 body digest뿐 아니라 producer header와의 인증된 대응이 필요하다. Local build 직후 아직 header가 서명되지 않았다면 그 body는 local speculative candidate로 구분한다. Authenticated header를 아는 것과 final cut 포함도 별개다. 순서를 바꿀 수 있는 global frontier는 노드의 AppliedCursor로 대신하지 않는다.

기존 `Activity::ProtocolAccepted`는 contextually ready set에 들어간 exact authenticated artifact의 `Arc`를 제공한다. 여기서 Ready는 native artifact의 crypto/context admission이며 body 검증 완료나 native Retained completion이 아니다. Native `TransactionBlock` artifact에서 header를 얻어 StoredBody와 join하는 shared attachment를 재사용 경로로 검토한다. 두 사건의 도착 순서를 가정하지 않고 exact context·commitment·header identity로 대조한다. [Accepted activity](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/activity.rs#L1).

`ArtifactId`는 artifact 종류와 exact canonical artifact encoding 전체를 domain-separated hash로 식별한다. Native `TransactionBlock` artifact에는 `SignedTransactionBlock`의 encoding이 들어가므로 producer `header.block_ref`와 구분한다. [Artifact identity 계산](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/admission.rs#L145).

Reporter는 synchronous callback이고 native가 Feedback을 무시한다. Callback 안에서 느린 저장·본문 fetch·무제한 retry를 기다리지 않고 adapter owner에게 작업을 전달해야 한다. 구체 queue/budget은 미결정이며 알림의 acknowledged retention이나 lossless delivery를 가정하지 않는다. 관측 누락은 opportunistic candidate intake의 pending/retry 문제이지 native 진행을 멈추는 새 ACK 조건이 아니다. Canonical 순서에 필요한 exact witness export·retention 계약은 [§4.5](ordered-input.md#합의와-baton-연결)의 별도 연결이다. [Reporter dispatch](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/actor.rs#L1655).

`Automaton` callback는 future를 거쳐 `oneshot::Receiver<Digest>` 또는 `oneshot::Receiver<bool>`를 반환한다. 미가용 dependency는 그 receiver를 pending으로 유지하고, receiver 해소 뒤 native owner가 요청 correlation과 completion을 대조한다.

Live propose의 receiver가 닫히면 native executor는 commitment 없는 build completion을 전달한다. 현재 요청과 일치하는 build는 새 header를 만들지 않는 build decline으로 처리한다. Live verify의 receiver closure는 현재 유효한 task completion에서 `Fatal::Automaton`이며, `verify(false)`의 무효 payload 판정과 다르다. [Build completion 소비](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/executor.rs#L811), [현재 build의 decline](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1187), [Live validation completion](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/executor.rs#L848).

`Automaton`의 producer Context는 epoch·chain·height·producer parent header ID를 제공하며 leader V-QC / policy history를 제공하는 API가 아니다. Context와 commitment로 public header constructor/digest를 통해 exact reference를 재구성할 수 있다. 다만 propose·live verify·recovery에 같은 Context 타입이 쓰이고 callback에 mode tag가 없으므로, metadata 재구성만으로 signed artifact의 accepted/current 상태를 인정하지 않는다. [Header reconstruction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L126).

## Mempool에서 가져와 블록 생성

`propose(Context)`를 받으면 native가 지정한 producer-chain parent를 보존하고 pool에서 tx batch를 가져온다. Body codec·commitment·limits를 적용한 뒤 body와 필요한 parent custody를 durable 확보하고 digest를 반환한다. Native executor가 build job의 ID·generation·parent를 보존하고 completion을 원래 요청과 대조한다. Automaton Context에는 이 token이 포함되지 않으므로 attachment가 별도 job token API를 이미 받는다고 가정하지 않는다. [Build correlation](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/executor.rs#L683).

Producer lane의 parent-state filtering을 global canonical state로 취급하지 않는다. Stateful tx 성공·실패는 실제 ordered execution에서 판정한다.

Tx byte budget과 full encoded body size는 다르다. Tx 목록뿐 아니라 codec framing·metadata를 포함한 최종 본문을 bounded하게 구성해야 한다.

Commonware codec의 [`EncodeSize::encode_size`](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/codec/src/codec.rs#L26)는 선택한 body 타입의 전체 encoded size를 계산하는 연결 지점이다. 읽는 쪽에는 [`Read::Cfg`](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/codec/src/codec.rs#L197)로 타입별 decoding 제약을 전달할 수 있다. Body 필드·version·크기 제한과 구체 codec 구현은 미결정이며 application adapter에서 연결한다.

## 블록 전파·조회·custody

Commonware storage/archive, `broadcast::buffered`, `resolver::p2p`를 우선 활용한다. Broadcast의 bounded cache는 durable custody 저장소를 대신하지 않는다. Archive 저장 뒤 sync 완료, expected digest 검증, parent 복구와 startup 순서를 attachment에서 연결한다. [Broadcast](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/broadcast/src/buffered/mod.rs), [Resolver](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/mod.rs).

| 기존 primitive / API | 실제로 제공하는 것 | 새 body adapter가 책임질 것 |
|---|---|---|
| Archive `put`, `get`, `sync` / `start_sync` | Buffered write, key/index lookup, covering durable completion | Header ID→body commitment/context 대응, body/parent custody와 sync 완료 확인 |
| `broadcast::buffered` cache lookup | 최근 digest에 대한 bytes가 있으면 반환 | Expected body 검증, durable archive lookup / promotion |
| Buffered broadcast subscription | Cache hit 또는 앞으로 들어올 body를 기다리는 local waiter | Subscription과 active peer fetch를 구분 |
| Generic resolver `fetch` / shared subscribers | Key request·peer retry·subscriber sharing | Exact-key Consumer 검증, context correlation, pending wants / bytes / validation capacity |
| 기존 `resolver::p2p::Producer` trait | Key 요청을 application의 async bytes lookup으로 전달 | Archive-backed 구현 연결, body retention·request limits·storage error 처리 |

Archive `put` 성공만으로 custody를 인정하지 않는다. `sync` 또는 returned sync handle의 완료가 covering accepted writes의 durability 경계다. Existing `marshal::store::Blocks`는 finalized block을 global height와 digest로 저장하는 계약이므로, producer lane의 height만을 그대로 global archive index로 사용하면 lane·fork가 충돌할 수 있다. Native header ID와 body digest의 mapping 및 store layout은 선택할 adapter 책임이다. [Blocks storage contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/store.rs#L118), [Archive uniqueness](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/archive/immutable/mod.rs#L6).

Generic resolver의 `Consumer`가 returned bytes의 key validity를 판단한다. Wrong digest / invalid peer response, 올바른 bytes를 기다리던 subscriber의 취소, local archive sync failure는 다른 사건이다. Local storage failure나 stale generation을 peer-invalid 응답으로 처벌하지 않는다. Missing body는 fetch / dependency pending이며 expected payload의 permanent invalidity나 empty canonical slot의 증거가 아니다. [Resolver delivery contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/lib.rs#L149).

Fetch 취소로 validation 결과를 버릴 수 있어도 application의 custody writes가 rollback되었다는 뜻은 아니다. 선택할 storage의 mutation/completion lifetime을 subscriber 취소와 따로 연결한다. 예를 들어 `marshal::store::Blocks`의 mutating calls는 store를 소비하므로 dropped future/error가 handle을 잃게 하고 failed sync handle 뒤에는 store를 계속 사용할 수 없다. 이 store를 그대로 채택한 것은 아니며 [cancellation/storage 계약](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/store.rs#L115)을 확인해 adapter를 연결한다.

Targeted fetch는 지정한 targets 밖으로 자동 fallback하지 않는다. Outbound 요청은 `latest.primary` 안에서만 peers를 고르고 targets도 이 filter를 우회하지 않으므로, peer set 변경 후 serving 가능 여부를 adapter에서 연결해야 한다. [Resolver peer selection](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/p2p/mod.rs#L64). Generic resolver가 여러 concurrent fetch를 허용한다는 사실만으로 application의 pending key·subscriber·bytes·validation work가 bounded라고 주장하지 않는다. Native custody obligation과 취소 가능한 speculative subscriber를 owner가 따로 관리하고, 구체 admission bounds·retry/target policy는 빈칸에 남긴다.

`Relay::broadcast`는 synchronous callback이다. 느린 archive lookup·fetch·sync는 callback에서 기다리지 않고 body publication owner에게 전달한다. Native는 `Feedback::Closed`이면 해당 sender attempt를 미루고 그 외에는 전송을 시도한다. Remote body receipt나 custody quorum의 ACK를 받은 것은 아니다.

Native 송신기는 local sender가 전송 요청을 받아들인 뒤에도 같은 effect와 encoded bytes로 재시도한다. Core가 영속화된 후속 상태에 따라 Retire를 발급하면 해당 publication을 제거한다. 이 native retry를 report/direction 승인 대기로 바꾸지 않는다. [Relay dispatch](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/actor.rs#L2286), [Native retry ownership](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/egress.rs#L1).

Resolver `retain`은 pending fetch subscribers를 정한다. Fetch Complete/cancel, native publication Retire, body archive의 보관 해제는 서로 다른 lifecycle이다. Speculative subscriber를 취소하거나 cache에서 bytes를 지워도 live native custody·recovery·serving 의무가 끝났다고 가정하지 않는다. Body/history references와 durable handoff에 맞춘 retention·release 조건은 아래 빈칸에 남긴다. [Fetch subscriber retention](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/resolver/src/lib.rs#L216).

Native/application planes와 example 채널 번호는 [P2P message-plane 표](../overview/networking.md#p2p-연결과-message-planes)에 정리했다. Native data plane은 application body 전파 자체가 아니며, tx/body/report/direction의 실제 channel IDs는 미결정이다. [Channel wiring](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs#L358).
