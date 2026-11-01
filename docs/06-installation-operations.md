> 이 문서는 2026-11-01 조사·설치 기록입니다. 새 컴퓨터에서는 루트 README와 `scripts/bootstrap.py`를 우선 사용하세요. `$HOME`은 해당 컴퓨터의 홈 디렉터리이며, 당시 경로·검증 결과가 새 컴퓨터에 그대로 적용되는 것은 아닙니다.

# 설치와 운영 참고

기준일: 2026-11-01

아래 명령은 공식 안내에서 확인한 **실행 참고 예시**입니다. 이 문서를 작성하면서 어떤 설치 명령도 실행하지 않았습니다. 운영체제·Claude Code 버전·기존 설정에 따른 실제 동작은 확인하지 않았습니다.

## 명령을 입력하는 위치

- `claude ...`로 시작하는 명령은 터미널에서 실행합니다.
- `/memory`, `/mcp`, `/plugin ...` 같은 명령은 실행 중인 Claude Code 대화창에서 입력합니다.
- 동일한 MCP 서버를 중복 등록하지 않도록 확인합니다. 플러그인이 추가하는 hook·스킬은 별도 기능이므로, 설치 시 기존 MCP 등록과의 중복을 정리합니다.
- 설치 범위는 목적에 따라 선택합니다. `user`는 사용자 전체, `local`은 해당 저장소의 본인 설정, `project`는 공유할 프로젝트 설정에 해당합니다.

