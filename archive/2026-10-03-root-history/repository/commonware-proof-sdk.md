# Proof-Aware Multimmit: Minimal Commonware SDK

> **ARCHIVED — 2026-09-29:** [새 연구 개요](overpass-plan-ordering-outline.md)가 현재 방향이다. 아래 fixed-cut·placement 및 proof/PAC 계획은 모두 이전 기록이며 새 구현 지침이 아니다.

> **2026-09-28 문서 구분:** 아래 proof/PAC SDK는 보관 설계이며 새 Overpass 구현 계획이 아니다. [Fixed-cut module 구현 계획](./overpass-fixed-cut-implementation-plan.md)이 최신이다. 기존 Voter/Actor와 admission을 재사용하고 execution·placement·result/state modules를 붙이며 proof/PAC SDK를 복원하지 않는다. 아래 본문과 fork 코드는 이번 기록에서 수정하지 않았다.

> 상태: target L-QC-integrated proof/PAC and conflict-scoped branch-proof SDK design  
> 기준일: 2026-09-14  
> 논문 protocol: [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)  
> 구현 주의: 현재 `commonware/` 코드는 아직 이 SDK를 구현하지 않는다. Legacy EC reducer는 active path가 아니다.

## 1. 설계 원칙

- Multimmit ordering quorum, final-tip extraction과 progress rule은 변경하지 않는다. Wire format 변경은 optional bounded proof-readiness claim으로 제한한다.
- `producer lane = state-owner lane`인 reference model을 먼저 구현한다.
- Cross-lane fragment는 각 participant lane의 speculative overlay에 즉시 실행하지만 finalized cut 전에는 canonical state에 적용하지 않는다.
- Application logic, access schema, circuit와 proof backend를 consensus crate에 넣지 않는다.
- Proof bytes는 opaque하게 다루고 transport, custody, exact-cut join과 deterministic branch selection은 framework가 담당한다.
- Proof readiness는 ordering vote나 다음 block production의 선행조건이 아니다.
- Runtime-dependent EVM access discovery는 지원하지 않는다. Signed bytes와 immutable schema로 conservative read/write set과 participant lanes를 결정할 수 있어야 한다.

## 2. 공개 Application Trait 하나

Application 개발자는 다음 세 method만 구현한다.

```rust
pub trait Application<D: Digest>: Clone + Send + 'static {
    type Error: std::error::Error + Send + Sync + 'static;

    /// Executes an exact producer block on speculative state. Local work
    /// extends one path; cross-lane conflict components return all bounded
    /// Commit/Abort variants and their proofs.
    fn prove(
        &mut self,
        context: ExecutionContext<D>,
    ) -> impl Future<Output = Result<ProofBundle<D>, Self::Error>> + Send;

    /// Verifies the opaque linear proof and every branch variant, including
    /// access containment, common-parent and conflict-closure bindings.
    fn verify(
        &self,
        bundle: &ProofBundle<D>,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;

    /// Durably applies only the variants selected by the finalized cut.
    fn apply(
        &mut self,
        cut: StateCut<D>,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send;
}
```

Protocol-facing data는 다음처럼 최소화한다.

```rust
pub struct ProofBundle<D: Digest> {
    pub block: BlockRef<D>,
    pub execution_batch: D,
    pub parent_state: D,
    pub linear_state: D,
    pub access_commitment: D,
    pub linear_apply_material: Bytes,
    pub linear_proof: Bytes,
    pub branch_components: Vec<BranchComponent<D>>,
    pub circuit: D,
}

pub struct CrossOperation<D: Digest> {
    pub id: D,
    pub application: D,
    pub application_version: u64,
    pub participant_lanes: Vec<u64>,
    pub fragment_digests: Vec<(u64, D)>,
    pub access_manifest: D,
    pub decision_cut_index: u64,
    pub sender_nonce: u64,
    pub payload_digest: D,
}

pub struct BranchComponent<D: Digest> {
    pub component: D,
    pub common_parent_state: D,
    pub conflict_closure: D,
    pub operations: Vec<CrossOperation<D>>,
    pub local_prepared: Vec<(D, bool)>,
    pub variants: Vec<BranchVariant<D>>,
}

pub struct BranchVariant<D: Digest> {
    /// Canonical ordered pairs of operation id and Commit/Abort bit.
    pub decisions: Vec<(D, BranchDecision)>,
    pub state_delta: D,
    pub post_component_state: D,
    pub effects: D,
    pub apply_material: Bytes,
    pub proof: Bytes,
}

pub enum BranchDecision {
    Commit,
    Abort,
}

/// Protocol-neutral view of Autobahn's committed cut-of-tips or
/// Multimmit's L-QC-derived immediately emitted ordered prefix.
pub struct FinalizedCut<D: Digest> {
    pub index: u64,
    pub finality_fact: D,
    pub lane_boundaries: Vec<BlockRef<D>>,
    pub ordered_prefix: Vec<BlockRef<D>>,
}
```

