> 이 문서는 2026-11-01 조사·설치 기록입니다. 새 컴퓨터에서는 루트 README와 `scripts/bootstrap.py`를 우선 사용하세요. `$HOME`은 해당 컴퓨터의 홈 디렉터리이며, 당시 경로·검증 결과가 새 컴퓨터에 그대로 적용되는 것은 아닙니다.

# 목적별 추천 조합

> 설치 후 갱신: 두 기억 플러그인·자동 훅·Obsidian 보관함·공식 Dart/Flutter 도구를 구성했고 실제 저장·검색을 검증했습니다. Context7 로그인은 나중에 진행합니다. 아래는 설치 전 추천 근거이며, 현재 상태는 [13 설치 결과](13-installed-memory.md)를 우선합니다.

기준일: 2026-11-01 · 문서·소스 조사에 따른 권장안이며 실제 설치 검증은 하지 않았습니다.

추가 조사 후의 세부 도입 순서는 [12 추천 우선순위](12-priorities.md)를 참고합니다. 아래 기본 조합은 유지하며 구조 검색·위키 검색·자료 변환 등 부족한 역할을 선택적으로 보강하는 방향입니다.

모든 후보를 한꺼번에 설치하는 대신, 아래 조합 중 자신의 작업에 맞는 구성을 출발점으로 삼습니다.

## 현재 요청에 가장 맞는 구성

| 역할 | 선택 | 맡길 일 |
|---|---|---|
| 코드 이해·진단 | 사용하는 언어의 LSP | 정의·참조 탐색, 언어 서버 진단 |
| 라이브러리 문서 | Context7 | API와 버전에 맞는 사용법 조회 |
| 변경 검토 | 내장 `/code-review` | 브랜치·경로·PR의 변경 검토 |
| 선호·프로젝트 규칙 | 내장 Auto memory + `CLAUDE.md` | 선호·교정 사항과 명시적인 프로젝트 지침 |
| 과거 대화 | episodic-memory | 이전 결정·시도·실패 과정 검색 |
| 지속적으로 관리할 지식 | claude-obsidian | 검증된 해결법·설계 근거·학습 자료를 출처와 함께 저장 |

