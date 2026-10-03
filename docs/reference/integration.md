# Commonware 연결 지점과 개발 순서

Pinned Commonware source와 example wiring을 실제 개발할 bridge에 대응시킨다. 단계는 개발 계획이며 구현 완료 기록이 아니다.

## Commonware integration anchors

모든 native 링크는 commit `534af0ede48affd35b2111522527547b4cc9bf72`에 고정한다. 이 표의 신규 bridge는 개발할 계약이며 구현 완료 상태가 아니다.

조립 진입점은 `log-multimmit/main.rs`다. 기존 example은 `commonware_runtime::tokio::Runner`를 만들고, 그 context에서 `commonware_p2p::authenticated::discovery::Network`와 native logical channels를 등록한다. Application을 Automaton·Relay로 넘기고 `commonware_parallel::Rayon` native crypto strategy·profile·committee를 EngineConfig에 연결한 뒤 `network.start()` → `engine.start(...)` → `running.ready()`로 시작한다. Baton attachment에서는 [startup 흐름](../e2e/recovery.md#startup-custody를-준비한-뒤-native-recovery)에 따라 body service를 먼저 준비하고 application planes·execution을 연결한다. [Runtime / network assembly](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs#L293).

이 example의 committee는 ordinary BLS roster와 DA/nullification용 독립 threshold sharing을 mock seed에서 만든다. 이것은 source example의 key setup이며 Baton의 production setup 정책을 확정한 것이 아니다. Transport identity, native signing domain, application tx/result signature domain을 하나의 키·namespace로 가정하지 않는다. [Example key material](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs#L17).

| 연결 지점 | 가져올 것 | 변경 / 신규 연결 |
|---|---|---|
| [Example main](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs#L358) | Runtime, committee, authenticated discovery network, native channel / Engine wiring | Tx / body / report / direction channel과 Baton / execution actor 시작 |
| [Example Application](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/application/actor.rs#L40) | Automaton / Relay trait 경계와 main의 Reporter wiring | Mock body callbacks를 pool·body·custody adapter로 교체, accepted-artifact candidate intake에 existing Reporter 활용 |
| [Native view owner](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/view.rs#L1269) | Actual leader proposal context와 native owner authority | Read-only planning context export / prepared result correlation |
| [Leader block](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L563) | LeaderBlock 구조 / canonical codec | Frozen policy binding와 proposal validity / recovery 연결 |
| [Finality owner](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/finality.rs) | Exact native facts와 인증 근거의 provenance | Resumable evidence export / retention handoff / history backfill |
| [Native tip algebra](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/tips.rs#L143) | Native extraction / settledness 규칙 | Verified shared extraction facade와 dense ordered delivery; private algebra 접근 문제 해결 |
| [QMDB Stateful](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/mod.rs) | Batch fork / merkleize / apply, pending-state 관리 | Multimmit exact execution order에 맞는 branch / canonical adapter |
| [Cryptography interfaces](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/cryptography/src/lib.rs) | Namespace와 message를 받는 서명·검증 primitive | ExecutionStatement encoding·epoch key 연결과 signer / result collector 구성 |
| [Codec interfaces](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/codec/src/lib.rs) | Write / Read / EncodeSize와 encoding·decoding 기본 API | Tx / body / report / direction / result의 schema·version·limits 연결 |

#### 실제 소스를 따라 읽는 순서

소스 탐색과 아래 개발 단계는 다르다. 먼저 upstream이 소유하는 흐름을 확인한 뒤 application / Baton 연결부를 개발한다.

Tx 저장·선택은 [§3.1의 pool 재사용 후보](../tx/README.md#역할과-책임), body 보관·전파·fetch는 [§4.4의 primitive 표](../consensus/block-body.md#블록-전파조회custody)를 먼저 읽고, 아래 순서에서 native callback과 연결한다.

같은 pin의 [reshare validator 조립](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/reshare/src/validator.rs#L122)은 resolver·buffer·archives·Marshal·Stateful·application wrapper에 어떤 handles를 넘기는지 한 파일에서 읽는 참고다. 이 Simplex example의 [Deferred wrapper](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/marshal/standard/deferred.rs#L488)는 digest를 durability 전에 반환하고 별도 certify gate에서 기다린다. Native Multimmit의 producer Context·custody/signing·recovery 계약을 그대로 제공하는 adapter로 취급하지 않는다.

| 순서 | 소스 진입점 | 읽을 때 확인할 질문 |
|---|---|---|
| 1. Node 조립 | [log-multimmit main.rs](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/examples/log-multimmit/src/main.rs) | Network channel, application, Engine config는 어디서 연결되는가? |
| 2. Native 시작·복구 | [Engine::start](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/engine.rs) | Journal replay와 recovered-payload verify가 actor 시작보다 앞서는 이유는 무엇인가? |
| 3. Wire→observation→verification | [Wire types](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/wire.rs), [Batcher](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/batcher/mod.rs) | Untrusted observation와 owner가 발급한 verification completion은 어떻게 구분되는가? |
| 4. Native 상태 소유자 | [Machine ownership](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/mod.rs), [Voter executor](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/voter/executor.rs) | Semantic state와 async job 실행은 누가 각각 소유하는가? |
| 5. Producer와 leader | [Chain](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs), [View](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/view.rs) | Payload build callback와 leader의 여러 lane cut 구성은 어떻게 다른가? |
| 6. Native 출력 경계 | [Finality](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/finality.rs), [State-machine contract](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md) | 어떤 evidence를 export·보관해야 application이 dense order를 복구할 수 있는가? |
| 7. QMDB 내부 | [QMDB lifecycle](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/mod.rs), [Batch chain](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/storage/src/qmdb/batch_chain.rs) | Pending checkpoint, actual DB ancestor, operations commitment의 관계는 무엇인가? |
| 8. Apply와 durable 완료 | [DatabaseSet / Barrier](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/db/mod.rs), [Stateful processor](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/glue/src/stateful/actor/processor/mod.rs) | Readable callback과 flush ACK는 어느 지점에서 갈라지고 Executor가 무엇을 추가해야 하는가? |

## 개발 단계와 확인할 흐름

| 단계 | 개발할 연결 | 확인할 lifecycle |
|---|---|---|
| 1 | 기존 Multimmit example 구조와 버전 고정 | 기존 native producer / DA / consensus 흐름 |
| 2 | TxPool / BlockService | §2.2–2.4, 업무 runtime 없이도 tx body 전달 확인 |
| 3 | Orderer / native evidence export | Native sparse finality → contiguous exact inputs, gap backfill |
| 4 | Executor / Runtime / QMDB | §2.7–2.10·2.13, canonical range·결과 인증·Executor peer state sync·durable state 연결 |
| 5 | Baton의 block 수신 / scheduling / reschedule | §2.1·2.6·2.8, 동일 prefix 재사용과 suffix 재실행 |
| 6 | Baton report / Planner / direction 전파 | §2.5, no-report·late-report·leader 교체·cut preemption |
| 7 | Native proposal policy / continuation / recovery 연결 | Selected prefix inclusion + exact leading order + no-wait 검증 |

단계 7의 native adoption·continuation 증명이 없으면 advisory scheduling 연결과 protected-prefix Baton 통합을 같은 완료 상태로 부르지 않는다. 테스트 workload는 application semantics 결정 후 정하며 Bank를 먼저 개발하는 단계는 두지 않는다.

단계 4에서는 [§4.5의 Orderer→Executor::commit 직접 연결](../consensus/ordered-input.md#합의와-baton-연결)로 단계 3의 canonical 입력을 execution에 먼저 전달하고, 단계 5에서 candidate intake·speculation·reschedule을 더한다. [§2.10의 direct-result signer / collector / query 연결](../e2e/results.md#결과-endpoint-direct-execution과-f1-인증)과 [§2.13의 Executor peer state sync](../e2e/state-sync.md#state-sync-인증된-실행-결과로-상태-동기)도 단계 4의 Executor 내부 연결 과제다. Baton 간 결과 전달로 구현하지 않는다. 구체 signature boundary·root construction·codec·key 연결은 빈 결정 칸을 정한 뒤 구현한다.
