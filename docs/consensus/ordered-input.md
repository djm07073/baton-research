# 확정 실행 순서 전달

Orderer가 검증한 native 증거와 이력에서 연속 확정 입력을 만들어 Executor에 직접 전달한다. Native sparse finality와 dense 실행 순서는 구분한다.

## 합의와 Baton 연결

```rust
use std::future::Future;

pub trait Orderer: Send {
    type Evidence: Send;
    type OrderedRange: Send;
    type CommitResult: Send;
    type Recovery: Send;
    type Error: Send;

    fn record(
        &mut self,
        evidence: Self::Evidence,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
    fn next_range(
        &mut self,
    ) -> impl Future<Output = Result<Self::OrderedRange, Self::Error>> + Send;
    fn acknowledge(
        &mut self,
        result: Self::CommitResult,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
    fn recover(
        &mut self,
        recovery: Self::Recovery,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
}
```

`Evidence`는 exact authenticated source witness와 해당 policy/history 해석을 포함하는 연결이다. Native 알림이나 normalized projection만 저장했다고 witness 보관이 끝나지 않는다. `next_range`는 contiguous irrevocable 입력만 반환하고 unresolved gap에서는 backfill / pending으로 둔다. Included body 미가용을 empty로 바꾸지 않는다. `acknowledge`는 같은 exact range의 durable `CommitResult`를 확인한 뒤 application delivery cursor를 진행한다. Native vote ACK나 body release 요청이 아니다.

이 trait는 이력 보관·순서 해석·전달의 공개 경계를 합친 것이다. Source witness export와 native policy adoption hook은 기존 native owner에 붙일 별도 연결 과제로 남으며, Orderer가 native proposal을 스스로 인증·채택하는 권한을 갖지 않는다.

