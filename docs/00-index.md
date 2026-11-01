> 이전 추천 자료의 목차입니다. 여러 컴퓨터에 복원할 때는 저장소 루트 README를 먼저 읽으세요.

# Claude Code 추천 도구와 기억·지식관리 가이드

기준일: **2026-11-01** · 공식 문서와 제작자 저장소를 확인해 정리한 권장안

이 폴더에는 추천 문서와 실제 설치 결과가 들어 있습니다. 영어 전역 `CLAUDE.md`, 두 기억 플러그인, 공식 Dart/Flutter 도구, Obsidian 보관함과 자동 기록·검색 훅을 구성했습니다. 실제 저장·재검색까지 확인했고 Context7 로그인은 사용자 요청에 따라 남겨두었습니다. 현재 상태와 사용법은 [13 설치 결과와 자동 기억 운영](13-installed-memory.md)을 먼저 읽으세요.


**개발 스킬 추가 설치:** Matt Pocock 1.3.1과 pstack 0.15.36을 설치하고, Superpowers와 역할이 겹치지 않도록 전역 지침을 적용했습니다. 자동 호출 가능 범위와 직접 실행 명령은 [14 개발 스킬 설치와 역할 분담](14-skill-routing.md)을 확인하세요.

현재 요청에 가장 잘 맞는 출발점은 다음과 같습니다.

> **개발:** 사용하는 언어의 LSP + Context7 + 내장 `/code-review`
>
> **선호 기억:** 내장 Auto memory + `CLAUDE.md`
>
> **과거 대화 검색:** episodic-memory
>
> **지식 위키:** claude-obsidian

위 도구를 설치하는 것과, 자동 저장·검색을 하나의 흐름으로 연결하는 것은 별도 작업입니다. 특히 claude-obsidian의 기본 훅은 지식을 자동 작성하지 않습니다.

## 추가 심층 조사

**외부 도구 26종과 내장 기능 13개 묶음**을 추가 검토했습니다. 무엇을 더할지부터 보려면 [12 추가 조사 후 추천 우선순위](12-priorities.md)를 먼저 읽으세요.

- **기억·검색:** QMD, MCPVault, Obsidian Local REST API, Supermemory, Mem0, Hindsight, Pieces, Letta
- **개발:** ast-grep, Repomix, RTK, jCodeMunch, Semgrep Guardian, Sourcegraph, Playwright CLI, agent-browser, 공식 Dart/Flutter 도구, Docker MCP Toolkit
- **자료 수집·운영:** Tavily, Brave Search, Jina Reader, MarkItDown, Zotero 커뮤니티 도구, Rovo, Notion, DBHub
- **내장 기능:** 경로별 rules, 서브에이전트 기억, 세션 재개, Skills, 진단, Tool search, Worktree, Checkpoint, Goal, 예약 실행 등

각 항목의 용도·자동 실행 범위·선행 설정·비용·데이터 처리 위치·기존 구성과의 중복을 구분했습니다. 이 추가 조사는 추천 근거이며, 이후 실제 설치·자동화 작업 결과는 13번 문서에 별도로 기록했습니다.

## 문서 안내

