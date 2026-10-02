# 이전 연구 자료 보관

현재 읽고 수정할 문서는 [구현 스펙](../../IMPLEMENTATION_SPEC.md)과 [연구·논문 초안](../../baton-paper.md)이다.

Root의 역사 문서 39개와 관련 `research` 자료를 `repository/`에 원래 폴더 구조로 보존했다. 기준은 commit `b47cadba07dfa322e6b3da1671ed3ef748498b55`이며 당시 현재 문서와 assets도 사본으로 남겼다. 기존 archive의 상대경로가 원래 문서끼리 이어지도록 전체 topology를 보존한 snapshot이다. Snapshot 안의 current/latest 표현·AGENTS 지침·실험 결과는 당시 기록이며 현재 개발 지침이나 Baton 검증 결과를 대신하지 않는다.

[Snapshot 진입점](repository/README.md) · [이전 handoff](repository/SESSION_HANDOFF.md) · [보존 manifest](manifest.json)

원문 bytes와 당시 존재하던 repository 내부 상대경로를 확인했다. 기존에 이미 누락된 참조는 manifest에 별도로 기록했으며 snapshot을 임의 수정해 과거 자료를 현재 구현처럼 만들지 않는다. Private connector readbacks, 로컬 dependency runtime, 추가 원문 cache는 이 archive에 포함하지 않았다.