정상 native 메시지 흐름은 [§2.14 sequence](../e2e/native-consensus.md#native-합의-정상-경로-producer-da--leader-proposal--finality)에서 함께 볼 수 있다.

Native votes와 finality는 기존 core가 담당한다. 각 producer는 독립 lane의 application commitment를 담은 signed header를 전파하고, 여러 producer chains의 순서 근거는 별도 leader chain에 모인다. 각 view의 leader는 earlier V-QC parent와 lane별 anchored path를 transaction-free `LeaderBlock`에 넣는다. 모든 descendant의 DA certificate를 기다리는 구조는 아니며, native 조건을 만족하는 locally DA-voted 연속 suffix도 proposal에 포함할 수 있다. [Producer / leader chain 구조](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/mod.rs#L9), [Proposal / direct vote](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md#L309).

Native owner가 구성한 `LeaderBlock`의 canonical digest가 leader proposal 식별자이며, `VoteBody`는 이 digest를 round·position·extension과 함께 참조한다. [LeaderBlock digest](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L643), [VoteBody 구성](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/vote.rs#L119).

Producer별 anchor는 해당 lane의 제안 경로가 시작하는 기준 block reference다. Parent V-QC에서 물려받은 safe-tip reference 또는 proposal에 함께 실은 더 높은 DA certificate로 표현하며, leader proposal이 참조하는 parent V-QC와 별도의 좌표다. [Anchor 표현](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/block.rs#L399).

Validator는 producer별 제안의 anchor 다음에서 자신이 DA vote한 경로와 연속으로 일치하는 블록 수를 position에 기록한다. 일치한 prefix의 끝(0이면 anchor)에서 이어지는 DA-voted 경로의 body commitments를 길이 제한 안에서 extension에 담고, 모든 producer의 position과 extension을 묶은 complete vote에 서명한다. [Position / extension 구성](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/chain.rs#L1978).

| 주요 native 증거 | 묶는 자료 | 제공하는 근거 |
|---|---|---|
| DA certificate | 같은 producer header의 distinct valid DA shares `n−2f`개 | 해당 producer position의 availability / uniqueness와 certified anchor |
| V-QC | Distinct identities의 attributed votes / novotes `n−f..n`개, 그중 designated leader proposal에 대한 votes 최소 `2f+1`개 | 다음 leader가 이어갈 safe tips와 view exit |
| L-QC | 같은 leader proposal에 대한 complete votes `n−f`개 | Leader와 producer별 tips의 portable finality 증거 |

DA certificate는 threshold certificate이고 V-QC / L-QC는 complete attributed transcript의 ordinary signatures를 묶는다. Local sticky vote pool은 `n−f`에서 L-QC 생성과 독립적으로 finality에 도달한다. Producer별 prefix가 고정된 길이보다 cross-lane exact 실행 순서가 더 짧을 수 있으므로, sparse finality 뒤에 [§2.7의 ordered delivery](../e2e/canonical.md#cut-commit--ordered-range--실행-commit)를 연결한다. [DA / certificates](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/mod.rs#L147), [View / local finality](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md#L350), [Chain-local finality와 exact placement](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/mod.rs#L210).

이 native DA/view votes는 [Baton intended-order reports](../baton/direction.md#leader-report로-baton-생성), [direct execution 결과 서명](../e2e/results.md#결과-endpoint-direct-execution과-f1-인증)과 구분한다. Baton direction의 별도 승인 quorum은 추가하지 않는다. 실제 proposal을 인증할 때 selected prefix·policy를 actual parent/history/frontier에 결속하고 고정하는 연결은 개발·검증해야 한다. 선택 prefix의 membership뿐 아니라 정확한 leading order가 유지되어야 한다.

Orderer는 native owner가 선택한 exact witness와 original policy/history를 검증·보관하고 연속 입력을 계산한다. 이를 넘기는 resumable owner export는 신규 연결이다. Native sparse tip certificate는 body stream·past policy·dense cursor를 제공하지 않는다. Simplex marshal의 Multimmit 호환성도 별도 검토한다. [Native application boundary](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/docs/STATE_MACHINE.md).

| Existing attachment / query | 제공하는 자료 | 새 adapter가 보완할 책임 |
|---|---|---|
| Native `Reporter::report(Activity)` | Accepted artifact 등 activity 알림 | Durable witness handoff·cursor·retention 계약. Baton intended-order report와 별도 domain |
| `Running::inspect` / `Inspection::finality` | 현재 normalized finality projection | Same-tip evidence·settledness revision까지 필요한 원자료의 보존 |
| `Running::serve(view)` | Retained useful native ViewProof | Exact historical interpretation. Higher covering L-QC가 반환될 수 있고 old proof는 prune될 수 있음 |
| Proposed exact owner export | Selected source와 immutable context를 넘기는 신규 연결 | Original witness 검증·보관 → terminal slot 해석 → contiguous OrderedRange 방출 |

이 단계는 한 consensus application attachment의 논리적 책임으로 구현할 수 있다. Orderer를 별도 서버나 여러 actor로 나누는 결정은 하지 않았다. [Reporter trait](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/lib.rs#L246), [Inspection / serving](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/engine.rs#L530), [Retained proof selection](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/actors/resolver/actor.rs#L245).

`FinalityFact`는 leader/tips/positions/settledness와 evidence identity의 normalized projection이며 actual witness archive가 아니다.

Evidence hash는 witness의 식별 commitment이며 서명 검증 자료 자체가 아니다. Aggregate V-QC에서 재구성한 selected row에는 standalone raw vote artifact가 없을 수 있다. Orderer는 selected row와 함께 이를 인증하는 signed vote 또는 source certificate, extraction/opening을 재현할 자료를 보존해야 한다. Native가 선택한 identity별 exact body를 다른 conflicting body나 임의 quorum subset으로 바꾸지 않는다.

Tips가 같아도 source/evidence·settledness가 달라질 수 있어, 필요한 immutable export는 owner의 exact source-selection 전환에 연결해야 한다. [Evidence commitment](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/finality.rs#L2082), [Aggregate row provenance](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/finality.rs#L1681), [Pool revision](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/finality.rs#L1865).

Ordered delivery는 같은 epoch/committee와 actual parent·history·frozen policy, selected pool source, producer header/ancestry, native tips·positions·extensions·settledness를 함께 검증한다. 그 근거에서 included / irrevocably-empty / unresolved slots를 구분하고 첫 unresolved slot에서 방출을 멈춘다. Included body를 못 받았다는 사실은 empty의 증거가 아니다. Native extraction의 private `pub(crate)` API를 application이 이미 호출할 수 있다고 가정하지 않으며, 제한된 facade 또는 검증된 동등 연결은 개발 선택으로 남긴다. [Native extraction](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/machine/algebra/tips.rs#L336), [History opening](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/types/history.rs#L10).