[Claude Code 플러그인 설치 문서](https://code.claude.com/docs/en/discover-plugins), [MCP 등록 문서](https://code.claude.com/docs/en/mcp)

## 1. 내장 기억과 리뷰 확인

Claude Code 안에서:

```text
/memory
/code-review
```

`/memory`에서 Auto memory 상태와 기억 파일을 확인합니다. `/code-review`는 최신 Claude Code의 내장 리뷰 기능이며, 여기에는 별도 code-review 플러그인 설치가 필요하지 않습니다. 리뷰는 일반 세션 사용량 또는 API 비용에 반영됩니다.

[기억 문서](https://code.claude.com/docs/en/memory), [내장 리뷰 문서](https://code.claude.com/docs/en/code-review-local)

## 2. 공식 마켓플레이스 플러그인

공식 마켓플레이스를 찾지 못하는 경우 터미널에서:

```bash
claude plugin marketplace add anthropics/claude-plugins-official
```

선택한 플러그인의 설치 형식:

```bash
claude plugin install claude-code-setup@claude-plugins-official --scope local
```

아래 이름은 필요에 맞게 하나씩 선택합니다.

| 설치 이름 | 용도 |
|---|---|
| `claude-code-setup` | 현재 저장소에 적합한 자동화 추천 |
| `claude-md-management` | 프로젝트 지침 점검·개선 |
| `typescript-lsp` | TypeScript·JavaScript 코드 진단·탐색 |
| `pyright-lsp` | Python 코드 진단·탐색 |
| `pr-review-toolkit` | 분야별 코드 리뷰 |
| `frontend-design` | 웹 UI 디자인·구현 지침 |
| `feature-dev` | 기능 탐색·설계·구현 절차 |
| `hookify` | 패턴 기반 경고·차단 훅 규칙 |
| `skill-creator` | 스킬 작성·평가·개선 |
| `plugin-dev` | 플러그인 개발·패키징 |
| `security-guidance` | 보안 검토; 추가 모델 사용량 확인 필요 |
| `superpowers` | 커뮤니티 개발 워크플로 |
| `ralph-loop` | 완료 조건 기반 반복 작업; 반복 상한을 정해 사용 |
| `figma` | Figma MCP와 스킬 |
| `exa` | 웹 검색·자료 조회 |

공식 마켓플레이스의 항목에도 외부 제작자가 포함됩니다. [현재 카탈로그](https://github.com/anthropics/claude-plugins-official/blob/main/.claude-plugin/marketplace.json)

LSP 플러그인은 실제 언어 서버가 별도로 필요합니다. TypeScript의 공식 예시는 다음과 같습니다.

```bash
npm install -g typescript-language-server typescript
claude plugin install typescript-lsp@claude-plugins-official --scope local
```

다른 언어는 해당 플러그인의 요구 서버를 확인합니다. [LSP 설치 안내](https://code.claude.com/docs/en/plugins/code-intelligence)

## 3. Context7

Claude Code 안에서 플러그인 방식으로 설치:

```text
/plugin marketplace add upstash/context7
/plugin install context7@context7-marketplace
```

공식 안내에 따라 재시작 후 `/mcp`에서 연결·로그인을 확인합니다. 같은 Context7를 수동 MCP로 추가한 상태라면 중복 여부를 먼저 확인합니다. [공식 설치 안내](https://context7.com/docs/clients/claude-code)

## 4. 과거 대화 검색: episodic-memory

Claude Code 안에서:

```text
/plugin marketplace add obra/superpowers-marketplace
/plugin install episodic-memory@superpowers-marketplace
```

Superpowers 코어를 설치했다고 episodic-memory까지 자동으로 설치되는 것은 아닙니다. 설치 후 MCP 연결과 훅 활성화를 확인합니다.

현재 소스의 자동 sync 이벤트는 세션 시작·재개·clear입니다. 검색은 remembering-conversations 스킬과 MCP 도구가 담당합니다. 기본 대화 요약에는 모델 사용량이 발생할 수 있습니다.

[프로젝트](https://github.com/obra/episodic-memory), [실제 훅](https://github.com/obra/episodic-memory/blob/main/hooks/hooks.json), [검색 스킬](https://github.com/obra/episodic-memory/blob/main/skills/remembering-conversations/SKILL.md)

선택형 요약을 끄려면 Claude Code를 시작하는 환경에 `EPISODIC_MEMORY_SKIP_SUMMARIES=1`을 설정할 수 있습니다. 이는 검색을 끄는 설정이 아닙니다. [환경변수 안내](https://github.com/obra/episodic-memory#api-configuration)

## 5. 지식 위키: claude-obsidian

터미널에서:

```bash
claude plugin marketplace add AgriciDaniel/claude-obsidian
claude plugin install claude-obsidian@agricidaniel-claude-obsidian
```

Python 3.11 이상 등 프로젝트의 요구 환경을 확인합니다. 그다음 **실제로 사용할 보관함 폴더**에서 Claude Code를 시작하고 다음 작업을 요청합니다.

```text
/claude-obsidian:wiki
/claude-obsidian:wiki-ingest
/claude-obsidian:wiki-query
/claude-obsidian:save
/claude-obsidian:wiki-lint
```

위 명령을 순서대로 무조건 모두 실행하는 것은 아닙니다. `wiki`는 초기 설정·기존 보관함 채택, `wiki-ingest`는 입력 자료 정리, `wiki-query`는 조회, `save`는 선택한 답변 저장, `wiki-lint`는 상태 점검에 사용합니다. 자연어로 해당 작업을 요청할 수도 있습니다.

이 가이드가 저장된 `$HOME/claude`를 실제 보관함으로 선택한 것은 아닙니다. 보관함 위치와 자동화 범위는 별도로 정해야 합니다.

[설치·사용 안내](https://github.com/AgriciDaniel/claude-obsidian), [기본 훅의 동작](https://github.com/AgriciDaniel/claude-obsidian/blob/main/hooks/README.md)

## 6. 필요에 따라 선택할 대안

### Obsidian 작성 지원만 필요한 경우

Claude Code 안에서:

```text
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills
```

claude-obsidian과 겹치는 스킬이 있으므로 필요한 기능을 비교해 선택합니다. [공식 저장소](https://github.com/kepano/obsidian-skills)

### 자동 작업 요약 중심으로 기억하고 싶은 경우

Claude Code 안에서:

```text
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

공식 안내에 따라 재시작하고 worker·훅 상태를 확인합니다. 단순 전역 npm 패키지 설치만으로 전체 연동이 구성되는 것은 아닙니다. [공식 설치 안내](https://github.com/thedotmack/claude-mem)

### 상태를 보고 싶은 경우: Claude HUD

Claude Code 안에서:

```text
/plugin marketplace add jarrodwatts/claude-hud
/plugin install claude-hud
/reload-plugins
/claude-hud:setup
```

설치 후 setup이 status line을 연결합니다. 선택형 도구·에이전트·진행 표시 등은 `/claude-hud:configure`로 조정합니다. [공식 안내](https://github.com/jarrodwatts/claude-hud)

### 브라우저 기능 검증: Playwright MCP

Node.js 환경에서 터미널에 등록하는 예시:

```bash
claude mcp add --transport stdio playwright -- npx -y @playwright/mcp@latest
```

위 예시는 Microsoft의 서버 실행 명령과 Claude Code의 공식 stdio 등록 문법을 조합했습니다. 공식 저장소는 코딩 에이전트에 CLI+Skills 방식도 검토하도록 안내합니다. [Microsoft 저장소](https://github.com/microsoft/playwright-mcp), [Claude Code MCP 문법](https://code.claude.com/docs/en/mcp)

### 브라우저 디버깅: Chrome DevTools MCP+Skills

Claude Code 안에서:

```text
/plugin marketplace add ChromeDevTools/chrome-devtools-mcp
/plugin install chrome-devtools-mcp@chrome-devtools-plugins
```

Node·Chrome 등 요구 환경과 기존 수동 MCP 중복 여부를 확인합니다. [공식 클라이언트 설정](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/client-configurations.md)

### 그 밖의 도구

아래 도구는 운영 환경·설치 경로 차이가 크므로 공식 안내를 기준으로 선택합니다.

| 도구 | 설치·운영 출처 |
|---|---|
| Basic Memory | [공식 README](https://github.com/basicmachines-co/basic-memory) — 조사 시점의 prerelease 의존성 안내 포함 |
| Serena | [설치](https://oraios.github.io/serena/02-usage/010_installation.html), [Claude Code 연결](https://oraios.github.io/serena/02-usage/030_clients.html) — 현재 공식 uv 경로와 `serena setup claude-code` 확인 |
| planning-with-files | [설치 안내](https://github.com/OthmanAdi/planning-with-files/blob/master/docs/installation.md) — 플러그인과 스킬 설치의 훅 제공 차이 확인 |
| GSD Core | [현재 저장소](https://github.com/open-gsd/gsd-core) — 이전 get-shit-done 저장소·설치 명령과 구분 |
| ECC | [현재 저장소](https://github.com/affaan-m/ECC) — 이전 everything-claude-code 이름에서 연결되는 현행 안내 |
| GitHub MCP | [Claude Code 설치](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-claude.md) |
| Linear MCP | [공식 안내](https://linear.app/docs/mcp) |
| Sentry MCP | [공식 안내](https://mcp.sentry.dev/) |
| Supabase MCP | [공식 안내](https://supabase.com/docs/guides/ai-tools/mcp) |
| Exa | [공식 MCP 안내](https://exa.ai/docs/get-started/exa-mcp) |
| Firecrawl | [Claude Code 시작 안내](https://docs.firecrawl.dev/quickstarts/claude-code) |
| Docling | [공식 저장소](https://github.com/docling-project/docling) |

## 연결 후 확인할 실제 동작

1. `/plugin`에서 선택한 플러그인이 활성화되어 있는지 확인합니다.
2. `/mcp`에서 필요한 서버가 연결되었는지 확인합니다.
3. 과거 대화 하나를 검색해 episodic-memory의 검색 결과와 원문을 확인합니다.
4. 보관함에서 자료 하나를 저장·검색하여 claude-obsidian의 경로와 결과를 확인합니다.
5. 세션을 재개해 자동 sync와 필요한 기억 읽기가 동작하는지 확인합니다.
6. 별도 통합 자동화를 만들었다면, 작업 완료 때 위키 기록이 한 번만 생성되고 다음 작업에서 회수되는지 확인합니다.

MCP 연결 성공과 기억 활용 성공은 별개이므로, 실제로 사용할 예시 하나를 저장하고 다시 찾는 것이 확인의 기준입니다.

자동화의 추가 설계는 [자동 저장·검색 설계](05-memory-automation.md)를 참고하세요.

---

[목차로 돌아가기](00-index.md)