- `prove`는 native execution, witness generation, common-prefix folding과 branch proof backend를 자유롭게 구현한다.
- `verify`는 proof validity뿐 아니라 actual access가 manifest 범위 안인지, 모든 variants가 같은 parent/component에서 시작하는지, variant table이 locally possible한 decision combinations를 빠짐없이 포함하는지를 검증한다. `local_prepared=false`가 proof-certified이면 그 operation의 Commit variant는 요구하지 않는다.
- `apply`는 framework가 선택한 variant 외의 bytes를 볼 필요가 없다.
- 한 unresolved operation만 든 component는 `Commit`과 `Abort` 두 variants를 가진다. 겹친 `m`개 operations는 최악에 `2^m` variants가 필요하므로 framework limits를 넘으면 해당 component가 cut 이후 순차 실행 mode로 전환된다.

## 3. Framework가 고정하는 것

Commonware glue가 담당한다.

- `FinalityFact -> FinalizedCut` 변환과 immediately emitted ordered-prefix binding.
- Signed `AccessManifest` canonical encoding/signature, deterministic owner placement와 operation/fragment digest 검증.
- Static footprint에서 conflict graph와 connected components 계산.
- Height별 `ProofBundle`/branch snapshots와 candidate execution-batch binding.
- Current cut 아래의 branch-compatible snapshots는 `Pending`으로 유지하고 incompatible canonical input만 `Orphaned`로 전환.
- Proof 준비 즉시 `ProofSidecar` broadcast, missing bundle `Resolver` fetch와 durable storage.
- Proof 검증 성공 후 custody share 서명 및 `f+1` PAC 집계.
- Vote 시점에 이미 준비된 lane별 highest exact `ProofReadyClaim`만 optional bounded field에 추가. Vote는 claim을 기다리지 않는다.
- 실제 L-QC transcript의 같은 claim `f+1`개에서 embedded PAC를 추출하고, 없으면 standalone PAC를 사용.
- Operation별 fragment completeness와 decision-cut deadline 계산.
- 모든 participant의 proof-authenticated `local_prepared` bits를 모아 동일 `Commit | Abort` selector 계산.
- Cut-derived terminal operation decision 저장과 late/duplicate fragment의 deterministic no-op enforcement.
- Selected branch delta와 disjoint common deltas의 join 검증.
- `StateAdmissible`인 `StateCut`만 `Application::apply`에 전달하고 node-local `StateApplied` event 기록.
- `max_unresolved_per_component`, `max_decision_horizon`, `max_branch_bytes`, `max_branch_proof_work` enforcement.
- Bound 초과 component만 cut 이후 순차 실행으로 전환하고 unrelated components는 계속 실행.
- Finalized-cut count 기반 prover failover와 bounded pending proof store/restart recovery.

Application 개발자는 proof transport, PAC aggregation 또는 branch selector를 다시 구현하지 않는다. Customization은 access schema, lane-local transition, local prepared predicate와 opaque proof backend에 한정한다.

## 4. 최소 runtime flow

```text
on_da_certified_block(block)
  -> signed access manifests and cross-operation bindings 검사
  -> static conflict components 계산
  -> background application.prove(context)
  -> ProofBundle/branch snapshots 저장
  -> ProofSidecar 즉시 broadcast

on_proof_sidecar(sidecar)
  -> exact lane/block/batch/parent/component binding 검사
  -> application.verify(bundle)
  -> durable ProofBundle store
  -> custody share 서명/전파

on_build_multimmit_vote(vote)
  -> 이미 검증·저장된 bounded ProofReadyClaim만 non-blocking 첨부

on_ordering_finality(cut)
  -> L-QC의 immediately emitted ordered prefix 계산
  -> embedded 또는 standalone PAC에서 exact bundles pull
  -> each due operation:
       complete = all required fragments are in the emitted prefix
       prepared = all participant local_prepared proofs are true
       decision = Commit if complete && prepared else Abort
       persist terminal decision; later fragments become no-op
  -> every lane/component에서 동일 decision variant 선택
  -> selected branch delta와 common deltas join 검증
  -> application.apply(state_cut)
  -> node-local StateApplied event 기록
```

