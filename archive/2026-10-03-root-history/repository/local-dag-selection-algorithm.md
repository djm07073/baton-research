# Deterministic Local-DAG Selection

> 2026-09-18 후속: block-level 합성 및 recovery의 구체적인 규칙은
> [block-selected-view-protocol.md](./block-selected-view-protocol.md)를 우선한다.
> 아래는 이전 탐색 기록이다. 후속안에는 별도 PAC가 없으며 native Multimmit의
> prefix compatibility와 selection input closure를 별도의 구현 의무로 명시한다.

> 상태: exploratory algorithm note; authoritative protocol이 아님  
> 목적: Autobahn-family ordering을 막지 않으면서, 여러 validator의 speculative execution을 최대한 보존하는 하나의 execution DAG와 post-state를 결정한다.

## 1. 문제 정의

각 validator는 마지막 finalized state에서 시작해, 여러 producer lane으로부터 받은 blocks를 local DAG로 연결하고 cut 전에 speculative execution을 수행한다. 네트워크 도착 순서가 다르므로 다음처럼 서로 다른 view가 정상적으로 생길 수 있다.

```text
V1: X -> Y -> Z       (X,Y,Z 실행 완료)
V2: Y -> X -> Z       (Y,X 실행 완료)
V3: X -> Z; Y 독립    (X,Z 실행 완료)
```

Candidate cut이 exact block universe를 닫으면, 모든 validator가 같은 state를 만들도록 하나의 `SelectedDAG`를 결정해야 한다. 동시에 다음 순서로 기존 작업을 최대한 보존해야 한다.

1. 이미 연결되고 실행된 block fragments
2. 이미 연결되었지만 아직 실행되지 않은 block fragments
3. 그 다음으로 짧은 critical path와 canonical tie-break

단순 edge 다수결은 사용하지 않는다. 개별 edge가 각각 다수의 지지를 받아도 그 합집합이 cycle을 만들 수 있고, 이미 실행된 fragment를 중간에서 쪼개 재사용 불가능하게 만들 수 있기 때문이다.

### 1.1 Ordering과의 권한 경계

이 문서는 공격적인 **view-derived canonical merge**를 다룬다. Candidate cut proposal은 lane tips뿐 아니라 `EligibleViewSetRoot`와 synthesis algorithm version도 commit한다. 따라서 `SelectedDAG`가 정하는 conflicting transactions의 상대 순서는 ordering QC가 commit한 입력에서 결정적으로 도출된다. State-result quorum은 여러 DAG 중 하나를 다시 고르는 두 번째 consensus가 아니라, 이미 결정된 DAG의 실행 결과만 인증한다.

이는 Autobahn의 consensus core를 막지는 않지만, 기존 deterministic zip 이후의 merge rule을 확장한다. Ordering semantics를 전혀 바꾸지 않는 보수적 baseline에서는 cut-derived serial rank를 hard edge로 두고 `SelectedDAG`를 serially equivalent한 parallel schedule로만 사용한다. 두 mode의 성능을 실험에서 분리 비교해야 한다.

## 2. 두 종류의 state root

### 2.1 Local result root

각 `LocalDAGView`는 자신이 실제로 실행한 local plan의 결과를 commit한다.

```text
LocalDAGView {
  validator_id
  epoch
  parent_finalized_cut
  parent_state_root
  observed_lane_tips
  node_set_root
  semantic_dependency_root
  executed_fragment_root
  read_observation_root
  effect_root
  local_post_state_root
  application_code_hash
  execution_environment_hash
  view_sequence
  signature
}
```

`local_post_state_root`는 그 view의 exact node set, dependency order, input versions와 실행 환경에 대해서만 의미가 있다. 서로 다른 local views의 roots는 직접 비교하지 않는다.

### 2.2 Selected-plan result root

`SelectedDAG`가 결정되면 각 validator는 재사용 가능한 결과를 남기고 stale closure만 재실행한다. 그 뒤 다음 exact subject에 서명한다.

```text
ExecutionSubject = H(
  epoch,
  ordering_instance_id,
  parent_finalized_cut,
  parent_state_root,
  applied_parent_state_version,
  candidate_cut_digest,
  eligible_view_set_root,
  selected_DAG_root,
  synthesis_algorithm_version,
  application_code_hash,
  execution_environment_hash
)

ExecutionResult = H(
  occurrence_keyed_status_root,
  occurrence_keyed_effect_root,
  occurrence_keyed_event_and_receipt_root,
  component_delta_roots,
  exact_written_key_set_roots,
  global_post_state_root
)

ExecutionResultVote_v = Sign_v(ExecutionSubject, ExecutionResult)
```