| 문서 | 내용 |
|---|---|
| [01 개발용 추천](01-development.md) | 코드 탐색, 구현 절차, 리뷰, 웹 개발, 반복 업무 자동화, 고급 프레임워크 |
| [02 기억과 지식관리](02-memory-knowledge.md) | 선호 기억, 대화 검색, 지식 위키, 공유 메모리 및 대안 비교 |
| [03 자료수집과 외부연동](03-integrations.md) | 문서·웹 검색, PDF/OCR, Figma·GitHub·업무 서비스 연결 |
| [04 추천 조합](04-recommended-stack.md) | 사용 목적별 실제 시작 구성, 추가 순서, 중복 선택 기준 |
| [05 자동 저장과 검색 설계](05-memory-automation.md) | 기본 자동화 범위, 훅과 스킬의 차이, 별도 구현해야 할 통합 흐름 |
| [06 설치와 운영 참고](06-installation-operations.md) | 검증한 설치 명령 예시, 실행 위치, 연결 확인과 사용법 |
| [07 CLAUDE.md 적용 안내](07-claude-policy.md) | 실제 전역 지침 위치, 영어 규칙의 내용, 확인한 설치 상태와 남은 연결 조건 |
| [08 내장 기능 심화](08-built-in-features.md) | 새 플러그인 전에 활용할 기억·규칙·검증·병렬 작업·예약 실행 |
| [09 기억과 검색 추가 조사](09-memory-research.md) | 로컬 위키 검색 보강과 클라우드 기억 대체 후보 8종 |
| [10 개발 도구 추가 조사](10-development-research.md) | 구조 검색·코드 묶음·로그·보안·브라우저·Flutter 등 10종 |
| [11 자료 수집과 운영 추가 조사](11-integration-research.md) | 웹 검색·Office·논문·업무 서비스·DB 접근 8종 |
| [13 설치 결과와 자동 기억 운영](13-installed-memory.md) | 실제 설치 상태, 자동 동작, 검증 결과, 중지·복구 방법 |
| [12 추가 조사 후 추천 우선순위](12-priorities.md) | 무엇을 추가·대체·보류할지, 한국어 검색 평가와 목적별 조합 |
| [14 개발 스킬 설치와 역할 분담](14-skill-routing.md) | Matt·pstack 설치 버전, Superpowers와의 역할 분담, 자동·직접 호출 경계, 실측 검증 |

## 먼저 알아둘 구분

- **MCP:** 외부 도구·데이터를 호출하는 연결 방식입니다.
- **스킬:** Claude가 참고하거나 실행하는 작업 지침입니다.
- **플러그인:** 스킬·MCP·훅·에이전트 등을 묶어 배포하는 패키지입니다.
- **훅:** 세션 시작이나 도구 호출 같은 이벤트에 맞춰 작업을 실행합니다.
- **내장 기능:** 추가 플러그인 없이 Claude Code 자체가 제공하는 기능입니다.

같은 서비스가 MCP와 플러그인 양쪽으로 제공될 수 있습니다. 한 가지 설치 경로를 선택하고 중복 연결하지 않는 편이 관리하기 쉽습니다. [공식 확장 기능 설명](https://code.claude.com/docs/en/features-overview)

## 이 문서의 추천 표시

- **기본:** 대부분의 개발 작업에서 먼저 검토할 도구
- **선택:** 특정 작업이나 사용하는 서비스가 있을 때 추가
- **고급·조건부:** 별도 서비스 운영이나 개발 흐름 변경을 감수할 때 선택
- **참고·후순위:** 조사했지만 현재 추천 시작 조합에는 넣지 않은 도구

공식 마켓플레이스 등재와 Anthropic 자체 개발은 다릅니다. 제작자·플랫폼·커뮤니티의 도구가 함께 등록될 수 있습니다. [공식 마켓플레이스 설명](https://code.claude.com/docs/en/plugins/anthropic-marketplaces)

## 조사 중 확인한 정정 사항

1. 최신 Claude Code의 `/code-review`는 **내장 기능**입니다. 별도 code-review 플러그인을 기본으로 설치할 필요가 없습니다. [공식 문서](https://code.claude.com/docs/en/code-review-local)
2. episodic-memory의 README에는 세션 종료 색인 설명이 있지만, 확인한 `main` 브랜치 훅은 **SessionStart의 startup·resume·clear에서 백그라운드 sync**를 실행합니다. 이 문서는 실제 훅을 기준으로 설명합니다. [훅 설정](https://github.com/obra/episodic-memory/blob/main/hooks/hooks.json)
3. claude-obsidian의 훅은 선택형 시작 맥락과 복구 알림용이며, **지식을 쓰거나 갱신하지 않습니다.** [훅 문서](https://github.com/AgriciDaniel/claude-obsidian/blob/main/hooks/README.md)
4. 추천 도구의 무료 소스·로컬 저장과 AI 사용량·외부 처리 비용은 별개입니다. 각 도구의 실행 방식과 계정 설정을 기준으로 판단해야 합니다.
5. 내장 `/goal`, 기본 MCP Tool search 등 현재 기능까지 고려해 추가 도구를 고릅니다. 오래된 MCP 설치법·가격표·무료 라이선스 설명과 달라진 항목은 추가 조사 문서에 표시했습니다.

각 문서의 출처 링크는 조사 시점의 원문입니다. 향후 설치 시 설치 이름과 요구 버전은 해당 공식 안내를 다시 확인하는 것이 좋습니다.
