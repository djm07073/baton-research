# Proof-Aware State Finality for Autobahn-Family Consensus

> **ARCHIVED — 2026-09-29:** 현재 연구 기준은 [새 개요](overpass-plan-ordering-outline.md)다. 아래 proof/PAC 및 placement 관련 “현재/최신”은 당시 기록으로만 해석한다.

> **2026-09-28 문서 구분:** 아래는 2026-09-14 proof/PAC 설계 보관본이다. 현재 Overpass의 fixed certified cut + execution pipeline + producer placement 구현 방향은 [새 설계 기록](./overpass-fixed-cut-implementation-plan.md)을 따른다. 아래의 native extraction 유지·state-owner lanes·branch proofs를 새 Overpass에 적용하지 않는다. 본문은 이력 보존을 위해 그대로 둔다.

> 상태: active L-QC-selected conflict-scoped branch-proof model  
> 기준일: 2026-09-14  
> 범위: 논문에서 주장할 state-finality protocol model  
> SDK 설계: [commonware-proof-sdk.md](./commonware-proof-sdk.md)  
> 구현 주의: 현재 `commonware/`의 legacy glue PoC는 이 protocol을 구현하지 않는다. `commonware-proof-sdk.md`는 target interface 초안이다.


## 1. 문제와 목표

Autobahn은 BFT state machine replication protocol이지만, 핵심 설계 범위는 여러 data lane의 병렬 전파와 global ordering 합의다. Finalized cut 이후 deterministic application이 ordered log를 실행한다는 것은 전제하지만, application transition의 검증, 실행 결과의 가용성, durable state apply와 cross-lane execution semantics는 application state-machine abstraction 뒤에 둔다. 따라서 이는 Autobahn이 실행을 잘못 처리했다는 비판이 아니라, **ordering에 집중하기 위해 의도적으로 추상화한 경계**다.

Multimmit도 여러 producer chain의 membership와 global placement를 확정하며 state-partitioned application의 chain-local early execution 가능성을 언급한다. 그러나 early execution만으로 그 결과가 finalized cut과 일치하는지, 다른 validator가 검증·복구할 수 있는지, 한 state-owner lane의 finalized effect가 다른 lane의 canonical input으로 언제 안전하게 전달되는지는 결정되지 않는다.

또한 producer chain은 그 자체로 state ownership shard가 아니다. 서로 다른 producer lanes가 동일 account의 balance/nonce, AMM reserves 또는 shared collateral을 건드리는 transaction을 함께 포함할 수 있다. 각 lane이 동일한 pre-state에서 독립 실행하면 모두 유효해 보이더라도, canonical execution에서는 global order에 따라 일부만 성공할 수 있으므로 lane-local result를 그대로 독립 final state로 채택할 수 없다. Shared key는 execution을 serial path에 집중시키고, lane-local admission에서는 유효했던 transaction도 merged order에서는 stale state 때문에 retry, abort 또는 application rejection되어 wasted work와 cut-to-state latency를 늘릴 수 있다.