동일한 `ExecutionSubject`인데 `global_post_state_root`가 다르면, deterministic execution 가정 아래 적어도 한 결과는 잘못되었다. 그러나 root 두 개만 보고 어느 쪽이 거짓인지 즉시 판별할 수는 없다. 동일 result에 대한 state quorum이 형성된 뒤 minority result를 배제한다.

Equal-weight Multimmit-style `n=5f+1` deployment에서 state-result quorum을 `q=3f+1`로 두면 두 conflicting certificates의 signer intersection은 최소 `f+1`이다.

\[
2(3f+1)-(5f+1)=f+1
\]

Honest validator가 동일 subject에 하나의 result만 서명하면 서로 다른 두 state-result certificates는 동시에 형성될 수 없다. `f+1` PAC는 proof/result의 복구 가능성을 위한 availability evidence일 뿐, state-result agreement를 대체하지 않는다.

일반적인 equal-weight configuration의 uniqueness 조건은 `2q-n>f`다. Stake-weighted committee에서는 signer 수 대신 voting power와 weighted quorum/quantile을 사용해야 한다.

State root 불일치는 다음처럼 처리한다.

- Subject가 다르면 서로 다른 실행을 비교한 것이므로 Byzantine evidence가 아니다.
- Subject가 같으면 component roots를 비교해 최초 divergence 후보를 찾는다. Authenticated disjoint key/effect domains와 dependency closure가 검증될 때만 그 component로 재검증을 제한하며, 아니면 전체 affected cut을 재검증한다.
- `q` matching result가 형성되면 다른 result는 canonical apply에서 제외한다.
- Protocol은 minority signer를 faulty로 취급할 수 있지만, slashing에는 double-signature, validity/fraud proof 또는 재현 가능한 execution witness처럼 제3자가 검증할 증거가 별도로 필요하다.

## 3. View set을 cut에 binding해야 하는 이유

Leader가 자신에게 유리한 views만 고르면, 이미 실행한 작업이 많은 공모자만 점수에 넣거나 불리한 honest view를 누락할 수 있다. 따라서 `SelectedDAG`의 입력은 candidate cut으로부터 기계적으로 정해져야 한다.

권장 방식은 각 selected lane tip이 해당 validator/lane의 최대 valid cumulative `view_sequence` 하나를 anchor하는 것이다. Block header에는 다음 fixed-size signed envelope를 넣는다.

```text
ViewEnvelope {
  validator_and_lane_id
  epoch
  parent_cut_and_state_root
  covered_prefix_root
  view_sequence
  parent_view_hash
  view_sidecar_root
  sidecar_encoding_and_byte_length
  custody_certificate_digest
  signer_signature
}
```

Envelope는 **cut 전에 형성된 `f+1` sidecar-custody certificate**를 가리킨다. 각 custody signer는 exact sidecar root, encoding version, byte length와 retention horizon에 서명하고 reconstructable bytes를 보관한다. Candidate cut이 lane tips를 고르면 exact eligible envelope set도 함께 고정된다.

```text
EligibleViewSet(C) =
  max cumulative view per validator/lane
  whose hash and availability certificate are anchored
  by the lane prefixes selected by candidate cut C
```

각 view는 exact epoch, parent cut/root, prefix coverage, signer, parent-view hash와 monotonically increasing sequence를 bind한다. 한 validator/lane은 한 번만 점수화한다. 같은 maximum sequence에 서로 다른 hashes가 있으면 두 view 모두 제외하고 `bottom`으로 두며 equivocation evidence를 남긴다. 중복과 dominance를 제거한 뒤 validator ID 순으로 canonical serialization하여 `EligibleViewSetRoot`를 계산한다. Ordering voter는 sidecar를 fetch하지 않고 selected headers의 envelopes만으로 signature, base/prefix coverage, sequence dominance, equivocation rule와 root equality를 검증한다. Custody certificate는 현재 epoch의 서로 다른 `f+1` committee members, cryptographic signature validity, exact `(sidecar root, encoding, byte length)` binding과 protocol minimum retention horizon을 모두 만족해야 한다. Retention은 적어도 state certificate 형성 또는 archival handoff까지 지속된다. Sidecar의 semantic validity는 bytes 복구 후 모든 노드가 같은 규칙으로 판정한다.

Leader는 candidate cut과 선택 결과를 전달할 뿐이다. 모든 validator가 같은 `Synthesize(C, EligibleViewSet(C))`를 다시 계산한다.

