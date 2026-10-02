# Archive: producer placement와 이전 Overpass 설계

2026-09-29 사용자의 요청에 따라 이전 연구 자료를 현재 제안에서 분리했다. 현재 기준은 [새 연구 개요](../../../overpass-plan-ordering-outline.md)다.

## 보존한 snapshot

- 이전 root README·AGENTS·paper-outline: 당시 설계와 문서 탐색 경로.
- `state-affinity-placement*.md`: 과거 producer placement 버전들.
- `overpass-fixed-cut-implementation-plan.md`: placement를 포함하던 module 계획.
- `research/placement/`: grouping·routing 설계, 분석 코드, fixtures와 tests 전체.
- `research/paper/sections/04-placement.tex`, `09-placement-details.tex`, `placement-supplement.tex`, `figures/placement-sidecar.tex`: 이전 배치 알고리즘 본문·부록·그림.

Snapshot은 편집 전 원본을 복사한 것이다. 내부의 “현재/최신” 표현은 당시 시점에 한정된다. Snapshot 안의 AGENTS는 과거 기록이지 현재 작업 지침이 아니다. 완전한 standalone manuscript 복제본은 아니므로 상대 경로는 원래 project root 기준으로 해석한다.

## 원래 경로에 남겨 둔 자료

원래 경로의 placement 자료와 `research/paper/` manuscript·PDF는 기존 링크와 빌드 관계를 깨지 않도록 유지했다. 삭제하거나 새 protocol로 내용을 자동 변환하지 않았다. 이 자료들은 **reference-only**이며 현재 source of truth가 아니다.

Proof/PAC SDK·state-isolated branch-proof 자료, earlier progressive-ordering 탐색 역시 참고용이다. 새 연구에 producer placement·ZK·receipt bridge를 묵시적으로 다시 도입하지 않는다.

## 검증 범위

복사 시 주요 문서와 LaTeX 원본의 byte equality를 확인했다. 연구 코드의 실행 결과나 BFT safety를 새로 검증한 archive는 아니다. 기존 manuscript·Commonware fork·Google Docs는 이번 작업에서 개작하지 않았다.
