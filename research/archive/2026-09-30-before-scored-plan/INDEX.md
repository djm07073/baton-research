# 보관: 점수 기반 plan과 bounded report collection 이전

2026-09-30의 README, AGENTS, 연구 개요, 논리 전개와 prefix-plan 기록을 원본 그대로 보존했다. 이 버전은 3f+1 공통 prefix 발견과 leader 조정 뒤 support 수집을 제안하던 시점이다.

현재 결정은 [plan 설계 기록](../../../overpass-prefix-plan.md)을 따른다. 별도 plan 승인 quorum을 제거하고, 보고들과의 공통 prefix 길이 합으로 후보를 선택한다. n=5f+1에서 보고 4f+1개 또는 local deadline 중 먼저 도달한 시점에 계산·전파하며 cut은 수집을 기다리지 않는다.

보관본의 “현재” 표현은 역사적 기록이며, 상대 링크는 원래 프로젝트 루트 기준이다. Commonware·LaTeX·Google Docs 변경을 뜻하지 않는다.