- Signature, anchor 또는 canonical encoding이 invalid한 view는 모든 노드가 객관적으로 제외한다.
- Eligible sidecar를 아직 받지 못한 경우는 empty view가 아니라 `NeedData(view_hash)`다. 해당 노드는 execution vote를 보류하되 ordering vote와 block production은 계속한다.
- Availability certificate가 없는 commitment는 처음부터 모든 노드가 `bottom` view로 처리한다. Local fetch timeout 때문에 eligibility가 달라지지 않는다.
- 따라서 view sidecar commitment도 Autobahn data path에서 복구 가능해야 한다. Certificate signer는 protocol retention window 동안 reconstructable bytes를 저장·serve한다. Erasure coding을 사용하면 chunk 수와 reconstruction threshold를 별도로 commit한다.

이 규칙은 선택된 view set을 합의 입력에 binding하지만, leader가 lane tips를 고르며 간접적으로 view set을 편향하는 것까지 완전히 제거하지는 않는다. 그 공격면까지 없애려면 이전 slot에서 별도로 확정한 `ViewBatchRoot`를 사용하는 강화안이 필요하다.

## 4. Fragment와 재사용 조건

Local physical thread order는 합성 입력에서 제거한다. View는 application semantics에 필요한 fragments만 commit한다.

```text
ExecutedFragment {
  base_finalized_root
  fragment_plan_root
  nodes
  occurrence_and_transaction_roots
  manifest_root
  code_and_environment_root
  semantic_dependencies
  read_observations: [
    PointObservation {
      access_id,
      read_kind,
      source = BaseState(version) | OccurrenceID,
      source_output_slot,
      source_effect_commitment,
      observed_value_or_predicate_commitment
    }
    | RangeObservation {
      access_id,
      range_descriptor,
      index_version_root,
      source_set_root,
      membership_and_nonmembership_witness_root,
      result_commitment
    }
  ]
  actual_read_set_root
  actual_write_set_root
  write_set_root
  effect_root
  status_and_events_root
  protocol_execution_weight
  compute_proof
}

LinkedFragment {
  nodes
  semantic_dependencies
  protocol_link_weight
}
```

각 multi-node fragment의 sidecar는 `fragment_plan_root`와 occurrence별 read/write records를 제공하며, 상위 roots에는 inclusion proofs를 제공한다. Root만 제출하고 원자료를 제공하지 않으면 실행 검증이나 repair에 사용할 수 없다.

Plan `D`가 linked fragment를 보존한다는 것은 그 fragment의 모든 semantic precedence를 유지한다는 뜻이다. Executed result의 재사용은 다음 세 등급으로 나눈다.

```text
ExactReuse(F, D) iff
  ReuseEligible(F, D)
  AND PreserveSemanticEdges(F, D)
  AND CanonicalReadTranscript_D(F) == F.read_observations
  AND VerifyComputeAndBindingProofs(F)

ComputeReuse(F, D) iff
  ReuseEligible(F, D)
  AND ObservableTranscript_D(F) == ObservableTranscript(F)
  AND VerifyComputeProof(F)
  // source identity만 바뀌었으므로 binding proof만 다시 만든다.

ExecutionReuse(F, D) iff
  ReuseEligible(F, D)
  AND ObservableTranscript_D(F) == ObservableTranscript(F)
  AND VerifyCommittedTraceAndEffect(F)
  // 실행 결과는 유지하지만 compute/binding proof는 다시 만든다.

ReuseEligible(F, D) iff
  SameBaseOccurrenceTxManifestAndEnvironment(F, D)
  AND ActualAccessesWithinManifest(F)
  AND F.status is a deterministic terminal VM/application status
  AND F.status is not scheduler-local abort/stall/speculative failure

Reexecute(F, D) iff
  observable value, existence, metadata, size, range predicate,
  module/config 또는 다른 execution input이 달라졌다.
```

Full global input root만 사용하면 무관한 state update에도 cache가 무효화된다. 따라서 fragment-level reuse에는 read versions와 write/effect commitments가 필요하고, component composition에는 delta/witness roots, 최종 수렴 검증에는 global post-state root가 필요하다.

`read_kind`에는 value read뿐 아니라 existence/non-existence, metadata, resource size, metadata+size, range/phantom predicate, resource group, module/config, delayed field, fee와 nonce처럼 결과에 영향을 주는 hidden input도 포함한다. Range observation은 단일 writer가 아니라 ordered source set과 gaps에 bind되어 phantom insert/delete도 검출한다. 노드마다 다른 speculative 재실행 횟수(`local_incarnation`)와 terminal status는 local cache freshness와 stale-completion fence에만 사용하며, submitted fragment commitment, `SelectedDAG` 또는 execution vote에 넣지 않는다. 최신 generation만 output 설치와 reader invalidation을 수행할 수 있다.

Proof를 사용하는 구현은 다음처럼 분리하는 편이 재사용에 유리하다.