Production precedent로는 [Somnia MultiStream](https://docs.somnia.network/somnia-blockchain/multistream-consensus)을 사용한다. Somnia mainnet의 Autobahn-inspired independent data chains는 state shards가 아니며, consensus가 data-chain tips를 deterministic global byte stream으로 병합한 뒤 shared EVM state를 실행한다. 이는 multi-producer dissemination이 state-parallel execution을 자동으로 제공하지 않으며, shared state에는 global serialization 또는 별도의 state-ownership/cross-lane semantics가 필요함을 보여준다.

본 연구의 대상은 multi-producer lanes와 frontier-based global ordering을 사용하는 Autobahn-family consensus다. Formal protocol과 Commonware artifact는 concrete reference design으로 Multimmit의 producer-chain ordering, proposal-relative voting과 L-QC-derived frontier를 사용하며 이 ordering safety core를 다른 consensus algorithm으로 교체하지 않는다. 대신 **state를 consensus-visible 대상으로 만들고 ordering finality와 state apply의 간격을 줄이기 위해 state model과 consensus finalization model을 확장한다.** Validators는 cut finality 이전에 lane transition을 실행·증명하고 candidate execution에 바인딩된 proof-bundle availability evidence를 교환한다. 실제 finalized cut이 확정되면 각 node는 그 cut에서 결정적으로 도출한 canonical execution input과 exact evidence를 join하고, join 가능한 transition을 independently admit하여 durable state에 적용한다. 따라서 제안은 단순한 application-side 후처리가 아니라 기존 ordering consensus 위에 결합되는 proof-aware state-finalization protocol이다.

### 1.1 Common ordering abstraction: finalized cut

Autobahn의 committed cut-of-tips와 Multimmit의 L-QC에서 즉시 방출 가능한 ordered prefix를 논문에서는 별도 약어 없이 **finalized cut**으로 부른다. Multimmit에서는 chain-local membership-final tip과 global log에 즉시 배치된 prefix가 다를 수 있다. 한 lagging chain 때문에 horizontal sweep가 멈춘 뒤의 tip은 membership-final일 수 있어도 아직 global position이 정해지지 않았으므로 state layer의 canonical input으로 사용하지 않는다.

```text
FinalizedCut(F_k) = {
  authenticated_lane_boundaries,
  immediately_emitted_ordered_prefix
}
```

`F_k`는 ordering-finality evidence다.

- Autobahn: `F_k = CommitQC`, `FinalizedCut(F_k) = committed proposal의 cut-of-tips`
- Multimmit: `F_k = L-QC 또는 그에 상응하는 finality fact`, `FinalizedCut(F_k) = L-QC의 Tips*(F_k)까지 deterministic sweep가 즉시 방출한 ordered prefix`

두 protocol의 proposal과 vote 방식은 다르지만 state layer는 다음 공통 결과만 사용한다.

1. 모든 honest validator가 같은 `F_k`에서 같은 finalized cut을 계산한다.
2. Finalized cut은 각 lane의 authenticated boundary뿐 아니라 현재 global log에 배치된 정확한 ordered prefix를 지정한다.
3. 연속된 finalized cuts의 canonical positions는 monotonic하지만 Byzantine producer의 raw hash ancestry가 항상 연속일 필요는 없다.
4. State layer는 연속된 finalized cuts 사이의 canonical input을 deterministic하게 도출하며 proof/PAC는 그 exact input에만 join할 수 있다.

```text
CanonicalInput_i(F_{k-1},F_k)
  = DeterministicLinearize_i(FinalizedCut(F_{k-1}), FinalizedCut(F_k))
```

Rolling proof는 raw producer-parent continuity가 아니라 `CanonicalInput_i`의 digest와 canonical application-state parent에 연결된다. Finalized cut과 불일치하는 candidate proof는 valid할 수 있어도 canonical state에는 적용되지 않는다.

Candidate proof는 latest finalized cut에서 시작하는 candidate input에 대해 미리 만들 수 있다. **현재 cut이 candidate보다 낮다는 이유만으로 bundle을 폐기하지 않는다.** Candidate가 현재 canonical boundary를 그대로 연장한다면 `Pending`으로 유지하고, 이후 cut이 같은 branch를 포함할 때 exact snapshot을 재사용한다. Multimmit L-QC의 membership-final tip이 horizontal sweep 정지점 뒤에 있어 아직 global placement되지 않은 경우도 동일하다. 이후 finalized cut이 candidate와 양립할 수 없는 canonical input을 확정한 경우에만 bundle을 `Orphaned`로 표시한다. 그때는 exact canonical input을 다시 실행·증명하며, 이는 canonical rollback이 아니라 speculative computation의 폐기다.

이후 Autobahn과 Multimmit의 내부 차이가 중요하지 않은 곳에서는 공통 표현인 `finalized cut`을 사용한다.

두 finality는 다음처럼 서로 다른 사실을 의미한다.

```text
OrderingFinal(F_k):
  FinalizedCut(F_k)에서 도출한 CanonicalInput이 canonical하다.

StateAdmissible_v(i,h,F_k):
  node v가 finalized cut이 선택한 CanonicalInput의 exact ProofBundle을 확보하고,
  validity, bundle binding과 canonical state-parent continuity를 검증했다.

StateApplied_v(i,h,F_k):
  StateAdmissible_v가 성립하고 node v가 apply material을 durable state에 적용했다.
```

즉 cut finality는 "어떤 입력을 어떤 순서로 실행할지"를 확정하지만, 그 자체만으로 "그 실행 결과를 application의 최종 state로 채택할 수 있는지"까지 확정하지 않는다. Finalized cut이 확정된 이후에 proof 생성·전파·검증이나 cross-lane outcome 계산을 시작하면 그 시간이 그대로 사용자 관측 finality에 추가된다.

논문의 목표는 다음 간격을 최소화하는 것이다.

```text
Delta_cut_to_state,v = T_StateApplied,v - T_CutFinalized,v
```

정확한 related-work 표현은 “기존 연구가 state finality를 전혀 다루지 않았다”가 아니다. 논문은 **Autobahn-family finalized cut을 state-isolated application의 검증 가능한 local/cross-lane state finality로 변환하는 일반 규칙이 부족하다**는 빈틈을 다룬다.

제안의 핵심은 cut finality 이전에 lane execution, rolling proof와 `ProofBundle` availability 확보를 비동기적으로 진행해 두고, finalized cut에서 canonical execution input과 cross-lane outcome이 정해지면 exact evidence를 결합하는 것이다. Local transaction은 하나의 proof path를 따른다. Cross-lane transaction은 모든 관련 lane의 speculative overlay에 즉시 실행하되, 동일한 pre-state에서 `Commit`과 `Abort` continuation을 함께 증명한다. Finalized cut은 모든 lane에서 같은 branch를 결정적으로 선택하며 선택되지 않은 overlay는 canonical state에 적용하지 않는다.

분기는 lane 전체 suffix가 아니라 unresolved cross-lane transaction과 정적으로 충돌하는 read/write component에만 전파한다. 충돌하지 않는 transition은 공통 proof path에 한 번만 남긴다. 이를 실제로 구현하려면 monolithic linear fold만으로는 부족하며, branch-local state delta proof와 disjoint update를 다시 결합하는 proof-DAG 또는 componentized commitment가 필요하다. 단순 prototype은 두 linear folds를 만들 수 있지만 그 경우 non-conflicting suffix proof도 중복되고 novelty와 scalability가 약해진다.

```text
Autobahn-family consensus가 담당:
  data availability + finalized cut

본 연구가 추가:
  state-isolated execution model
  + validity and proof availability relative to the finalized cut
  + immediate speculative execution of cross-lane fragments
  + conflict-scoped Commit/Abort branch proofs
  + finalized-cut-selected atomic branch admission
```

구체적으로 consensus model에는 `ProofBundle` sidecar와 PAC의 subject·전파·custody 규칙, cross-lane operation/fragment binding, conflict closure, `Commit | Abort` branch bundle과 finalized-cut selector가 추가된다. 이 변경은 finalized cut을 도출하는 규칙을 바꾸거나 proof readiness 때문에 ordering progress를 멈추지 않는다. Proof가 늦으면 해당 state component의 apply만 늦어진다.

따라서 연구 질문은 다음과 같다.

> Autobahn-family consensus의 ordering progress를 지연시키지 않으면서, cut finality 이전의 병렬 실행·증명 작업을 이용해 ordering finality와 verifiable application state finality 사이의 간격을 얼마나 줄일 수 있는가?

## 2. State-Isolated Lanes

Application state를 여러 execution lane으로 분리한다.

```text
Lane i = {
  producer-chain boundary and canonical execution batch,
  application-defined state commitment,
  application transition circuit,
  rolling proof
}
```

- Lane 내부 transition은 순차적이다.
- 서로 독립적인 lane은 병렬로 진행한다.
- Application은 각 mutable state key에 deterministic한 단일 owner lane `owner(key)`를 부여한다.
- Formal reference model은 `producer lane i = state-owner execution lane i`로 제한한다. 이는 finalized cut이 선택한 producer input과 pre-cut execution batch의 canonical mapping을 고정한다.
- 지원 대상 transaction은 signed transaction bytes와 immutable application schema만으로 owner set과 conservative read/write footprint를 실행 전에 결정할 수 있어야 한다. 이 조건은 현재 mutable state를 읽거나 transaction을 먼저 실행하지 않고 검사할 수 있어야 한다.
- 모든 transaction은 sender가 서명한 conservative `AccessManifest(tx)`를 포함하며, application은 이를 이용해 cut finality 이전에 `placement(tx)`와 owner-local/cross-owner path를 결정한다. Manifest는 application의 정적 transaction schema와 일치해야 하고, 실제 read/write가 선언 범위를 벗어나면 transition proof가 성립하지 않는다.
- Runtime state, dynamically computed storage address, dynamic call target 또는 EVM control flow에 따라 owner/read/write set이 달라지는 arbitrary smart-contract transaction은 formal model의 범위 밖이다. EVM을 일반적으로 지원한다고 주장하지 않는다.
- 한 local lane proof는 그 lane이 소유한 key만 직접 변경할 수 있고, 두 lane이 같은 key에 canonical write를 만들 수 없다.
- 여러 owner lane을 건드리는 operation은 Section 5의 동일 operation digest에 bind된 lane-local fragments로 분해된다. 각 fragment는 자기 owner lane의 key만 변경하며 모든 관련 lane은 같은 finalized-cut selector로 `Commit` 또는 `Abort`를 선택한다.
- State 내부 구조와 owner mapping은 application이 정한다. Bank prototype은 `owner(address) = H(address) mod 6`을 사용한다.

```text
Footprint(application_id, circuit_version, signed_tx_bytes)
  -> (declared_reads, declared_writes, owner_lanes)

ActualReads(tx)  subset_of declared_reads
ActualWrites(tx) subset_of declared_writes
```

`Footprint`은 mutable pre-state를 입력으로 받지 않는다. 잔고 부족처럼 실행 성공 여부가 state에 따라 달라지는 것은 허용하지만, 그 분기가 새 owner나 선언되지 않은 key에 접근하게 만들 수는 없다.

별도의 global state frontier나 state QC를 추가하지 않는다. Proof가 늦어도 Autobahn-family ordering은 계속 진행하며, 각 node의 `StateAdmissible_v`와 `StateApplied_v` event만 늦어진다.

Trust boundary는 다음과 같다. Inherited ordering은 finalized-cut safety와 input availability를, application은 statically decidable transaction schema, owner mapping, conservative access manifest, lane-local fragment와 local prepare predicate를, proof system은 등록된 circuit relation에 대한 soundness를 담당한다. 본 protocol은 exact cut binding, `ProofBundle` custody, fragment completeness, conflict closure와 동일 branch selection을 담당한다. Proof soundness는 등록된 circuit이 외부 business intent를 충실히 표현한다는 사실까지 보장하지 않으므로 safety claim은 등록된 application contract와 circuit version에 상대적이다.

## 3. Application-Specific Rolling Proof

일반-purpose VM execution을 증명하지 않는다. 실행 전에 owner/read/write footprint를 결정할 수 있는 application의 개발자가 SDK로 state transition circuit을 정의한다.

```text
C_app(
  application_id,
  circuit_version,
  lane_id,
  execution_batch_digest,
  pre_state_commitment,
  post_state_commitment,
  effects_commitment,
  access_commitment,
  branch_context_commitment,
  conflict_component_commitment
) = 1
```

Lane prover는 block production과 병렬로 rolling recursive proof를 갱신한다.

```text
Q(i,h) = RecursiveProve(Q(i,h-1), C_app(E(i,h)))
```

Requirements:

- `E(i,h)`는 cut finality 이전 candidate execution batch이며 `Q(i,h)`는 exact batch digest와 canonical application-state parent에 바인딩된다.
- Finalized cut이 확정되면 `CanonicalInput_i`와 digest가 같은 candidate proof만 join할 수 있다.
- Finalized cut이 height `h`를 선택할 수 있으므로 lane은 height별 proof snapshot을 보관한다.
- Proof 생성은 이전 proof의 custody share 또는 cut finality를 기다리지 않는다.
- Rolling proof의 크기와 verification cost는 history 길이에 따라 선형 증가하지 않아야 한다.
- `NotYetSelected`와 `Incompatible`을 구분한다. 전자는 proof snapshot과 branch bundle을 retention window 동안 재사용하고, 후자만 orphan 처리한다.
- Expensive proving의 낭비를 제한하는 reference policy는 block을 즉시 speculative execute하되 DA certificate 또는 configurable support signal 뒤에 proof work를 시작하는 것이다. Raw-candidate proving은 더 낮은 latency와 더 높은 orphan cost를 갖는 실험 variant로 둔다.

## 4. ProofBundle Availability and Exact Cut Matching

Lane proof `Q(i,h)`가 준비되면 proof와 deterministic apply material을 하나의 content-addressed `ProofBundle`로 만든다. Local-only batch는 하나의 continuation을 담는다. Unresolved cross-lane operation과 충돌하는 component는 동일 prefix에서 갈라진 `Commit`/`Abort` continuations와 두 apply deltas를 함께 담는다. Cut finality를 기다리지 않고 sidecar로 전파하며 다음 producer block의 transaction으로 다시 ordering하지 않는다. 이 pre-finality path가 proof-bundle dissemination과 custody round를 ordering latency 뒤에 숨긴다.

```text
ProofBundle(i,h) = {
  execution_batch_digest,
  canonical_parent_state,
  post_state_commitment,
  effects_commitment,
  access_commitment,
  branch_context_commitment,
  conflict_component_commitment,
  apply_material,
  rolling_proof
}
```

Cross-lane component의 bundle은 다음 public data를 추가한다.

```text
BranchBundle(X,i) = {
  common_prefix_proof,
  operation_digest,
  participant_lanes,
  decision_cut_index,
  declared_access_manifest,
  conflict_closure_commitment,
  local_prepared_bit,
  commit_state_delta_if_prepared,
  abort_state_delta,
  commit_proof_if_prepared,
  abort_proof
}
```

`local_prepared_bit`는 fragment가 lane-local application precondition을 만족했는지를 proof가 인증한 값이다. `true`이면 commit과 abort continuations를 모두 증명한다. `false`이면 global selector가 commit을 선택할 수 없으므로 certified rejection과 abort continuation만 필요하다. `Abort` path는 이전 state를 되돌리는 역연산이 아니라, 같은 common prefix에서 fragment를 deterministic no-op으로 처리한 별도 forward transition이다. Branch bundle에서 `post_state_commitment`는 한 root가 아니라 canonical-order의 possible outcome roots에 대한 commitment로 해석한다.

기존 Multimmit DA certificate는 ordered input block availability를 담당한다. Execution 이후에 생성되는 proof와 apply material은 기존 DA certificate의 소급 보장 대상이 아니며 `ProofBundle` custody가 담당한다.

Validator는 proof를 검증하고 durable하게 보관한 뒤 다음 subject에 custody share를 서명한다.

```text
ProofSubject = H(
  epoch,
  lane_id,
  height,
  execution_batch_digest,
  pre_state_commitment,
  post_state_commitment,
  effects_commitment,
  access_commitment,
  branch_context_commitment,
  conflict_component_commitment,
  circuit_version,
  proof_bundle_digest
)
```

`f+1` distinct custody shares가 모이면 Proof Availability Certificate(PAC)가 된다.

- Proof soundness가 execution correctness를 보장한다.
- PAC는 correctness 투표가 아니라 exact `ProofBundle` custody와 recovery 가능성을 보장한다.
- `f+1`은 최대 `f` Byzantine nodes 아래 적어도 한 honest custodian을 포함한다.
- 추가 `c`개 custodian crash까지 견디려면 optional replication target을 `q >= f+c+1`로 높일 수 있지만 canonical state admission 조건은 최소 `f+1` PAC로 유지한다.
- PAC는 cut finality 이전에 local bundle 또는 commit/abort 양쪽을 포함한 branch bundle에 형성될 수 있으며 canonicality를 만들지 않는다.
- Finalized cut에서 도출한 exact `CanonicalInput_i`와 digest가 같은 proof/PAC만 state admission에 사용할 수 있다.
- Custody votes는 개별 signed objects로 gossip되어 단일 aggregator가 PAC를 숨겨도 다른 node가 같은 signer set에서 PAC를 재구성할 수 있다.
- Honest custodian은 branch가 후속 finalized cut에서 영구 배제되거나, selected state가 recoverable proof-bearing checkpoint에 포함되고 grace window가 끝날 때까지 bundle을 보관한다.
- Eventual retrieval liveness는 retention interval, eventual synchrony, fair service와 bounded proof-request load 아래 honest custodian이 digest-addressed request에 응답한다는 조건에 의존한다.
- Takeover proving은 ordered input뿐 아니라 application witness/state, registered circuit와 parent proof 또는 proof-bearing checkpoint가 복구 가능한 경우에만 보장한다.

### 4.1 L-QC-integrated proof readiness

Standalone custody-share gossip만으로도 PAC를 만들 수 있지만, Multimmit의 L-QC를 state-finality pipeline에 더 직접적으로 재사용한다. Multimmit vote는 원래 leader proposal에 대한 모든 producer chain의 position과 extension을 서명하고, L-QC는 정확히 `n-f`개 vote의 attributed transcript와 aggregate signature를 보존한다. 이 signed vote body에 다음 **optional, bounded** claim을 추가한다.

```text
ProofReadyClaim = {
  proof_subject,
  proof_bundle_digest
}
```

- Validator는 exact bundle을 검증하고 durable하게 저장한 경우에만 claim을 싣는다.
- Claim을 만들기 위해 vote 전송을 기다리지 않는다. Vote 시점에 준비되지 않은 proof는 생략하며 L-QC validity, final-tip extraction과 ordering progress에는 영향을 주지 않는다.
- 기본 encoding은 lane마다 voted path 위의 **가장 높은 exact proof-ready bundle 하나**만 claim하고 전체 개수를 chain count로 제한한다. Claim은 height만이 아니라 exact `ProofSubject`와 bundle digest에 바인딩된다. L-QC가 더 낮은 position을 선택하면 해당 claim을 잘라 쓰지 않고 standalone PAC/slow path로 간다.
- 실제로 확정된 L-QC transcript 안에 같은 claim의 distinct signer가 `f+1`명 이상이면 그 L-QC에서 embedded PAC를 추출할 수 있다. Applying node는 L-QC가 인증한 signer를 custodian으로 즉시 식별하고 bundle을 요청할 수 있다.
- `f+1`은 **그 L-QC 안에 실제로 포함된 claim**에 대해 최소 한 honest custodian을 보장한다. 네트워크 전체에 claim이 `f+1`개 생겼다는 사실만으로 모든 가능한 L-QC가 이를 포함하는 것은 아니다. Malicious assembler가 최대 `f` votes를 제외해도 embedded PAC가 항상 남게 하려면 동일 claim이 최소 `2f+1` votes에 실려야 한다.
- Embedded PAC가 없는 L-QC도 완전히 유효하다. 이 경우 standalone PAC gossip 또는 post-cut recovery/proving slow path를 사용한다.
- 서로 다른 valid L-QC가 서로 다른 readiness evidence를 담더라도 canonical state는 달라지지 않는다. L-QC가 정한 ordered prefix와 exact proof verification이 canonicality/correctness를 정하고, readiness claim은 오직 custody discovery를 앞당긴다.

```text
EmbeddedPAC(F_k, subject) =
  { signer | signer is in L-QC(F_k)
             AND signer.vote carries ProofReadyClaim(subject) }

ValidEmbeddedPAC(F_k, subject) iff
  |EmbeddedPAC(F_k, subject)| >= f+1
  AND subject's exact block is in FinalizedCut(F_k)
```

이 결합은 proof를 consensus safety predicate로 승격하지 않으면서, common case의 별도 PAC aggregation/discovery 지연을 기존 ordering vote와 겹친다. 비용은 vote/L-QC bytes, claim 검증과 worst-case deviation encoding 증가이며 Section 7에서 standalone PAC와 비교 측정한다.

Node-local state admission과 apply는 다음처럼 구분한다.

```text
StateAdmissible_v(i,h,F_k) iff
  ExactCanonicalInputSelected(i,h,FinalizedCut(F_k))
  AND v retrieved a digest-matching ProofBundle from a valid PAC
  AND ValidRollingProof(Q(i,h))
  AND BundleCommitmentsMatch(i,h)
  AND ContinuousFromCanonicalStateParent_v(i,h)

StateApplied_v(i,h,F_k) iff
  StateAdmissible_v(i,h,F_k)
  AND AppliedDurably_v(i,h)
```

별도의 state leader, global state frontier 또는 state QC는 없다. 각 validator는 같은 finalized cut과 `ProofBundle`/PAC를 deterministic join하고 도착 시점에 비동기적으로 state를 적용한다. Proof/PAC가 cut finality 전에 준비된 fast path에서는 추가 post-finality vote round가 없다.

## 5. Conflict-Scoped Cross-Lane Branch Proofs

### 5.1 Cross-lane operation and fragments

각 mutable key는 하나의 state-owner lane만 갱신한다. 하나의 cross-lane operation `X`는 statically known participant lanes와 각 owner가 실행할 fragment를 가진다. 모든 fragment는 동일한 sender-signed operation digest에 bind된다.

```text
CrossOperation X = {
  operation_id,
  application_id,
  application_version,
  participant_lanes,
  fragment_digest_by_lane,
  declared_access_manifest,
  decision_cut_index,
  sender_nonce,
  payload_digest
}

operation_id = H(application/version, participants, fragment digests,
                 access manifest, decision cut, sender nonce, payload digest)
```

Application은 `X`의 signed bytes와 immutable schema만으로 participant set, lane-local fragments와 conservative read/write footprint를 결정할 수 있어야 한다. Runtime-dependent EVM call graph처럼 실행 후에야 participant 또는 key가 드러나는 transaction은 대상이 아니다. Fragment는 자기 lane이 소유한 key만 읽고 쓸 수 있으며 다른 operation의 fragment로 재사용할 수 없다.

### 5.2 Immediate speculative apply

각 participant lane은 자기 fragment를 candidate block에 담는 즉시 local speculative overlay에 실행한다. 여기서 “즉시 apply”는 후속 block construction과 speculative read가 사용할 수 있다는 뜻이지 canonical durable state가 되었다는 뜻은 아니다.

```text
CanonicalState_i
  -> CommonPrefix_i
      -> CommitOverlay_i(X): Execute(fragment_i)
      -> AbortOverlay_i(X):  DeterministicNoOp(fragment_i)
```

Canonical state에 먼저 반영하면 `Abort`에서 후속 dependent transaction까지 되돌려야 한다. 따라서 RPC 또는 application은 speculative/latest read와 proof-final read를 구분해야 한다. Finalized cut 전에는 어느 overlay도 irreversible external effect의 근거가 될 수 없다.

### 5.3 Cut-relative branch selection

Operation은 local wall-clock이 아니라 monotonically finalized되는 cut index `decision_cut_index`를 가진다. 그 cut 전에는 fragment가 일부만 보이더라도 `Pending`이며 두 overlays를 보관한다. Decision cut에서 모든 honest nodes는 finalized cut이 즉시 방출한 exact ordered prefix와 verified branch bundles로 같은 selector를 계산한다.

```text
Complete(X,F_k) iff
  for every lane i in X.participant_lanes:
    exactly one fragment with X.operation_id and fragment_digest_by_lane[i]
    appears in FinalizedCut(F_k).ordered_prefix by X.decision_cut_index

Prepared(X) iff
  every participant's verified BranchBundle has local_prepared_bit = true

Select(X,F_k) =
  Commit  if Complete(X,F_k) AND Prepared(X)
  Abort   otherwise, when k >= X.decision_cut_index
  Pending otherwise
```

`Complete`는 membership-final tip이 아니라 finalized cut이 실제 global order로 방출한 prefix만 본다. 서로 다른 digest의 duplicate fragment, undeclared lane access, invalid local precondition 또는 deadline까지 누락된 fragment는 모두 `Abort`를 만든다. Proof가 아직 도착하지 않은 경우에는 `Prepared`를 false로 추측하지 않고 해당 component의 state apply를 기다리거나 PAC custodian에게 bundle을 요청한다. Ordering은 계속 진행한다.

Decision이 한번 정해지면 `(operation_id, decision_cut_index, Commit|Abort)`를 cut-derived terminal decision으로 기록한다. Abort 뒤 늦게 ordered prefix에 들어온 fragment나 이미 committed operation의 duplicate fragment는 이후 lane proof에서 deterministic no-op이어야 한다. 그렇지 않으면 withheld fragment가 later cut에서 단독 effect를 만드는 replay가 가능하다.

모든 participant lane은 동일 `Select(X,F_k)`를 사용한다.

```text
Select = Commit -> every lane applies its commit delta
Select = Abort  -> every lane applies its abort delta
```

따라서 한 lane만 commit하고 다른 lane은 abort하는 상태는 허용되지 않는다. 이것은 새로운 ordering consensus나 participant handshake가 아니라 finalized cut과 validity proofs 위의 deterministic state-admission rule이다.

### 5.4 Branch proof generation and folding

Local transaction은 기존 rolling proof에 한 번 fold한다. Locally prepared인 cross-lane transaction 경계에서는 common-prefix accumulator를 복제하고 서로 다른 transition을 fold한다. Local precondition이 이미 false이면 rejection bit와 abort path만 증명한다.

```text
P_A = Fold(P_parent, Execute(A))

P_commit = Fold(P_A, Execute(B_fragment))
P_abort  = Fold(P_A, AbortNoOp(B_fragment))

if C conflicts with B:
  P_commit = Fold(P_commit, Execute(C on commit state))
  P_abort  = Fold(P_abort,  Execute(C on abort state))
else:
  prove C once as a disjoint component update and join it to either selected path
```

SuperNova-style non-uniform IVC는 `Execute`와 `AbortNoOp`처럼 서로 다른 step circuits를 한 incremental computation에 넣는 구현 재료가 될 수 있다. 그러나 folding scheme 자체가 두 branches를 공짜로 증명하거나 자동으로 다시 합쳐주지는 않는다. Naive linear IVC는 global pre-state root가 달라진 순간 이후 suffix proof를 양쪽에서 모두 만들어야 한다.

본 연구의 conflict-scoped optimization은 branch의 영향을 state-delta component에 제한한다. Branch bundle은 declared key set, read versions, commit/abort deltas와 disjointness witness를 포함하고, cut 이후 join circuit이 선택된 branch delta와 공통 deltas가 겹치지 않음을 확인해 lane state commitment를 구성한다. 이 proof-DAG/join이 구현되지 않은 prototype은 “full dual-fold baseline”으로만 부르고 conflict-scoped proof reuse를 달성했다고 주장하지 않는다.

### 5.5 Conflict closure

두 transactions `x`, `y`의 static footprint를 `R(x), W(x)`라고 할 때 다음이면 충돌한다.

```text
Conflict(x,y) iff
  W(x) intersects (R(y) union W(y))
  OR W(y) intersects (R(x) union W(x))
```

Unresolved cross-lane operation을 정점으로 하고 이 conflict relation을 edge로 하는 graph를 만든다. 같은 connected component에 속한 후속 transactions만 branch-dependent execution/proof에 들어간다. 다른 component의 transactions는 한 번 실행하고 공통 delta proof로 재사용한다.

`AccessManifest`가 실제 access를 누락하면 conflict closure가 깨질 수 있으므로 application proof는 `ActualReads subset_of R`과 `ActualWrites subset_of W`를 강제한다. Conservative over-declaration은 안전하지만 component를 불필요하게 크게 만들어 성능을 낮춘다.

### 5.6 Example: `A -> B -> C` versus `A -> C`

Lane `L1`에서 `A`가 Alice balance를 바꾸고, cross-lane transfer `B`가 Alice에서 debit하며, `C`가 다시 Alice balance를 읽는다고 하자. Lane `L2`에는 `B`의 Bob credit fragment가 있다.

```text
L1 common prefix: A
  Commit(B): A -> debit B -> execute C using post-B balance
  Abort(B):  A -> skip B  -> execute C using post-A balance

L2 common prefix:
  Commit(B): credit B
  Abort(B):  skip B
```

- Decision cut에 L1/L2 fragments가 모두 포함되고 두 local prepared proofs가 valid하면 두 lanes 모두 `Commit`을 선택한다.
- L2 fragment가 deadline까지 cut에 없거나 어느 local precondition이 false이면 두 lanes 모두 `Abort`를 선택한다. L1은 이미 canonical debit을 되돌리는 것이 아니라 처음부터 준비해 둔 `A -> C` branch를 적용한다.
- `C`가 Alice와 무관한 key만 건드리면 `C`의 component proof는 한 번만 만들 수 있다. `C`가 Alice를 읽거나 쓰면 두 branches에서 결과가 달라질 수 있으므로 두 번 실행·증명해야 한다.

### 5.7 N-lane operation

두 lane 예시는 그대로 `N` lanes에 일반화된다. 각 lane은 자기 fragment의 `local_prepared_bit`와 commit/abort delta를 증명하며, global selector는 모든 required fragments와 local prepared bits의 conjunction이다. Cross-account liquidation이라면 account, BTC market, ETH market fragments가 같은 operation에 들어가고 세 lanes 모두 commit하거나 모두 abort한다.

이 방식은 receipt DAG보다 same-cut success path가 짧고 arbitrary statically declared N-lane all-or-none state transition을 표현할 수 있다. 대신 unresolved operations가 서로 겹치면 state/proof branches가 늘어나는 비용을 명시적으로 지불한다.

### 5.8 Bounds, attacks and fallback

`m`개의 unresolved cross-lane operations가 한 conflict component에 겹치면 최악에는 `2^m` branch combinations가 필요하다. 이는 설계의 핵심 한계다. Protocol은 다음 deterministic bounds를 둔다.

- `max_unresolved_per_component`: 한 conflict component가 동시에 유지할 operation 수.
- `max_decision_horizon`: transaction admission부터 decision cut까지의 finalized-cut 수.
- `max_branch_bytes`와 `max_branch_proof_work`: overlay와 proving budget.
- Bound를 넘은 component는 새 conflicting cross-lane transaction의 speculative continuation을 멈추고 finalized cut 이후 순차 실행한다. 다른 components와 unrelated lanes는 계속 진행한다.

주요 공격과 대응은 다음과 같다.

- **Branch-explosion griefing:** hot keys에 overlapping operations를 보내는 공격은 component bounds와 admission pricing으로 격리한다.
- **Fragment withholding:** sender/producer가 일부 fragment만 넣으면 decision cut에서 operation만 abort한다. 전체 cut을 revert하지 않는다.
- **Replay/equivocation:** operation id가 participants, every fragment digest, manifest, nonce와 decision cut에 bind된다.
- **False manifest:** proof circuit이 actual access containment를 검증한다.
- **Selected proof withholding:** `f+1` PAC custodian에게 digest로 병렬 요청한다. Availability가 state apply만 늦추며 ordering은 막지 않는다.
- **Prover stall:** `D_failover` finalized cuts 동안 proof/PAC progress가 없으면 동일 logical lane의 deterministic backup prover를 활성화한다. Wall-clock timeout을 사용하지 않는다.
- **Speculative side effects:** external I/O, withdrawal 또는 irreversible action은 selected branch가 state-final되기 전에 실행하지 않는다.

### 5.9 Related design points

- [X-Shard](https://doi.org/10.1109/TPDS.2024.3361180)는 cross-shard sub-transactions를 optimistic하게 input shards에서 병렬 처리하고 threshold-signature commit protocol을 사용한다. 그러나 conflict 발생 시 touched state change를 withdraw하며, 동일 prefix에서 두 proof continuations를 유지해 later cut으로 선택하지 않는다.
- [Prophet](https://arxiv.org/abs/2304.08595)은 cross-shard transactions를 pre-execute해 read/write 정보와 messages를 얻은 뒤 Byzantine-tolerant global order로 conflict와 abort를 피한다. 이는 branch를 유지하기보다 ordering 전에 conflict를 제거하는 반대 선택이다.
- [Block-STM](https://arxiv.org/abs/2203.06871)은 preset block order 아래 충돌한 incarnation과 dependent transactions를 validation/re-execution한다. Conflict-directed speculation의 직접적인 참고점이지만 cross-lane atomic selector, validity proof custody와 pre-cut dual continuations는 없다.
- [Proof-of-Execution](https://arxiv.org/abs/1911.00838)은 consensus 전 speculative execution과 quorum responses를 사용하며 충분한 proof-of-execution이 없으면 rollback할 수 있다. 여기의 proof는 application validity SNARK가 아니고 state-isolated cross-lane branch도 아니다.
- [RollShard](https://doi.org/10.1109/TC.2026.3673996)는 stateless off-chain execution, hierarchical state-delta tree와 ZK proof로 batched multi-shard deltas 및 value conservation을 증명한다. Proof-based atomic multi-shard execution의 가장 가까운 비교점이지만 Autobahn-family cut이 commit/abort continuations 중 하나를 선택하는 구조는 아니다.
- [SuperNova](https://eprint.iacr.org/2022/1758)는 서로 다른 step relations를 지원하는 non-uniform IVC로 branch circuit의 cryptographic building block이 될 수 있다. Cross-lane protocol이나 conflict-scoped proof merge를 제공하지는 않는다.

따라서 선행성 주장은 “optimistic execution, conflict tracking 또는 ZK atomicity가 처음”이 아니다. 현재 확인한 literature에서 직접 보이지 않는 조합은 **Autobahn-family finalized cut을 selector로 사용하고, cut 전에 양쪽 outcomes를 증명하며, static conflict closure에만 branch cost를 제한하는 proof-carrying state admission**이다. 체계적 literature review 전에는 절대적 최초라고 표현하지 않는다.

## 6. 논문 기여와 검증 항목

권장 contribution은 세 가지다.

1. **L-QC-Integrated Cut-to-State Finalization.** Finalized cut 전에 준비된 candidate execution `ProofBundle`을 exact ordered prefix와 결합하고, optional custody claims로 proof recovery를 ordering vote와 겹친다.
2. **Cut-Selected Conflict-Scoped Branch Proofs.** Statically declared N-lane operation을 모든 participant overlays에서 즉시 실행하고 commit/abort state deltas를 미리 증명하며, finalized cut이 모든 lanes에서 같은 branch를 선택한다. Static conflict closure와 proof-DAG join은 branch duplication을 affected state component로 제한한다.
3. **Formal and Experimental Characterization.** Cut-to-state latency 이득과 branch proof amplification의 trade-off를 proof lag, cross-lane ratio, conflict density, decision horizon과 Byzantine failure 아래 측정한다.

State isolation, recursive proof, speculative execution, OCC와 `f+1` proof custody 각각은 단독 novelty가 아니다. Novelty claim은 **pre-final multi-lane execution의 양쪽 결과를 proof-carrying branches로 준비하고, Autobahn-family finalized cut으로 원자적으로 선택하며, proof duplication을 static conflict component에 제한하는 end-to-end state-finalization model**에 둔다. Multimmit은 attributed L-QC transcript를 PAC discovery에 재사용하는 concrete artifact다.

필수 formal properties:

- Finalized-cut selector consistency
- Fragment completeness and operation-digest binding
- Cross-lane all-or-none branch selection
- Selected-branch validity and canonical-parent continuity
- Conflict-closure soundness
- No canonical effect from an unselected overlay
- Proof readiness와 무관한 ordering progress
- Bounded-component fallback liveness
- Exact bundles를 받은 honest nodes의 lane-state convergence

명시적인 non-guarantees:

- Runtime-dependent EVM footprint
- Unbounded optimistic branching
- Pre-final speculative reads와 irreversible external effects의 finality
- Proof throughput이 input rate보다 낮을 때 bounded state-finality latency
- Registered application/circuit semantics 밖의 business correctness

Primary evaluation metrics:

```text
Delta_local        = T_local_state_applied - T_cut_finalized
Delta_cross        = max_i(T_selected_branch_applied_i) - T_cut_finalized
ProofAmplification = branch_proving_work / single_path_proving_work
```

필수 비교:

- Cut finality 이후 canonical execution/proving baseline
- Pre-execute/pre-prove local-only baseline
- Full dual-fold cross-lane baseline
- Proposed conflict-scoped branch proof + pre-cut PAC + exact cut selection
- X-Shard-style optimistic abort/repair reference와 synchronous lock/2PC reference
- RollShard-style proof-based multi-shard baseline은 가능한 범위에서 분석 또는 축소 구현
- Standalone PAC 대 L-QC-integrated readiness claims
- Cross-lane ratio, conflict density, hot-key skew, unresolved component width와 decision horizon
- Commit/abort latency, proof-ready-at-cut ratio, fallback rate, overlay memory, proof bytes와 wasted proving CPU
- Missing/late/invalid proof, fragment omission/equivocation, false manifest와 branch-explosion load
- Invalid state installation과 mixed commit/abort outcome은 항상 0