기본 도구 근거: [LSP](https://code.claude.com/docs/en/plugins/code-intelligence), [Context7](https://context7.com/docs/clients/claude-code), [내장 리뷰](https://code.claude.com/docs/en/code-review-local), [내장 기억](https://code.claude.com/docs/en/memory), [episodic-memory](https://github.com/obra/episodic-memory), [claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian).

이 조합에 대한 권장 이유는 각 도구가 서로 다른 대상을 담당하기 때문입니다. 프로젝트 규칙은 짧게 유지하고, 과정은 검색 가능하게 남기며, 결론은 사람이 읽는 위키로 정리할 수 있습니다. 후속 요청으로 검색·선별 저장 규칙을 전역 CLAUDE.md에 적용했지만, 실제 도구 연결·저장·검색은 아직 검증하지 않았습니다. [적용 상태](07-claude-policy.md)

## 사용 목적에 따른 추가 구성

| 목적 | 시작 구성 | 필요한 경우 추가 |
|---|---|---|
| 가벼운 일반 개발 | LSP + Context7 + 내장 리뷰·기억 | Claude HUD, claude-md-management |
| 중간 이상 기능 추가 | 일반 개발 + feature-dev 또는 Superpowers | 긴 작업 재개가 어렵다면 planning-with-files |
| 여러 세션에 걸친 장기 개발 | 일반 개발 + GSD Core 같은 주 워크플로 하나 | 필요한 서비스 MCP, 분야별 리뷰 |
| 웹 UI 제작 | 일반 개발 + frontend-design + 브라우저 도구 하나 | Figma, GitHub, 사용 중인 배포·백엔드 서비스 |
| Obsidian 지식관리 | 내장 기억 + claude-obsidian | 웹 수집에는 Firecrawl, 로컬 PDF 변환에는 Docling |
| Obsidian 편집 중심 | 내장 기억 + obsidian-skills | 필요한 외부 추출기·Obsidian CLI |
| 개발과 지식관리 병행 | 위의 6개 역할 구성 | 반복 업무 스킬, 웹 도구 등 실제 필요가 생긴 항목 |
| 자동 개발 이력 회수 | 일반 개발 + episodic-memory 또는 claude-mem | 사람이 읽을 위키가 필요하면 claude-obsidian |
| 여러 AI에서 같은 지식 사용 | 내장 기억 + Basic Memory | 공유 서버 운영이 필요하면 mcp-memory-service와 비교 |

개별 기능·환경·공식 링크는 [개발용 목록](01-development.md), [기억 목록](02-memory-knowledge.md), [외부 연동 목록](03-integrations.md)에 정리했습니다.

## 겹치는 도구를 고르는 기준

| 선택지 | 선택 기준 |
|---|---|
| 언어 LSP / Serena | 기본 진단·탐색이면 LSP부터. 더 풍부한 심벌 편집·프로젝트 탐색이 필요하면 Serena 검토 |
| Playwright / Chrome DevTools | 사용자 조작 흐름과 브라우저 탐색에는 Playwright. 콘솔·네트워크·성능 조사에는 Chrome DevTools |
| feature-dev / Superpowers / GSD / ECC | 기능 하나의 절차, 일관된 개발 방법론, 장기 프로젝트 단계 관리, 광범위한 도구 묶음 중 무엇이 중심인지 선택 |
| 내장 리뷰 / pr-review-toolkit | 기본 변경 검토는 내장 기능. 테스트·주석·오류 처리 등 전문 영역이 필요할 때 toolkit 추가 |
| episodic-memory / claude-mem | 과거 대화 원문 검색에는 전자. 도구 관찰·AI 요약·다음 세션 맥락 주입에는 후자 |
| claude-obsidian / obsidian-skills | 출처 있는 위키 운영에는 전자. Markdown·Canvas·Bases 작성 지원에는 후자 |
| claude-obsidian / Basic Memory | Obsidian 중심 위키 운영과 여러 MCP 클라이언트의 공통 지식 접근 중 주목적에 따라 선택 |
| Exa / Firecrawl | 자료 탐색·검색을 보완하려면 Exa. 웹·문서를 추출·변환하려면 Firecrawl |

서로 함께 쓸 수 없는 조합이라는 뜻은 아닙니다. 처음에는 같은 역할의 도구 하나로 시작하고, 부족한 기능이 확인될 때 추가하는 권장안입니다.

## 단계별 도입 순서

1. **기본 기능 확인:** `/memory`, 언어 LSP, 내장 리뷰를 사용하고 `CLAUDE.md`를 짧게 정리합니다.
2. **문서 조회 보완:** Context7를 연결합니다.
3. **대화 검색:** episodic-memory의 MCP 연결과 자동 sync 훅을 확인하고, 과거 대화가 실제 검색되는지 확인합니다.
4. **지식 위키:** 명시적으로 선택한 Obsidian 보관함을 claude-obsidian에 연결하고, 자료 하나의 저장·검색을 확인합니다.
5. **자동 연결:** 작업 시작·관련 질문·작업 완료에 어떤 검색·저장 처리를 실행할지 정합니다.
6. **개발 특화:** 반복 문제에 따라 hookify, skill-creator, 웹 도구, 개발 워크플로를 추가합니다.

이 가이드가 저장된 `$HOME/claude`는 문서 폴더입니다. 사용자가 선택한 보관함은 그 아래 `$HOME/claude/obsidian`이며, 경로 지정과 위키 초기화·실제 연결 완료는 구분합니다.

## 기록을 나누는 예시

로그인 오류를 해결했다고 가정하면 다음처럼 나눕니다.

- `CLAUDE.md`: 이 프로젝트의 테스트 실행 명령, 지켜야 할 개발 규칙
- Auto memory: 사용자가 반복해서 알려준 작업 선호·교정 사항
- episodic-memory: 시도한 해결책, 실패 과정, 대안에 대한 대화
- Obsidian 위키: 확인된 원인, 검증된 해결 방법, 적용 조건, 관련 코드·출처

위키의 오래된 내용과 현재 코드가 다르면 현재 상태를 다시 확인하고 노트를 갱신해야 합니다. 검색된 과거 대화의 추측을 확정된 프로젝트 사실로 취급하지 않도록 출처와 확인 상태를 함께 기록하는 방식이 적절합니다.

---

[목차로 돌아가기](00-index.md)