```text
ComputeProof:
  (tx, code/environment, complete observation transcript)
    -> (status, writes, events, effects)

ReadBindingProof:
  (fragment/observation root, canonical read-from sources)
    -> observed values

SelectedDAGInclusionWitness:
  fragment/occurrences are included under SelectedDAGRoot
```

Read binding의 최소 subject와 whole-DAG inclusion witness를 분리하므로 unrelated DAG region이 바뀌어도 core binding proof를 유지할 수 있다. Source writer가 바뀌었지만 complete observable transcript가 같으면 비싼 compute proof를 유지하고 binding만 갱신할 수 있다. Value나 predicate가 바뀔 때만 해당 fragment를 다시 실행·증명한다. Fragment의 write/effect는 재사용할 수 있어도 sibling composition이나 write order가 달라지면 intermediate component root는 바뀔 수 있으므로 component root를 fragment 산출물로 취급하지 않는다.

실행 완료로 점수화할 수 있는 record는 validity-verified compute proof 또는 protocol이 인정한 trace/effect evidence를 가져야 한다. 그렇지 않으면 linked-only로 취급한다. 비용은 validator가 보고한 wall-clock이 아니라 transaction/circuit에서 결정되는 capped deterministic weight를 사용하며, 첫 prototype은 모든 fragment에 unit weight를 줄 수 있다.

## 5. 안전 제약과 최적화 제약

### 5.1 반드시 지켜야 하는 hard constraints

- Candidate cut에 포함된 occurrence가 정확히 한 번씩 나타난다.
- Lane-local parent order, nonce order와 명시적 causal dependency를 보존한다.
- Static access manifests에서 도출한 모든 conflicting pair가 한 방향으로 ordered된다.
- Cross-lane logical operation의 모든 fragments는 하나의 atomic node처럼 같은 위치에서 성공 또는 실패한다.
- Graph는 acyclic이다.
- Application/code/environment version과 parent root가 일치한다.
- VM이 manifest completeness를 enforce하고 undeclared access는 deterministic transaction failure로 처리한다. Discovery-based fallback을 쓰려면 cut-derived reference order로 entire affected closure를 재실행하는 규칙을 별도로 정의해야 한다.

이 조건들은 local view의 vote 수와 무관하게 모든 validator가 직접 검증한다.

### 5.2 보존 목적함수

Validator `v`가 plan `D`를 따를 때 남은 실행 작업량을 다음처럼 정의한다.

\[
Saved_v(D)=\sum_{F\in Executed_v}
\begin{cases}
w_{exec}+w_{prove}+w_{bind}, & ExactReuse(F,D)\\
w_{exec}+w_{prove}, & ComputeReuse(F,D)\\
w_{exec}, & ExecutionReuse(F,D)\\
0, & otherwise
\end{cases}
\]

\[
X_v(D)=TotalExecWork(D)-Saved_v(D)
\]

\[
L_v(D)=\sum_{F\in LinkedOnly_v} ProtocolWeight(F)\,[\neg PreserveLinked(F,D)]
\]

Overlapping/cumulative fragments가 동일 작업을 중복 credit하지 않도록 `NormalizeSemanticFragments`는 fragments를 atomic `(OccurrenceID, proof-work ID)` units로 펼치고 각 unit을 한 번만 계산한다. 따라서 `Saved_v(D)<=TotalExecWork(D)`다. 동등하게 구현하려면 canonical maximal disjoint fragment partition만 제출하게 할 수 있다.

`TotalExecWork(D)`와 모든 fragment weight는 candidate 실행 뒤에야 알 수 있는 dynamic gas나 wall-clock이 아니라 protocol-defined capped static work units만 사용한다. 이미 validity-verified된 trace weight만 예외적으로 사용할 수 있다. 따라서 synthesis objective가 candidate 실행 결과에 순환 의존하지 않는다.

`C_v(D)=(X_v(D),L_v(D))`를 lexicographically 비교한다. 즉 이미 실행한 작업 손실을 먼저 최소화하고, 그 다음 이미 연결한 작업 손실을 최소화한다. `Q_r(D)`는 이 vector들을 lexicographic order로 정렬했을 때 `r`번째 값이다.

State result에 `q` signatures가 필요하면 평균 손실보다 `q`번째로 빨리 준비되는 validator의 남은 작업이 state-finality latency에 더 직접적이다. Byzantine validators `f`명이 준비됐다고 보고한 뒤 응답을 숨기는 경우까지 견디는 robust objective는 다음이다.

```text
Objective(D) = minimize lexicographically:
  1. Q_(q+f)(D) = (executed loss, linked loss)
  2. Q_q(D)     = (executed loss, linked loss)
  3. total executed loss
  4. total linked loss
  5. weighted critical path
  6. canonical structural encoding of SelectedDAG
```