Proof/PAC가 늦으면 due component의 state apply만 기다린다. Multimmit ordering, 다음 producer blocks와 disjoint components의 proving은 계속 진행한다.

## 5. 재사용과 만들지 않는 것

재사용:

- `commonware_broadcast::Broadcaster`
- `commonware_resolver::Resolver`
- `commonware_cryptography::certificate`
- Commonware runtime의 CPU-task spawning과 deterministic tests
- 현재 `glue::multimmit`의 `ExecutionContext`와 finality callback

별도로 만들지 않는 것:

- Public `RollingProofBackend`, `CircuitCostModel`, `CrossLaneApplication` trait
- Custom proof network trait
- 별도 state consensus/QC 또는 repair lane
- Receipt/ack/compensation subsystem
- Canonical rollback manager
- 새 SDK crate 또는 외부 actor/runtime dependency

Branch-proof 구현이 두 개 이상 생겨 실제 분리 필요성이 확인될 때만 backend trait를 추출한다.

## 6. 최소 구현 순서

1. `Application::execute/apply`를 `prove/verify/apply`로 바꾸고 local-only `MockProver`를 연결한다.
2. `ProofBundle`, sidecar, custody share와 standalone `f+1` PAC를 추가한다.
3. L-QC optional `ProofReadyClaim`과 exact ordered-prefix join을 연결한다.
4. Bank transfer에 signed access manifest, operation id와 lane-local debit/credit fragments를 추가한다.
5. Locally prepared인 cross operation당 `Commit`/`Abort` full dual-fold와 cut selector를 구현한다. Rejected operation은 certified false bit와 Abort path만 만든다.
6. Conflict graph, component limits와 cut-after sequential fallback을 추가한다.
7. Componentized delta proof와 disjoint join을 구현해 non-conflicting suffix proof를 한 번만 생성한다.
8. 6 validators = 6 producer/state lanes E2E와 fault tests를 실행한다.
9. 실제 CPU proof backend와 microbenchmark를 같은 trait 경계에 연결한다.

첫 vertical slice의 완료 조건:

```text
6-node Multimmit
  -> local and cross-lane Bank blocks are DA-certified and ordered
  -> both branch proofs are generated before the decision cut for locally prepared operations when possible
  -> f+1 PACs are formed without blocking ordering
  -> complete debit+credit fragments select Commit on every honest node
  -> one missing/invalid fragment selects Abort on every honest node
  -> no honest node exposes a mixed commit/abort or unselected canonical effect
```

## 7. Benchmark driver

하나의 `proof_aware_bank` driver에서 mode와 workload를 바꾼다.

```text
--mode post-ordering|preexec-local|dual-fold|conflict-scoped|ordering-only
--pac-transport standalone|lqc-piggyback|hybrid
--validators 6 --lanes 6
--cross-ratio 0|25|50|75|100
--conflict-ratio 0|10|25|50|100
--hot-key-zipf 0|0.8|1.2
--decision-horizon-cuts 1|2|4|8
--max-unresolved-per-component N
--proof-delay-ms 0|50|100|300|600
--verify-delay-ms N --proof-bytes N
--block-gas N --offered-tps N --seed N
--fault none|missing-proof|late-proof|invalid-proof|prover-crash|fragment-omit|fragment-equivocate|false-manifest|branch-flood
```

Driver는 `T_cut_finalized`, `Delta_local`, `Delta_cross`, proof/PAC-ready-at-cut ratio, branch proof amplification, duplicated execution/proving work, component width, overlay bytes, fallback rate, standalone PAC messages, vote/L-QC bytes, throughput와 invalid/mixed state count를 machine-readable format으로 남긴다.

`MockProver`는 public-input commitment, configurable delay와 byte padding만 구현한다. Pipeline/system overhead에는 사용할 수 있지만 cryptographic soundness나 real proof throughput의 근거로 사용하지 않는다. Full dual-fold와 componentized join도 별도 결과로 보고해 proof reuse가 실제 구현된 범위를 과장하지 않는다.

## 8. 현재 코드와의 차이

현재 `commonware/glue/src/multimmit.rs`의 이전 execution/cross-lane reducer는 active 구현 계획에 포함하지 않는다. 새 vertical slice는 application rolling proof, `Commit`/`Abort` branch bundles, standalone/embedded `f+1` PAC, exact ordered-prefix selector와 selected-delta apply를 구현한다. 기존 synthetic tests와 benchmark는 이 branch-proof E2E 결과로 인용하지 않는다.