`q+f <= n`인 configuration에서만 robust 첫 항을 사용한다. 두 loss의 marginal quantile을 따로 계산하면 서로 다른 validator 집합을 섞게 되므로 반드시 pair 전체를 정렬한다. View를 제출하지 않은 validator는 모든 작업을 다시 수행하는 것으로 계산한다. `Q_(q+f)`는 Byzantine withholding에 대비한 deterministic work proxy이지, 실제 network delay, hardware speed 또는 crash를 포함한 wall-clock liveness bound는 아니다.

## 6. Deterministic synthesis algorithm

### 6.1 Conflict components

Candidate cut의 static manifests에서 undirected conflict graph를 만든다. 서로 state를 공유하지 않는 connected components는 독립적으로 선택하고 마지막에 disjoint union한다. 이로써 한 hot state의 disagreement가 전체 cut으로 퍼지지 않는다.

### 6.2 Whole templates와 SCC synthesis를 함께 사용

각 component에서 candidate plans를 다음처럼 만든다.

1. Protocol-defined canonical fallback plan
2. Valid views가 제출한 distinct complete component templates
3. 여러 views의 compatible regions를 결합한 synthesized plan
4. Disagreement SCC가 충분히 작을 때 exact-search plan

Whole template을 후보에 반드시 포함하는 이유는 edge heuristic이 이미 실행된 multi-edge fragment를 잘게 깨뜨리는 것을 막기 위해서다. Synthesized plan이 나쁘면 exact fragment objective에서 complete template이나 fallback에게 진다.

### 6.3 Disagreement를 SCC로 국소화

각 view는 edge list의 표기 방식이 아니라, 함께 관측한 모든 conflicting pair의 relative orientation으로 normalize한다. 따라서 같은 partial order를 transitive closure로 보냈는지 reduction으로 보냈는지에 따라 점수가 달라지지 않는다. Scheduler-only edges는 제거한다.

모든 valid view의 normalized semantic preferences를 합친다. 어떤 view도 함께 보지 못한 conflict pair에는 protocol-defined canonical fallback orientation을 넣은 뒤 SCC를 계산한다. Hard edges는 별도로 표시하고 절대 뒤집지 않는다.

```text
edge weight(u -> v) = (
  executed-fragment support/cost,
  linked-only support/cost
)
```

Union graph에 cycle이 생기면 Tarjan SCC를 계산한다. 서로 다른 SCC 사이 edge는 cycle에 속하지 않으므로 유지할 수 있고, 실제 선택은 nontrivial SCC 안으로 제한된다. Incomparable SCC들을 임의의 list로 직렬화하지 않고 condensation DAG의 partial order를 그대로 유지한다.

SCC 내부에서 가장 많은 preference를 보존하는 것은 weighted feedback-arc/rank-aggregation 문제를 포함하므로 일반적으로 NP-hard다. 따라서 다음의 bounded deterministic policy를 사용한다.

- 작은 SCC: canonical branch-and-bound로 atomic fragment objective를 exact하게 계산한다.
- 큰 SCC: executed weight를 먼저, linked weight를 다음으로 보는 deterministic feedback-arc heuristic을 사용한다.
- 고정된 횟수의 deterministic local improvement를 수행한다.
- Wall-clock deadline이나 nondeterministic solver 결과를 consensus input으로 사용하지 않는다.

### 6.4 Pseudocode

```text
Synthesize(candidate_cut C, eligible_views V, q, f):
    occurrences := ExpandAndVerifyExactCut(C)
    valid_views := ValidateAnchorsSignaturesAndSidecars(V, C)
    if any eligible sidecar is not locally available:
        return NeedData(missing_view_hashes)

    occurrences, preinvalid_bundles :=
        DeterministicallySanitizeManifestsAndReferences(occurrences)
    conflict_graph := BuildConflictGraph(occurrences.access_manifests)
    components := ConnectedComponents(conflict_graph)
    component_candidate_sets := []

    for K in CanonicalComponentOrder(components):
        hard, invalid_bundles :=
            BuildAndTotalizeHardEdges(K, preinvalid_bundles)

        fragments := NormalizeToConflictPairOrientations(valid_views, K)
        fallback_edges := CanonicalEdgesForUnobservedConflicts(K, fragments)
        union := hard UNION AllSemanticPreferenceEdges(fragments)
                      UNION fallback_edges
        sccs := TarjanSCC(union)

        solved_sccs := {}
        for S in CanonicalSCCIDOrder(sccs):
            if Size(S) <= EXACT_LIMIT:
                part := ExactHardEdgeRespectingSearch(S, fragments)
            else:
                part := DeterministicExecutedFirstHeuristic(S, fragments)
                part := FixedPassLocalImprove(part, fragments)
            solved_sccs[S.id] := part

        synthesized := ComposeOnCondensationDAG(
            Condensation(sccs), solved_sccs
        )

        candidates := {
            CanonicalFallbackPlan(K),
            BuildPlan(synthesized),
            CompleteComponentTemplates(valid_views, K)
        }

        candidates := FilterByHardConstraints(candidates)
        component_candidate_sets.append(candidates)

    global_candidates := DeterministicBoundedCombine(
        component_candidate_sets,
        exact_product_limit = GLOBAL_EXACT_LIMIT,
        otherwise_beam_width = FIXED_BEAM_WIDTH
    )
    global_candidates += {
        GlobalCanonicalFallback(components),
        CompleteGlobalViewProjections(valid_views, components)
    }

    global_candidates :=
        FilterByGlobalHardConstraints(global_candidates)
    if global_candidates is empty:
        global_candidates := {TotalizedGlobalCanonicalFallback(components)}

    winner := ArgMin(global_candidates, GlobalObjective_q_plus_f_then_q)
    tie_break winner by lexicographically smallest canonical occurrence/edge encoding
    return winner
```

`Synthesize`는 모든 ordering-valid cut에서 결과를 내는 total deterministic function이어야 한다. `BuildAndTotalizeHardEdges`는 malformed manifest/reference/self-cycle을 가진 occurrence를 포함한 atomic bundle 전체를 `Invalid/No-op`으로 표시한다. Hard-edge SCC가 남으면 SCC 안의 canonical structural bundle ID가 가장 큰 bundle을 no-op 처리하고, cycle이 없어질 때까지 반복한다. No-op occurrences도 output map에는 정확히 한 번 나타난다. Candidate filtering 결과가 비면 동일하게 totalized hard graph의 canonical structural order를 사용하는 fallback candidate를 반드시 생성한다. 따라서 Byzantine payload가 poison cut을 만들어 state finality를 영구 정지시킬 수 없다.

`DeterministicBoundedCombine`은 다음처럼 완전히 고정한다.

```text
DeterministicBoundedCombine(candidate_sets, exact_limit, beam_width):
    sets := sort candidate_sets by component_id
    if product(Size(set) for set in sets) <= exact_limit:
        return every Cartesian combination in structural order

    beam := {empty_assignment}
    for set in sets:
        expanded := {}
        for partial in beam ordered by canonical structural encoding:
            for candidate in set ordered by canonical structural encoding:
                next := partial UNION candidate
                key := canonical partial occurrence/edge encoding
                deduplicate exact same key
                expanded.add(next)

        for next in expanded:
            lower_bound(next) := GlobalObjective using
                accumulated per-validator repair for assigned components,
                zero optimistic repair for unassigned components,
                accumulated totals and critical-path lower bound,
                canonical structural encoding as final tie-break

        beam := first beam_width entries after sorting by
                (lower_bound, canonical structural encoding)

    return beam
```

이 beam search는 global optimum 보장이 아니라 bounded deterministic approximation이다. Beam이 완성된 뒤 global canonical fallback과 complete global view projections를 추가하고, 모든 complete candidates를 exact global objective로 다시 비교한다.

The authoritative output is a pure function of:

```text
(candidate cut, eligible view set, algorithm version)
```

Leader가 `SelectedDAGRoot`를 함께 보내더라도 이는 검산을 줄이는 hint일 뿐이다. Validator가 재계산한 root와 다르면 state acceleration 경로에서 무시하며, Autobahn ordering vote 자체는 막지 않는다.

Component별 `q`번째 손실을 따로 최소화하면 각 component에서 서로 다른 fast quorum을 고를 수 있어 global root를 빨리 완성하는 validator가 `q`명 되지 않을 수 있다. 따라서 baseline은 component candidate들을 만든 뒤, whole-cut plan별 validator 총 repair cost를 합쳐 **global** `Q_q`로 최종 선택한다. Cartesian product가 작으면 exact search하고, 크면 protocol parameter로 고정한 deterministic beam search를 사용한다.

## 7. SelectedDAG 실행과 state finality

```text
candidate cut received
  -> derive the same SelectedDAG
  -> classify each record as exact-reuse, binding-dirty,
     compute-dirty, or join-dirty
  -> resolve canonical sources for value, negative, range,
     base-state and previous-writer readers
  -> push invalidation only to readers whose observation changed
  -> on reexecution, remove writes present in the old generation
     but absent from the new generation before installing new writes
  -> move/invalidate readers of removed or changed outputs
  -> reexecute until relevant output observations stop changing
  -> wait for quiescence: dirty queue empty, no pending invalidation,
     every accepted record is latest-generation terminal output,
     and all old-write cleanup is complete
  -> deterministically join accepted writes
  -> compute component delta/witness roots and global post-state root
  -> gossip ExecutionResultVote

ordering cut finalized
  AND q matching ExecutionResultVotes available
  -> apply state immediately

otherwise
  -> ordering continues
  -> missing execution/proof data is fetched asynchronously
  -> global state root becomes ready after q validators finish every required component
```

Ordering vote의 validity 조건은 기존 Autobahn QC/lock, exact lane tips/prefixes, header `ViewEnvelope`s, envelope에서 재계산한 `EligibleViewSetRoot`, full custody-certificate validity/minimum-retention check와 resource bounds까지만 포함한다. Validator는 view sidecar fetch, synthesis, execution, proof 생성 또는 `ExecutionResultVote`를 기다리지 않는다. Candidate를 받았을 때 sidecar가 이미 있는 validator는 speculative synthesis를 시작하고, state apply는 finalized exact cut과 state certificate가 함께 있을 때만 한다.

Aggressive mode에서 eligible view sidecar를 아직 복구하지 못한 노드는 canonical conflict order 자체를 모르므로 임의의 serial fallback을 실행하지 않는다. Availability assumption 아래 `NeedData` 상태로 state vote만 보류한다. Transaction payload fallback은 `SelectedDAG`가 결정된 뒤 missing fragment proof/effect를 locally reexecute할 때, 또는 conservative cut-derived-order mode에서만 사용한다. Permanent sidecar failure에 대한 fallback이 필요하면 local timeout이 아니라 ordering에 미리 bind된 finalized-cut-count switch rule/certificate를 별도로 정의해야 한다.

Parallel scheduler의 실제 completion order는 public result encoding에 영향을 주지 않는다. Status와 effects는 `OccurrenceID` keyed Merkle map으로, events/receipts는 `(OccurrenceID,event_index)` keyed map으로 serialize한다. State writes의 semantics는 `SelectedDAG`가 정하지만, incomparable nodes의 commitment order는 canonical occurrence ID로 정한다. 따라서 같은 DAG를 다른 worker schedule로 실행해도 byte-identical `ExecutionResult`가 나온다.

Candidate cut과 finalized cut이 다르면 그 candidate의 state-result votes는 canonicality를 만들지 않는다. Exact same cut과 exact same selected plan에 대해서만 join한다.

Static conflict graph의 모든 descendants를 무조건 폐기하면 repair가 과도해진다. 구현은 writer output뿐 아니라 base/missing version, negative/range observation에도 actual readers를 등록한다. 이전 generation의 write set과 새 write set을 diff하여 사라진 old write를 overlay에서 먼저 제거한다. Write가 create/modify/delete/delta되거나 사라질 때 해당 `read_kind`의 관찰이 깨진 direct readers만 dirty queue에 넣는다. Source identity만 바뀌고 complete observation이 같으면 binding만 갱신한다. 재실행 뒤 relevant output observations가 같으면 reader dependency를 새 source로 이관하고 전파를 멈춘다. W/W-only successor는 재실행하지 않아도 되지만 final canonical write join은 다시 계산한다. Quiescence barrier를 통과하기 전에는 state root를 계산하거나 vote하지 않는다. 이는 Block-STM의 versioned read validation과 push invalidation에서 가져온 원칙이다.

Baseline의 `component_delta_roots`는 divergence localization과 global root 재계산을 위한 statements이며, component별 독립 finality certificate는 아니다. 각 component artifact sidecar는 exact written-key set과 parent-root-bound Merkle/JMT transition witness를 포함해야 한다. 여러 valid multiproof encodings가 있을 수 있으므로 witness bytes/root 자체는 matching result vote에 넣지 않고 별도 availability-certified sidecar로 둔다. Verified key-domain disjointness와 deterministic delta join이 하나의 `global_post_state_root`를 산출한다. Component-asynchronous state readiness를 추가하려면 별도의 `ComponentExecutionSubject`, component QC와 deterministic global join 규칙을 정의해야 한다.

Honest validator는 exact subject에 대해 transaction status, complete effects, read bindings와 resulting root를 직접 검증한 뒤 persistent one-vote rule을 지킨다. State certificate는 exact `(ExecutionSubject, ExecutionResult)` equality에 `q` votes가 모였을 때만 성립한다. Equal-weight model의 조건은 safety `2q>n+f`, liveness `q<=n-f`이며 `n=5f+1`이면 최소 integer quorum이 `3f+1`이다. Root certificate와 별도로 full node가 effects/proofs를 가져갈 수 있는 `f+1` availability certificate가 필요하다.

### Example: root mismatch

`f=1`, `n=6`, `q=4`라 하자. 같은 subject를 실행한 결과가 다음과 같다.

```text
V1: R42
V2: R42
V3: R42
V4: R42
V5: R99
V6: no response
```

`R42`에 네 signatures가 모이므로 state-result certificate가 형성된다. `R99`는 적용되지 않는다. Verified component delta roots가 `Account=DA`, `Orderbook=DB`인데 V5만 `Orderbook=DB'`라면 authenticated disjointness와 dependency witness를 확인한 뒤 재검증 범위를 Orderbook component와 그 readers로 좁힐 수 있다.

반대로 `R42` 두 표, `R99` 두 표뿐이라면 어느 쪽도 canonical state가 아니다. Ordering은 완료될 수 있지만 state finality는 추가 실행 결과를 기다린다.

## 8. Byzantine과 failure handling

- **Leader view substitution/omission:** cut-committed view set과 sidecar DA로 검출한다. Tip 선택을 통한 간접 편향은 남으며, 필요하면 prior-slot `ViewBatchRoot`로 강화한다.
- **거짓 connected/executed report:** 안전성에는 영향을 주지 않는다. Exact read versions, effects와 root를 검증하지 못하면 재사용하지 않는다. 성능 점수 조작은 robust rank와 quorum-supported records로 제한한다.
- **Conflict 누락:** static manifest에서 모든 validator가 conflict graph를 다시 만든다.
- **Cycle/SCC inflation:** scheduler-only edges를 제거하고 실제 semantic conflicts만 입력으로 허용한다.
- **Result withholding:** `q+f` readiness objective와 sidecar replication을 사용하되, ordering은 기다리지 않는다.
- **Wrong state root:** matching state quorum에 들지 못한다. Verified disjointness와 dependency witness가 있을 때만 component 범위로 국소 재검증한다.
- **Missing committed view:** `NeedData`로 execution vote를 보류하고 DA holders에게 요청한다. Ordering은 계속된다. Objectively invalid view만 모든 노드가 동일하게 제외한다.
- **Missing fragment proof:** view와 plan이 정해진 뒤 해당 fragment를 locally reexecute하거나 proof를 복구한다.
- **Algorithmic DoS:** component size, manifest entries, exact-search threshold와 local-improvement pass count를 protocol parameter로 제한한다.

## 9. 기존 연구와 정확한 경계

- Generalized Paxos는 commuting commands의 서로 다른 histories를 동등하게 다룬다.
- EPaxos, BPaxos와 Byzantine ISOS는 dependency reports를 합치고 cycle을 SCC로 실행한다.
- Vegeta는 proposer가 speculative execution으로 dependency DAG를 만들고 consensus 후 replay한다.
- Block-STM은 이미 정해진 transaction order 아래 read-set validation과 selective reexecution을 수행한다.
- Feedback-arc/Kemeny 연구는 여러 conflicting orders의 최적 합성이 NP-hard임을 설명한다.

따라서 novelty를 단순히 “DAG를 합친다” 또는 “SCC를 사용한다”로 주장하면 약하다. 검증할 핵심 claim은 다음이다.

> Autobahn-family cut에 포함된 여러 divergent speculative execution views를 deterministic하게 합성하되, state-root-bound executed fragments를 첫 번째 우선순위로, semantic links를 두 번째 우선순위로 보존하여 state quorum의 남은 작업을 최소화한다.

이 claim은 다음과 분리해 평가해야 한다.

- Canonical zip/fallback execution
- 가장 많은 지지를 받은 whole local view 선택
- Edge-majority + canonical cycle breaking
- Proposed component/SCC synthesis
- Small-component oracle optimum

주요 지표는 preserved executed work, preserved linked work, dirty closure, synthesis time, critical path, matching roots ready at cut, 그리고 cut-to-state-finality latency다.

## 10. 선행연구

- [Autobahn, SOSP 2024](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf)
- [EPaxos, SOSP 2013](https://www.pdl.cmu.edu/PDL-FTP/associated/epaxos.pdf)
- [BPaxos](https://arxiv.org/abs/2003.00331)
- [ISOS, PRDC 2021](https://arxiv.org/pdf/2109.06811)
- [Vegeta, NSDI 2025](https://www.usenix.org/system/files/nsdi25-xu-tianjing.pdf)
- [Block-STM](https://arxiv.org/abs/2203.06871)
- [Generalized Paxos](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2005-33.pdf)
- [Kemeny/weighted feedback-arc PTAS](https://cs.brown.edu/~claire/Publis/kenyonschudy.pdf)
- [Parameterized feedback-arc algorithms](https://arxiv.org/abs/1006.4396)
- [Eades-Lin-Smyth feedback-arc heuristic](https://doi.org/10.1016/0020-0190(93)90079-O)
